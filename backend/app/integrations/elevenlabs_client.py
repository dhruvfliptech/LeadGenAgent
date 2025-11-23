"""
ElevenLabs Text-to-Speech API Integration.

Official API Docs: https://elevenlabs.io/docs/api-reference/text-to-speech
Pricing:
  - Free: 10k characters/month
  - Starter: $5/mo, 30k characters (~20 videos)
  - Creator: $22/mo, 100k characters (~70 videos)
  - Pro: $99/mo, 500k characters (~350 videos)
Rate Limit: Varies by plan (Free: 3 req/min, Paid: 20-40 req/min)
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import json

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class VoiceModel(str, Enum):
    """Available ElevenLabs voice models."""
    MULTILINGUAL_V2 = "eleven_multilingual_v2"  # Best quality, 29 languages
    MULTILINGUAL_V1 = "eleven_multilingual_v1"  # Good quality, 8 languages
    MONOLINGUAL_V1 = "eleven_monolingual_v1"    # English only, fastest
    TURBO_V2 = "eleven_turbo_v2"                # Fastest, lower quality


class OutputFormat(str, Enum):
    """Available audio output formats."""
    MP3_44100_128 = "mp3_44100_128"    # Standard MP3 (44.1kHz, 128kbps)
    MP3_44100_192 = "mp3_44100_192"    # High quality MP3 (44.1kHz, 192kbps)
    PCM_16000 = "pcm_16000"             # PCM 16kHz
    PCM_22050 = "pcm_22050"             # PCM 22.05kHz
    PCM_24000 = "pcm_24000"             # PCM 24kHz
    PCM_44100 = "pcm_44100"             # PCM 44.1kHz (CD quality)


# Voice presets for different use cases
VOICE_PRESETS = {
    "professional_male": {
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel (actually female, but professional)
        "voice_name": "Rachel",
        "stability": 0.5,
        "similarity_boost": 0.75,
        "style": 0.0,
        "use_speaker_boost": True
    },
    "professional_female": {
        "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Bella
        "voice_name": "Bella",
        "stability": 0.6,
        "similarity_boost": 0.8,
        "style": 0.0,
        "use_speaker_boost": True
    },
    "casual_male": {
        "voice_id": "ErXwobaYiN019PkySvjV",  # Antoni
        "voice_name": "Antoni",
        "stability": 0.4,
        "similarity_boost": 0.7,
        "style": 0.2,
        "use_speaker_boost": True
    },
    "casual_female": {
        "voice_id": "MF3mGyEYCl7XYWbV9V6O",  # Elli
        "voice_name": "Elli",
        "stability": 0.45,
        "similarity_boost": 0.75,
        "style": 0.1,
        "use_speaker_boost": True
    },
    "energetic_male": {
        "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam
        "voice_name": "Adam",
        "stability": 0.3,
        "similarity_boost": 0.7,
        "style": 0.3,
        "use_speaker_boost": True
    },
    "calm_female": {
        "voice_id": "IKne3meq5aSn9XLyUdCD",  # Freya
        "voice_name": "Freya",
        "stability": 0.7,
        "similarity_boost": 0.8,
        "style": 0.0,
        "use_speaker_boost": True
    }
}


class ElevenLabsError(Exception):
    """Base exception for ElevenLabs errors."""
    pass


class QuotaExceededError(ElevenLabsError):
    """Raised when API quota is exceeded."""
    pass


class RateLimitError(ElevenLabsError):
    """Raised when rate limit is hit."""
    pass


class InvalidVoiceError(ElevenLabsError):
    """Raised when voice_id is invalid."""
    pass


class ElevenLabsClient:
    """
    ElevenLabs Text-to-Speech API client.

    Usage:
        client = ElevenLabsClient(api_key="your_key")

        # Generate audio with preset
        audio_data = await client.generate_audio(
            text="Hello, this is a test.",
            voice_preset="professional_female"
        )

        # Generate audio with custom voice
        audio_data = await client.generate_audio(
            text="Hello, this is a test.",
            voice_id="EXAVITQu4vr4xnSDxMaL",
            stability=0.6,
            similarity_boost=0.8
        )

        # Get available voices
        voices = await client.get_available_voices()

        # Check quota
        quota = await client.get_quota_info()
    """

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(
        self,
        api_key: str,
        timeout: int = 60,
        max_retries: int = 3,
        concurrent_limit: int = 3
    ):
        """
        Initialize ElevenLabs client.

        Args:
            api_key: ElevenLabs API key
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            concurrent_limit: Maximum concurrent requests
        """
        if not api_key:
            raise ValueError("ElevenLabs API key is required")

        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.concurrent_limit = concurrent_limit
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
        )

        # Rate limiting and concurrency control
        self._request_times: List[float] = []
        self._semaphore = asyncio.Semaphore(concurrent_limit)

        # Usage tracking
        self._total_characters = 0
        self._total_requests = 0

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _check_rate_limit(self):
        """Check and enforce rate limits."""
        now = datetime.now().timestamp()
        # Remove requests older than 1 minute
        self._request_times = [t for t in self._request_times if now - t < 60]

        # Conservative rate limit (3 req/min for free, but we'll be safe)
        rate_limit_per_minute = 3

        if len(self._request_times) >= rate_limit_per_minute:
            wait_time = 60 - (now - self._request_times[0])
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
                self._request_times = []

        self._request_times.append(now)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(RateLimitError)
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make an API request with rate limiting and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional request parameters

        Returns:
            Response object

        Raises:
            QuotaExceededError: When API quota is exceeded
            RateLimitError: When rate limit is hit
            ElevenLabsError: For other API errors
        """
        await self._check_rate_limit()

        url = f"{self.BASE_URL}{endpoint}"

        try:
            async with self._semaphore:
                response = await self._client.request(method, url, **kwargs)

            # Check for errors
            if response.status_code == 429:
                raise RateLimitError("Rate limit exceeded. Try again later.")

            if response.status_code == 401:
                raise ElevenLabsError("Invalid API key")

            if response.status_code == 422:
                error_data = response.json()
                raise InvalidVoiceError(f"Invalid voice or parameters: {error_data}")

            if response.status_code == 400:
                error_data = response.json()
                error_detail = error_data.get("detail", {})

                if isinstance(error_detail, dict):
                    status = error_detail.get("status")
                    message = error_detail.get("message", "")
                else:
                    message = str(error_detail)

                if "quota" in message.lower() or "limit" in message.lower():
                    raise QuotaExceededError(f"API quota exceeded: {message}")
                raise ElevenLabsError(f"Bad request: {message}")

            if response.status_code != 200:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = json.dumps(error_data, indent=2)
                except:
                    pass
                raise ElevenLabsError(f"API error ({response.status_code}): {error_msg}")

            return response

        except httpx.TimeoutException:
            raise ElevenLabsError(f"Request timeout after {self.timeout} seconds")
        except httpx.RequestError as e:
            raise ElevenLabsError(f"Request failed: {str(e)}")

    async def generate_audio(
        self,
        text: str,
        voice_id: Optional[str] = None,
        voice_preset: Optional[str] = None,
        model_id: str = VoiceModel.MULTILINGUAL_V2,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True,
        output_format: str = OutputFormat.MP3_44100_128
    ) -> bytes:
        """
        Generate audio from text using ElevenLabs TTS.

        Args:
            text: Text to convert to speech (max 5000 characters)
            voice_id: Voice ID (if not using preset)
            voice_preset: Voice preset name (professional_female, casual_male, etc.)
            model_id: Model to use for generation
            stability: Voice stability (0.0-1.0)
            similarity_boost: Voice similarity boost (0.0-1.0)
            style: Style exaggeration (0.0-1.0)
            use_speaker_boost: Enable speaker boost
            output_format: Audio output format

        Returns:
            Audio data as bytes (MP3 format)

        Raises:
            ValueError: If text is too long or parameters are invalid
            ElevenLabsError: For API errors
        """
        # Validate text length
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if len(text) > 5000:
            raise ValueError(f"Text too long ({len(text)} characters). Maximum is 5000.")

        # Get voice settings
        if voice_preset:
            if voice_preset not in VOICE_PRESETS:
                raise ValueError(
                    f"Invalid voice preset: {voice_preset}. "
                    f"Available: {list(VOICE_PRESETS.keys())}"
                )
            preset = VOICE_PRESETS[voice_preset]
            voice_id = preset["voice_id"]
            stability = preset["stability"]
            similarity_boost = preset["similarity_boost"]
            style = preset["style"]
            use_speaker_boost = preset["use_speaker_boost"]
            logger.info(f"Using voice preset: {voice_preset} ({preset['voice_name']})")
        elif not voice_id:
            # Default to professional_female
            preset = VOICE_PRESETS["professional_female"]
            voice_id = preset["voice_id"]
            logger.info("No voice specified, using default: professional_female")

        # Validate parameters
        if not 0 <= stability <= 1:
            raise ValueError("Stability must be between 0 and 1")
        if not 0 <= similarity_boost <= 1:
            raise ValueError("Similarity boost must be between 0 and 1")
        if not 0 <= style <= 1:
            raise ValueError("Style must be between 0 and 1")

        # Prepare request
        endpoint = f"/text-to-speech/{voice_id}"

        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": use_speaker_boost
            }
        }

        params = {
            "output_format": output_format
        }

        logger.info(
            f"Generating audio: {len(text)} characters, "
            f"voice={voice_id}, model={model_id}"
        )

        # Make request
        response = await self._make_request(
            "POST",
            endpoint,
            json=payload,
            params=params
        )

        # Track usage
        self._total_characters += len(text)
        self._total_requests += 1

        audio_data = response.content
        logger.info(
            f"Audio generated successfully: {len(audio_data)} bytes, "
            f"characters={len(text)}, total_chars={self._total_characters}"
        )

        return audio_data

    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices.

        Returns:
            List of voice dictionaries with keys:
                - voice_id: Unique voice identifier
                - name: Voice name
                - category: Voice category
                - labels: Voice characteristics
                - preview_url: URL to preview audio
                - samples: Sample audio files

        Example:
            voices = await client.get_available_voices()
            for voice in voices:
                print(f"{voice['name']}: {voice['voice_id']}")
        """
        logger.info("Fetching available voices")

        response = await self._make_request("GET", "/voices")
        data = response.json()

        voices = data.get("voices", [])
        logger.info(f"Found {len(voices)} available voices")

        return voices

    async def get_voice_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Find a voice by name.

        Args:
            name: Voice name to search for

        Returns:
            Voice dictionary or None if not found
        """
        voices = await self.get_available_voices()

        for voice in voices:
            if voice.get("name", "").lower() == name.lower():
                logger.info(f"Found voice '{name}': {voice['voice_id']}")
                return voice

        logger.warning(f"Voice '{name}' not found")
        return None

    async def get_quota_info(self) -> Dict[str, Any]:
        """
        Get API quota and usage information.

        Returns:
            Dictionary with:
                - character_count: Characters used this month
                - character_limit: Total characters available
                - can_extend_character_limit: Can upgrade
                - allowed_to_extend_character_limit: Allowed to upgrade
                - next_character_count_reset_unix: When quota resets (timestamp)

        Example:
            quota = await client.get_quota_info()
            used = quota['character_count']
            limit = quota['character_limit']
            print(f"Used: {used}/{limit} characters ({used/limit*100:.1f}%)")
        """
        logger.info("Fetching quota information")

        response = await self._make_request("GET", "/user/subscription")
        data = response.json()

        quota_info = {
            "character_count": data.get("character_count", 0),
            "character_limit": data.get("character_limit", 0),
            "can_extend_character_limit": data.get("can_extend_character_limit", False),
            "allowed_to_extend_character_limit": data.get("allowed_to_extend_character_limit", False),
            "next_character_count_reset_unix": data.get("next_character_count_reset_unix", 0),
            "tier": data.get("tier", "free"),
            "status": data.get("status", "active")
        }

        used = quota_info["character_count"]
        limit = quota_info["character_limit"]
        remaining = limit - used
        percentage = (used / limit * 100) if limit > 0 else 0

        logger.info(
            f"Quota: {used}/{limit} characters used ({percentage:.1f}%), "
            f"{remaining} remaining"
        )

        return quota_info

    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current usage statistics for this client session.

        Returns:
            Dictionary with usage stats
        """
        return {
            "total_characters": self._total_characters,
            "total_requests": self._total_requests,
            "avg_characters_per_request": (
                self._total_characters / self._total_requests
                if self._total_requests > 0 else 0
            )
        }

    def estimate_cost(self, text_length: int, plan: str = "pro") -> float:
        """
        Estimate cost for generating audio.

        Args:
            text_length: Number of characters
            plan: Pricing plan (free, starter, creator, pro)

        Returns:
            Estimated cost in USD
        """
        # Cost per character by plan
        costs_per_char = {
            "free": 0.0,  # Free tier
            "starter": 5.0 / 30000,   # $5/mo for 30k chars
            "creator": 22.0 / 100000,  # $22/mo for 100k chars
            "pro": 99.0 / 500000       # $99/mo for 500k chars
        }

        cost_per_char = costs_per_char.get(plan.lower(), costs_per_char["pro"])
        return text_length * cost_per_char

    def get_preset_info(self, preset_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a voice preset.

        Args:
            preset_name: Name of the preset

        Returns:
            Preset configuration or None if not found
        """
        return VOICE_PRESETS.get(preset_name)

    def list_presets(self) -> List[str]:
        """
        Get list of available voice presets.

        Returns:
            List of preset names
        """
        return list(VOICE_PRESETS.keys())
