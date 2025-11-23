"""
Unit tests for Voice Synthesizer service.

Tests voice synthesis functionality including:
- ElevenLabs client integration
- Script to audio conversion
- Audio merging
- Cost estimation
- Caching
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.video.voice_synthesizer import VoiceSynthesizer, VoiceoverResult
from app.integrations.elevenlabs_client import ElevenLabsClient, VOICE_PRESETS
from app.models.video_scripts import VideoScript
from app.models.voiceovers import Voiceover, VoiceoverCache


# Fixtures

@pytest.fixture
def mock_api_key():
    """Mock ElevenLabs API key."""
    return "test_api_key_12345"


@pytest.fixture
def mock_storage_path(tmp_path):
    """Create temporary storage path."""
    storage = tmp_path / "voiceovers"
    storage.mkdir()
    return str(storage)


@pytest.fixture
def synthesizer(mock_api_key, mock_storage_path):
    """Create VoiceSynthesizer instance with mocked dependencies."""
    return VoiceSynthesizer(
        api_key=mock_api_key,
        storage_path=mock_storage_path,
        enable_cache=True
    )


@pytest.fixture
def sample_script():
    """Create sample VideoScript for testing."""
    return VideoScript(
        id=1,
        demo_site_id=1,
        lead_id=1,
        script_style="professional",
        sections=[
            {
                "title": "Introduction",
                "content": "Welcome to our demo. This is a test script.",
                "duration_seconds": 5,
                "scene_type": "intro"
            },
            {
                "title": "Main Content",
                "content": "Here we showcase the main features of the product.",
                "duration_seconds": 10,
                "scene_type": "feature"
            }
        ],
        total_duration_seconds=15
    )


@pytest.fixture
def mock_audio_data():
    """Mock audio data."""
    return b"fake_mp3_audio_data_12345"


# Tests

class TestVoiceSynthesizer:
    """Test VoiceSynthesizer class."""

    def test_initialization(self, mock_api_key, mock_storage_path):
        """Test synthesizer initialization."""
        synthesizer = VoiceSynthesizer(
            api_key=mock_api_key,
            storage_path=mock_storage_path,
            enable_cache=True
        )

        assert synthesizer.api_key == mock_api_key
        assert str(synthesizer.storage_path) == mock_storage_path
        assert synthesizer.enable_cache is True

    def test_initialization_without_api_key(self):
        """Test initialization fails without API key."""
        with pytest.raises(ValueError, match="API key is required"):
            VoiceSynthesizer(api_key=None)

    def test_generate_cache_key(self, synthesizer):
        """Test cache key generation."""
        text = "Hello world"
        voice_preset = "professional_female"
        model_id = "eleven_multilingual_v2"

        key1 = synthesizer._generate_cache_key(text, voice_preset, model_id)
        key2 = synthesizer._generate_cache_key(text, voice_preset, model_id)

        # Same inputs should produce same key
        assert key1 == key2
        assert len(key1) == 64  # SHA256 hex string

        # Different inputs should produce different keys
        key3 = synthesizer._generate_cache_key("Different text", voice_preset, model_id)
        assert key1 != key3

    def test_list_presets(self, synthesizer):
        """Test listing voice presets."""
        presets = synthesizer.list_presets()

        assert len(presets) > 0
        assert "professional_female" in presets
        assert "professional_male" in presets
        assert "casual_male" in presets
        assert "casual_female" in presets

    def test_get_preset_info(self, synthesizer):
        """Test getting preset information."""
        info = synthesizer.get_preset_info("professional_female")

        assert info is not None
        assert "voice_id" in info
        assert "voice_name" in info
        assert "stability" in info
        assert "similarity_boost" in info

    def test_get_preset_info_invalid(self, synthesizer):
        """Test getting invalid preset returns None."""
        info = synthesizer.get_preset_info("invalid_preset")
        assert info is None

    def test_estimate_cost(self, synthesizer, sample_script):
        """Test cost estimation."""
        cost = synthesizer.estimate_cost(sample_script, plan="pro")

        assert cost > 0
        assert isinstance(cost, float)

        # Should be low cost for short script
        assert cost < 0.01  # Less than 1 cent

    @pytest.mark.asyncio
    async def test_synthesize_text(self, synthesizer, mock_audio_data):
        """Test synthesizing plain text."""
        text = "This is a test."

        with patch.object(synthesizer, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_audio = AsyncMock(return_value=mock_audio_data)
            mock_client.estimate_cost = Mock(return_value=0.001)
            mock_get_client.return_value = mock_client

            with patch.object(synthesizer, 'get_audio_duration', return_value=2.5):
                result = await synthesizer.synthesize_text(
                    text=text,
                    voice_preset="professional_female"
                )

        assert isinstance(result, VoiceoverResult)
        assert result.audio_data == mock_audio_data
        assert result.format == "mp3"
        assert result.duration_seconds == 2.5
        assert result.sample_rate == 44100
        assert result.characters_processed == len(text)

    @pytest.mark.asyncio
    async def test_synthesize_script(self, synthesizer, sample_script, mock_audio_data):
        """Test synthesizing complete video script."""
        with patch.object(synthesizer, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_audio = AsyncMock(return_value=mock_audio_data)
            mock_client.estimate_cost = Mock(return_value=0.001)
            mock_client.api_key = "test_key"
            mock_get_client.return_value = mock_client

            with patch.object(synthesizer, 'get_audio_duration', return_value=5.0):
                with patch.object(synthesizer, 'merge_audio_files', return_value=mock_audio_data):
                    result = await synthesizer.synthesize_script(
                        script=sample_script,
                        voice_preset="professional_female",
                        merge_sections=True
                    )

        assert isinstance(result, VoiceoverResult)
        assert result.audio_data == mock_audio_data
        assert result.characters_processed > 0
        assert result.cost_usd > 0
        assert "sections" in result.metadata

    @pytest.mark.asyncio
    async def test_synthesize_script_without_merge(self, synthesizer, sample_script, mock_audio_data):
        """Test synthesizing script without merging sections."""
        with patch.object(synthesizer, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_audio = AsyncMock(return_value=mock_audio_data)
            mock_client.estimate_cost = Mock(return_value=0.001)
            mock_client.api_key = "test_key"
            mock_get_client.return_value = mock_client

            with patch.object(synthesizer, 'get_audio_duration', return_value=5.0):
                result = await synthesizer.synthesize_script(
                    script=sample_script,
                    voice_preset="professional_female",
                    merge_sections=False
                )

        assert result.sections_audio is not None
        assert len(result.sections_audio) > 0

    @pytest.mark.asyncio
    async def test_synthesize_script_invalid_preset(self, synthesizer, sample_script):
        """Test synthesizing with invalid preset raises error."""
        with pytest.raises(ValueError, match="Invalid voice preset"):
            await synthesizer.synthesize_script(
                script=sample_script,
                voice_preset="invalid_preset"
            )

    @pytest.mark.asyncio
    async def test_save_audio_file(self, synthesizer, mock_audio_data):
        """Test saving audio file to storage."""
        demo_site_id = 123
        voiceover_id = 456

        file_path = await synthesizer.save_audio_file(
            audio_data=mock_audio_data,
            demo_site_id=demo_site_id,
            voiceover_id=voiceover_id,
            format="mp3"
        )

        assert file_path is not None
        assert "123" in file_path  # demo_site_id
        assert "456" in file_path  # voiceover_id
        assert file_path.endswith(".mp3")

        # Verify file exists
        from pathlib import Path
        assert Path(file_path).exists()

        # Verify file content
        assert Path(file_path).read_bytes() == mock_audio_data

    def test_get_audio_duration_valid(self, synthesizer):
        """Test getting audio duration from valid MP3."""
        # This would need a real MP3 file to test properly
        # For now, test that method exists and handles errors
        fake_audio = b"not_real_audio"

        duration = synthesizer.get_audio_duration(fake_audio)

        # Should return 0.0 for invalid audio
        assert duration == 0.0

    @pytest.mark.asyncio
    async def test_merge_audio_files(self, synthesizer):
        """Test merging multiple audio files."""
        # This would need real audio files to test properly
        # For now, test basic validation
        audio_files = [b"audio1", b"audio2", b"audio3"]
        pauses_ms = [500, 500]

        with pytest.raises(Exception):
            # Should fail with invalid audio data
            await synthesizer.merge_audio_files(audio_files, pauses_ms)

    @pytest.mark.asyncio
    async def test_merge_audio_files_validation(self, synthesizer):
        """Test merge validation."""
        audio_files = [b"audio1", b"audio2"]
        pauses_ms = [500, 500, 500]  # Wrong length

        with pytest.raises(ValueError, match="pauses_ms length"):
            await synthesizer.merge_audio_files(audio_files, pauses_ms)


class TestElevenLabsClient:
    """Test ElevenLabsClient class."""

    def test_initialization(self, mock_api_key):
        """Test client initialization."""
        client = ElevenLabsClient(
            api_key=mock_api_key,
            timeout=30,
            max_retries=3
        )

        assert client.api_key == mock_api_key
        assert client.timeout == 30
        assert client.max_retries == 3

    def test_initialization_without_api_key(self):
        """Test initialization fails without API key."""
        with pytest.raises(ValueError, match="API key is required"):
            ElevenLabsClient(api_key=None)

    def test_estimate_cost(self, mock_api_key):
        """Test cost estimation."""
        client = ElevenLabsClient(api_key=mock_api_key)

        # Test different plans
        cost_free = client.estimate_cost(1000, "free")
        cost_pro = client.estimate_cost(1000, "pro")

        assert cost_free == 0.0  # Free tier
        assert cost_pro > 0.0
        assert cost_pro < 0.01  # Should be very cheap for 1000 chars

    def test_get_preset_info(self, mock_api_key):
        """Test getting preset info."""
        client = ElevenLabsClient(api_key=mock_api_key)

        info = client.get_preset_info("professional_female")

        assert info is not None
        assert info["voice_id"] == VOICE_PRESETS["professional_female"]["voice_id"]

    def test_list_presets(self, mock_api_key):
        """Test listing presets."""
        client = ElevenLabsClient(api_key=mock_api_key)

        presets = client.list_presets()

        assert len(presets) == len(VOICE_PRESETS)
        assert "professional_female" in presets


# Integration tests (require real API key)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api_call():
    """
    Integration test with real ElevenLabs API.

    Requires ELEVENLABS_API_KEY environment variable.
    Skip if not available.
    """
    import os

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        pytest.skip("ELEVENLABS_API_KEY not set")

    client = ElevenLabsClient(api_key=api_key)

    # Test with very short text to minimize cost
    text = "Test."

    try:
        audio_data = await client.generate_audio(
            text=text,
            voice_preset="professional_female"
        )

        assert audio_data is not None
        assert len(audio_data) > 0
        assert isinstance(audio_data, bytes)

    except Exception as e:
        pytest.fail(f"Real API call failed: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
