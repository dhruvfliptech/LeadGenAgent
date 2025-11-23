"""
Voice Synthesizer Service for Video Script Audio Generation.

Converts video scripts to high-quality voiceover audio using ElevenLabs.
"""

import asyncio
import logging
import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
from decimal import Decimal

from pydub import AudioSegment
from pydub.silence import detect_silence
import io

from app.integrations.elevenlabs_client import ElevenLabsClient, VOICE_PRESETS
from app.models.voiceovers import Voiceover, VoiceoverUsage, VoiceoverCache, VoiceoverStatus
from app.models.video_scripts import VideoScript
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class VoiceoverResult:
    """Result of voiceover generation."""
    audio_data: bytes
    format: str
    duration_seconds: float
    sample_rate: int
    voice_preset: str
    sections_audio: Optional[List[bytes]] = None
    cost_usd: float = 0.0
    characters_processed: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class VoiceSynthesizer:
    """
    Voice Synthesizer Service.

    Converts video scripts to audio using ElevenLabs TTS API with:
    - Section-based generation
    - Audio merging with pauses
    - Caching for repeated content
    - Cost tracking
    - Quality optimization
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        storage_path: Optional[str] = None,
        enable_cache: bool = True
    ):
        """
        Initialize voice synthesizer.

        Args:
            api_key: ElevenLabs API key (defaults to settings)
            storage_path: Path for storing audio files (defaults to settings)
            enable_cache: Enable audio caching
        """
        self.api_key = api_key or settings.ELEVENLABS_API_KEY
        if not self.api_key:
            raise ValueError("ElevenLabs API key is required")

        self.storage_path = Path(storage_path or settings.VOICEOVER_STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.enable_cache = enable_cache
        self.client = None

    async def _get_client(self) -> ElevenLabsClient:
        """Get or create ElevenLabs client."""
        if not self.client:
            self.client = ElevenLabsClient(
                api_key=self.api_key,
                timeout=60,
                max_retries=3,
                concurrent_limit=3
            )
        return self.client

    async def close(self):
        """Close the client."""
        if self.client:
            await self.client.close()
            self.client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _generate_cache_key(
        self,
        text: str,
        voice_preset: str,
        model_id: str
    ) -> str:
        """
        Generate cache key for audio content.

        Args:
            text: Text content
            voice_preset: Voice preset name
            model_id: Model ID

        Returns:
            SHA256 hash as hex string
        """
        content = f"{text}|{voice_preset}|{model_id}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def synthesize_script(
        self,
        script: VideoScript,
        voice_preset: str = "professional_female",
        output_format: str = "mp3",
        merge_sections: bool = True,
        add_section_pauses: bool = True,
        pause_duration_ms: int = 500,
        db_session = None
    ) -> VoiceoverResult:
        """
        Synthesize complete video script to audio.

        Args:
            script: VideoScript instance
            voice_preset: Voice preset name
            output_format: Audio format (mp3, wav, ogg)
            merge_sections: Merge all sections into one file
            add_section_pauses: Add pauses between sections
            pause_duration_ms: Pause duration in milliseconds
            db_session: Database session for caching

        Returns:
            VoiceoverResult with audio data and metadata
        """
        logger.info(
            f"Starting voiceover synthesis for script {script.id}, "
            f"voice={voice_preset}, merge={merge_sections}"
        )

        # Extract sections from script
        sections = script.sections or []
        if not sections:
            raise ValueError("Script has no sections to synthesize")

        # Validate voice preset
        if voice_preset not in VOICE_PRESETS:
            raise ValueError(
                f"Invalid voice preset: {voice_preset}. "
                f"Available: {list(VOICE_PRESETS.keys())}"
            )

        client = await self._get_client()
        sections_audio = []
        total_characters = 0
        total_cost = 0.0
        section_metadata = []

        # Generate audio for each section
        for idx, section in enumerate(sections):
            section_text = section.get("content", "")
            if not section_text or not section_text.strip():
                logger.warning(f"Section {idx} has no content, skipping")
                continue

            logger.info(f"Synthesizing section {idx + 1}/{len(sections)}: {len(section_text)} chars")

            try:
                # Check cache first
                audio_data = None
                if self.enable_cache and db_session:
                    audio_data = await self._get_cached_audio(
                        section_text,
                        voice_preset,
                        client.api_key,
                        db_session
                    )

                # Generate if not cached
                if not audio_data:
                    audio_data = await client.generate_audio(
                        text=section_text,
                        voice_preset=voice_preset,
                        output_format=f"mp3_44100_128"
                    )

                    # Cache the audio
                    if self.enable_cache and db_session:
                        await self._cache_audio(
                            section_text,
                            voice_preset,
                            client.api_key,
                            audio_data,
                            db_session
                        )

                sections_audio.append(audio_data)
                total_characters += len(section_text)

                # Calculate cost
                section_cost = client.estimate_cost(len(section_text), "pro")
                total_cost += section_cost

                # Store section metadata
                section_metadata.append({
                    "section_index": idx,
                    "title": section.get("title", f"Section {idx + 1}"),
                    "characters": len(section_text),
                    "cost_usd": section_cost,
                    "duration_estimate": section.get("duration_seconds")
                })

                logger.info(
                    f"Section {idx + 1} complete: {len(audio_data)} bytes, "
                    f"cost=${section_cost:.4f}"
                )

            except Exception as e:
                logger.error(f"Failed to synthesize section {idx}: {str(e)}")
                raise

        # Merge sections if requested
        if merge_sections and len(sections_audio) > 1:
            logger.info(f"Merging {len(sections_audio)} sections with {pause_duration_ms}ms pauses")
            merged_audio = await self.merge_audio_files(
                sections_audio,
                [pause_duration_ms] * (len(sections_audio) - 1) if add_section_pauses else [0] * (len(sections_audio) - 1)
            )
            final_audio = merged_audio
        else:
            final_audio = sections_audio[0] if sections_audio else b""

        # Calculate duration
        duration = self.get_audio_duration(final_audio)

        logger.info(
            f"Voiceover synthesis complete: {duration:.2f}s, "
            f"{total_characters} chars, cost=${total_cost:.4f}"
        )

        return VoiceoverResult(
            audio_data=final_audio,
            format=output_format,
            duration_seconds=duration,
            sample_rate=44100,
            voice_preset=voice_preset,
            sections_audio=sections_audio if not merge_sections else None,
            cost_usd=total_cost,
            characters_processed=total_characters,
            metadata={
                "sections": section_metadata,
                "merge_sections": merge_sections,
                "add_section_pauses": add_section_pauses,
                "pause_duration_ms": pause_duration_ms,
                "script_id": script.id,
                "script_style": script.script_style
            }
        )

    async def synthesize_text(
        self,
        text: str,
        voice_preset: str = "professional_female",
        output_format: str = "mp3"
    ) -> VoiceoverResult:
        """
        Synthesize plain text to audio.

        Args:
            text: Text to synthesize
            voice_preset: Voice preset name
            output_format: Audio format

        Returns:
            VoiceoverResult with audio data
        """
        logger.info(f"Synthesizing text: {len(text)} characters")

        client = await self._get_client()

        audio_data = await client.generate_audio(
            text=text,
            voice_preset=voice_preset,
            output_format=f"mp3_44100_128"
        )

        duration = self.get_audio_duration(audio_data)
        cost = client.estimate_cost(len(text), "pro")

        logger.info(f"Text synthesis complete: {duration:.2f}s, cost=${cost:.4f}")

        return VoiceoverResult(
            audio_data=audio_data,
            format=output_format,
            duration_seconds=duration,
            sample_rate=44100,
            voice_preset=voice_preset,
            cost_usd=cost,
            characters_processed=len(text)
        )

    async def merge_audio_files(
        self,
        audio_files: List[bytes],
        pauses_ms: List[int]
    ) -> bytes:
        """
        Merge multiple audio files with pauses between them.

        Args:
            audio_files: List of audio data in bytes
            pauses_ms: List of pause durations in milliseconds (length = len(audio_files) - 1)

        Returns:
            Merged audio data as bytes (MP3 format)
        """
        if not audio_files:
            return b""

        if len(audio_files) == 1:
            return audio_files[0]

        if len(pauses_ms) != len(audio_files) - 1:
            raise ValueError(
                f"pauses_ms length ({len(pauses_ms)}) must be "
                f"len(audio_files) - 1 ({len(audio_files) - 1})"
            )

        logger.info(f"Merging {len(audio_files)} audio files")

        # Load first audio segment
        combined = AudioSegment.from_file(io.BytesIO(audio_files[0]), format="mp3")

        # Append remaining segments with pauses
        for idx, audio_data in enumerate(audio_files[1:]):
            # Add pause
            if pauses_ms[idx] > 0:
                silence = AudioSegment.silent(duration=pauses_ms[idx])
                combined += silence

            # Add next segment
            segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
            combined += segment

        # Export to bytes
        output = io.BytesIO()
        combined.export(output, format="mp3", bitrate="128k")
        merged_data = output.getvalue()

        logger.info(f"Merged audio: {len(merged_data)} bytes")
        return merged_data

    def get_audio_duration(self, audio_data: bytes) -> float:
        """
        Get duration of audio file in seconds.

        Args:
            audio_data: Audio data in bytes (MP3 format)

        Returns:
            Duration in seconds
        """
        try:
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
            return len(audio) / 1000.0  # Convert ms to seconds
        except Exception as e:
            logger.error(f"Failed to get audio duration: {str(e)}")
            return 0.0

    def estimate_cost(self, script: VideoScript, plan: str = "pro") -> float:
        """
        Estimate cost for generating voiceover for a script.

        Args:
            script: VideoScript instance
            plan: Pricing plan (free, starter, creator, pro)

        Returns:
            Estimated cost in USD
        """
        sections = script.sections or []
        total_characters = sum(
            len(section.get("content", ""))
            for section in sections
        )

        client = ElevenLabsClient(api_key="dummy")  # Just for cost estimation
        return client.estimate_cost(total_characters, plan)

    async def save_audio_file(
        self,
        audio_data: bytes,
        demo_site_id: int,
        voiceover_id: int,
        format: str = "mp3"
    ) -> str:
        """
        Save audio file to storage.

        Args:
            audio_data: Audio data in bytes
            demo_site_id: Demo site ID
            voiceover_id: Voiceover ID
            format: Audio format

        Returns:
            File path (absolute path)
        """
        # Create demo site directory
        demo_dir = self.storage_path / str(demo_site_id)
        demo_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"voiceover_{voiceover_id}_{timestamp}.{format}"
        file_path = demo_dir / filename

        # Write file
        file_path.write_bytes(audio_data)

        logger.info(f"Saved audio file: {file_path} ({len(audio_data)} bytes)")
        return str(file_path.absolute())

    async def _get_cached_audio(
        self,
        text: str,
        voice_preset: str,
        model_id: str,
        db_session
    ) -> Optional[bytes]:
        """
        Get cached audio if available.

        Args:
            text: Text content
            voice_preset: Voice preset
            model_id: Model ID
            db_session: Database session

        Returns:
            Audio data or None if not cached
        """
        cache_key = self._generate_cache_key(text, voice_preset, model_id)

        try:
            cache_entry = db_session.query(VoiceoverCache).filter(
                VoiceoverCache.cache_key == cache_key,
                VoiceoverCache.expires_at > datetime.utcnow()
            ).first()

            if cache_entry:
                # Update usage stats
                cache_entry.hit_count += 1
                cache_entry.last_accessed_at = datetime.utcnow()
                db_session.commit()

                # Read audio file
                if cache_entry.audio_file_path and os.path.exists(cache_entry.audio_file_path):
                    audio_data = Path(cache_entry.audio_file_path).read_bytes()
                    logger.info(f"Cache hit: {cache_key[:16]}... (hits={cache_entry.hit_count})")
                    return audio_data

        except Exception as e:
            logger.error(f"Cache lookup failed: {str(e)}")

        return None

    async def _cache_audio(
        self,
        text: str,
        voice_preset: str,
        model_id: str,
        audio_data: bytes,
        db_session
    ):
        """
        Cache audio for future use.

        Args:
            text: Text content
            voice_preset: Voice preset
            model_id: Model ID
            audio_data: Audio data to cache
            db_session: Database session
        """
        try:
            cache_key = self._generate_cache_key(text, voice_preset, model_id)

            # Save audio file
            cache_dir = self.storage_path / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = cache_dir / f"{cache_key}.mp3"
            cache_file.write_bytes(audio_data)

            # Get audio duration
            duration = self.get_audio_duration(audio_data)

            # Create cache entry
            cache_entry = VoiceoverCache(
                cache_key=cache_key,
                text_content=text,
                voice_preset=voice_preset,
                model_id=model_id,
                audio_file_path=str(cache_file.absolute()),
                duration_seconds=duration,
                format="mp3",
                sample_rate=44100,
                file_size_bytes=len(audio_data),
                hit_count=0,
                expires_at=datetime.utcnow() + timedelta(days=30)
            )

            db_session.add(cache_entry)
            db_session.commit()

            logger.info(f"Cached audio: {cache_key[:16]}...")

        except Exception as e:
            logger.error(f"Failed to cache audio: {str(e)}")
            db_session.rollback()

    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices from ElevenLabs.

        Returns:
            List of voice dictionaries
        """
        client = await self._get_client()
        return await client.get_available_voices()

    async def get_quota_info(self) -> Dict[str, Any]:
        """
        Get ElevenLabs API quota information.

        Returns:
            Quota information dictionary
        """
        client = await self._get_client()
        return await client.get_quota_info()

    def list_presets(self) -> List[str]:
        """
        Get list of available voice presets.

        Returns:
            List of preset names
        """
        return list(VOICE_PRESETS.keys())

    def get_preset_info(self, preset_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a voice preset.

        Args:
            preset_name: Name of the preset

        Returns:
            Preset configuration or None
        """
        return VOICE_PRESETS.get(preset_name)
