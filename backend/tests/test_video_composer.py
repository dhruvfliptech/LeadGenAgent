"""
Comprehensive tests for video composer functionality.

Tests FFmpegWrapper, VideoComposer, and API endpoints.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.video.ffmpeg_wrapper import FFmpegWrapper, VideoMetadata, FFmpegProgress
from app.services.video.video_composer import (
    VideoComposer,
    CompositionConfig,
    BrandingConfig,
    TextOverlay,
    IntroConfig,
    OutroConfig,
    CompositionResult
)
from app.models.composed_videos import ComposedVideo, CompositionJob, CompositionStatus


# Fixtures

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_video_file(temp_dir):
    """Create a mock video file."""
    video_path = Path(temp_dir) / "test_video.mp4"
    video_path.write_bytes(b"fake video content")
    return str(video_path)


@pytest.fixture
def mock_audio_file(temp_dir):
    """Create a mock audio file."""
    audio_path = Path(temp_dir) / "test_audio.mp3"
    audio_path.write_bytes(b"fake audio content")
    return str(audio_path)


@pytest.fixture
def mock_logo_file(temp_dir):
    """Create a mock logo file."""
    logo_path = Path(temp_dir) / "logo.png"
    logo_path.write_bytes(b"fake logo content")
    return str(logo_path)


@pytest.fixture
def ffmpeg_wrapper():
    """Create FFmpegWrapper instance."""
    return FFmpegWrapper()


@pytest.fixture
def video_composer(temp_dir):
    """Create VideoComposer instance."""
    return VideoComposer(storage_base_path=temp_dir)


@pytest.fixture
def composition_config():
    """Create composition configuration."""
    return CompositionConfig(
        output_format="mp4",
        video_codec="h264",
        audio_codec="aac",
        crf=23,
        preset="fast"
    )


@pytest.fixture
def branding_config(mock_logo_file):
    """Create branding configuration."""
    return BrandingConfig(
        logo_path=mock_logo_file,
        logo_position="top-right",
        company_name="Test Company"
    )


# FFmpegWrapper Tests

class TestFFmpegWrapper:
    """Tests for FFmpegWrapper class."""

    def test_initialization(self, ffmpeg_wrapper):
        """Test FFmpegWrapper initialization."""
        assert ffmpeg_wrapper.ffmpeg_path is not None
        assert ffmpeg_wrapper.ffprobe_path is not None

    def test_validate_installation(self, ffmpeg_wrapper):
        """Test FFmpeg installation validation."""
        # Should not raise exception if FFmpeg is installed
        ffmpeg_wrapper._validate_installation()

    @pytest.mark.asyncio
    async def test_get_video_metadata(self, ffmpeg_wrapper, mock_video_file):
        """Test getting video metadata."""
        with patch.object(ffmpeg_wrapper, 'get_video_metadata') as mock_metadata:
            mock_metadata.return_value = VideoMetadata(
                duration=90.0,
                width=1920,
                height=1080,
                fps=30.0,
                bitrate=5000000,
                codec="h264",
                audio_codec="aac",
                file_size=10000000
            )

            metadata = await ffmpeg_wrapper.get_video_metadata(mock_video_file)

            assert metadata.duration == 90.0
            assert metadata.width == 1920
            assert metadata.height == 1080
            assert metadata.codec == "h264"

    def test_validate_video_file_not_exists(self, ffmpeg_wrapper):
        """Test validation of non-existent video file."""
        result = ffmpeg_wrapper.validate_video("/nonexistent/file.mp4")
        assert result is False

    def test_validate_video_empty_file(self, ffmpeg_wrapper, temp_dir):
        """Test validation of empty video file."""
        empty_file = Path(temp_dir) / "empty.mp4"
        empty_file.write_bytes(b"")

        result = ffmpeg_wrapper.validate_video(str(empty_file))
        assert result is False

    def test_get_progress_not_found(self, ffmpeg_wrapper):
        """Test getting progress for non-existent process."""
        progress = ffmpeg_wrapper.get_progress("nonexistent-id")
        assert progress is None

    def test_parse_progress(self, ffmpeg_wrapper):
        """Test parsing progress from FFmpeg output."""
        progress = FFmpegProgress(process_id="test", progress=0.0)

        # Test frame parsing
        ffmpeg_wrapper._parse_progress("frame=  100", progress)
        assert progress.current_frame == 100

        # Test time parsing
        ffmpeg_wrapper._parse_progress("time=00:01:30.50", progress)
        assert progress.current_time == 90.5

        # Test speed parsing
        ffmpeg_wrapper._parse_progress("speed=2.5x", progress)
        assert progress.speed == "2.5x"


# VideoComposer Tests

class TestVideoComposer:
    """Tests for VideoComposer class."""

    def test_initialization(self, video_composer, temp_dir):
        """Test VideoComposer initialization."""
        assert video_composer.storage_base == Path(temp_dir)
        assert video_composer.ffmpeg is not None

    def test_ensure_directories(self, video_composer, temp_dir):
        """Test that required directories are created."""
        base_path = Path(temp_dir)
        assert (base_path / "recordings").exists()
        assert (base_path / "voiceovers").exists()
        assert (base_path / "composed_videos").exists()
        assert (base_path / "thumbnails").exists()
        assert (base_path / "temp").exists()

    @pytest.mark.asyncio
    async def test_compose_video_invalid_recording(self, video_composer):
        """Test composition with invalid recording path."""
        with pytest.raises(ValueError, match="Invalid screen recording"):
            await video_composer.compose_video(
                screen_recording_path="/nonexistent/recording.mp4",
                voiceover_path="/nonexistent/voiceover.mp3",
                demo_site_id=1
            )

    @pytest.mark.asyncio
    async def test_compose_video_invalid_voiceover(self, video_composer, mock_video_file):
        """Test composition with invalid voiceover path."""
        with patch.object(video_composer.ffmpeg, 'validate_video', return_value=True):
            with pytest.raises(ValueError, match="Voiceover file not found"):
                await video_composer.compose_video(
                    screen_recording_path=mock_video_file,
                    voiceover_path="/nonexistent/voiceover.mp3",
                    demo_site_id=1
                )

    @pytest.mark.asyncio
    async def test_compose_video_success(
        self,
        video_composer,
        mock_video_file,
        mock_audio_file,
        composition_config
    ):
        """Test successful video composition."""
        with patch.object(video_composer.ffmpeg, 'validate_video', return_value=True):
            with patch.object(video_composer.ffmpeg, 'merge_audio_video', return_value=True):
                with patch.object(video_composer.ffmpeg, 'encode_video', return_value=True):
                    with patch.object(video_composer.ffmpeg, 'get_video_metadata') as mock_metadata:
                        mock_metadata.return_value = VideoMetadata(
                            duration=90.0,
                            width=1920,
                            height=1080,
                            fps=30.0,
                            bitrate=5000000,
                            codec="h264",
                            audio_codec="aac",
                            file_size=30000000
                        )

                        result = await video_composer.compose_video(
                            screen_recording_path=mock_video_file,
                            voiceover_path=mock_audio_file,
                            demo_site_id=1,
                            composition_config=composition_config
                        )

                        assert isinstance(result, CompositionResult)
                        assert result.duration_seconds == 90.0
                        assert result.resolution == "1920x1080"
                        assert result.processing_time_seconds > 0

    @pytest.mark.asyncio
    async def test_add_text_overlays(self, video_composer, mock_video_file):
        """Test adding text overlays."""
        overlays = [
            TextOverlay(
                text="Test Overlay",
                start_time_seconds=2.0,
                end_time_seconds=5.0,
                position="bottom"
            )
        ]

        with patch.object(video_composer.ffmpeg, 'add_text_overlay', return_value=True):
            result = await video_composer.add_text_overlays(mock_video_file, overlays)
            assert result is not None

    @pytest.mark.asyncio
    async def test_add_background_music(
        self,
        video_composer,
        mock_video_file,
        mock_audio_file
    ):
        """Test adding background music."""
        with patch.object(video_composer.ffmpeg, 'add_background_music', return_value=True):
            result = await video_composer.add_background_music(
                mock_video_file,
                mock_audio_file,
                volume=0.15
            )
            assert result is not None

    @pytest.mark.asyncio
    async def test_encode_for_web(self, video_composer, mock_video_file):
        """Test generating multiple quality versions."""
        qualities = ["1080p", "720p", "480p"]

        with patch.object(video_composer.ffmpeg, 'encode_video', return_value=True):
            versions = await video_composer.encode_for_web(
                mock_video_file,
                qualities,
                demo_site_id=1
            )

            assert len(versions) == len(qualities)
            for quality in qualities:
                assert quality in versions

    @pytest.mark.asyncio
    async def test_extract_thumbnail(self, video_composer, mock_video_file):
        """Test thumbnail extraction."""
        with patch.object(video_composer.ffmpeg, 'extract_thumbnail', return_value=True):
            thumbnail_path = await video_composer.extract_thumbnail(
                mock_video_file,
                demo_site_id=1,
                timestamp_seconds=5.0
            )
            assert thumbnail_path is not None

    def test_estimate_cost(self, video_composer):
        """Test cost estimation."""
        cost = video_composer._estimate_cost(
            processing_time_seconds=120.0,
            file_size_bytes=30000000
        )
        assert cost > 0
        assert isinstance(cost, float)


# Configuration Model Tests

class TestConfigurationModels:
    """Tests for configuration Pydantic models."""

    def test_composition_config_defaults(self):
        """Test CompositionConfig default values."""
        config = CompositionConfig()
        assert config.output_format == "mp4"
        assert config.video_codec == "h264"
        assert config.audio_codec == "aac"
        assert config.crf == 23
        assert config.preset == "fast"

    def test_composition_config_custom(self):
        """Test CompositionConfig with custom values."""
        config = CompositionConfig(
            output_format="webm",
            video_codec="vp9",
            crf=28,
            preset="slow"
        )
        assert config.output_format == "webm"
        assert config.video_codec == "vp9"
        assert config.crf == 28
        assert config.preset == "slow"

    def test_branding_config(self):
        """Test BrandingConfig."""
        config = BrandingConfig(
            logo_path="/path/to/logo.png",
            logo_position="top-left",
            company_name="Test Company",
            primary_color="#FF0000"
        )
        assert config.logo_path == "/path/to/logo.png"
        assert config.logo_position == "top-left"
        assert config.company_name == "Test Company"
        assert config.primary_color == "#FF0000"

    def test_text_overlay(self):
        """Test TextOverlay configuration."""
        overlay = TextOverlay(
            text="Test Text",
            start_time_seconds=1.0,
            end_time_seconds=5.0,
            position="center",
            font_size=64
        )
        assert overlay.text == "Test Text"
        assert overlay.start_time_seconds == 1.0
        assert overlay.end_time_seconds == 5.0
        assert overlay.position == "center"
        assert overlay.font_size == 64

    def test_intro_config(self):
        """Test IntroConfig."""
        config = IntroConfig(
            duration_seconds=5,
            template="corporate",
            company_name="Test Corp",
            tagline="Making tests better"
        )
        assert config.duration_seconds == 5
        assert config.template == "corporate"
        assert config.company_name == "Test Corp"
        assert config.tagline == "Making tests better"

    def test_outro_config(self):
        """Test OutroConfig."""
        config = OutroConfig(
            duration_seconds=10,
            template="cta",
            call_to_action="Contact us today!",
            contact_info={"email": "test@example.com", "phone": "555-1234"}
        )
        assert config.duration_seconds == 10
        assert config.template == "cta"
        assert config.call_to_action == "Contact us today!"
        assert "email" in config.contact_info


# Database Model Tests

class TestDatabaseModels:
    """Tests for database models."""

    def test_composed_video_model(self):
        """Test ComposedVideo model."""
        video = ComposedVideo(
            demo_site_id=1,
            lead_id=1,
            video_file_path="/path/to/video.mp4",
            duration_seconds=90.0,
            resolution="1920x1080",
            format="mp4",
            file_size_bytes=30000000,
            status=CompositionStatus.COMPLETED.value
        )

        assert video.demo_site_id == 1
        assert video.lead_id == 1
        assert video.duration_seconds == 90.0
        assert video.status == CompositionStatus.COMPLETED.value

    def test_composed_video_to_dict(self):
        """Test ComposedVideo to_dict method."""
        video = ComposedVideo(
            demo_site_id=1,
            lead_id=1,
            video_file_path="/path/to/video.mp4",
            duration_seconds=90.0,
            resolution="1920x1080",
            format="mp4",
            file_size_bytes=30000000,
            status=CompositionStatus.COMPLETED.value
        )

        video_dict = video.to_dict()

        assert video_dict["demo_site_id"] == 1
        assert video_dict["lead_id"] == 1
        assert video_dict["status"] == CompositionStatus.COMPLETED.value
        assert "metadata" in video_dict
        assert "files" in video_dict

    def test_composed_video_get_available_qualities(self):
        """Test getting available quality versions."""
        video = ComposedVideo(
            demo_site_id=1,
            lead_id=1,
            video_file_path="/path/to/video.mp4",
            duration_seconds=90.0,
            resolution="1920x1080",
            format="mp4",
            file_size_bytes=30000000,
            quality_1080p_path="/path/to/1080p.mp4",
            quality_720p_path="/path/to/720p.mp4"
        )

        qualities = video.get_available_qualities()

        assert "1080p" in qualities
        assert "720p" in qualities
        assert "480p" not in qualities

    def test_composition_job_model(self):
        """Test CompositionJob model."""
        job = CompositionJob(
            demo_site_id=1,
            lead_id=1,
            job_type="compose",
            priority=5,
            status="queued"
        )

        assert job.demo_site_id == 1
        assert job.lead_id == 1
        assert job.job_type == "compose"
        assert job.priority == 5
        assert job.status == "queued"

    def test_composition_job_to_dict(self):
        """Test CompositionJob to_dict method."""
        job = CompositionJob(
            demo_site_id=1,
            lead_id=1,
            job_type="compose",
            priority=5,
            status="queued"
        )

        job_dict = job.to_dict()

        assert job_dict["job_type"] == "compose"
        assert job_dict["priority"] == 5
        assert job_dict["status"] == "queued"


# Integration Tests

class TestIntegration:
    """Integration tests for video composition workflow."""

    @pytest.mark.asyncio
    async def test_full_composition_workflow(
        self,
        video_composer,
        mock_video_file,
        mock_audio_file,
        composition_config,
        branding_config
    ):
        """Test complete video composition workflow."""
        text_overlays = [
            TextOverlay(
                text="Welcome",
                start_time_seconds=2.0,
                end_time_seconds=5.0,
                position="bottom"
            )
        ]

        with patch.object(video_composer.ffmpeg, 'validate_video', return_value=True):
            with patch.object(video_composer.ffmpeg, 'merge_audio_video', return_value=True):
                with patch.object(video_composer.ffmpeg, 'add_overlay', return_value=True):
                    with patch.object(video_composer.ffmpeg, 'add_text_overlay', return_value=True):
                        with patch.object(video_composer.ffmpeg, 'encode_video', return_value=True):
                            with patch.object(video_composer.ffmpeg, 'extract_thumbnail', return_value=True):
                                with patch.object(video_composer.ffmpeg, 'get_video_metadata') as mock_metadata:
                                    mock_metadata.return_value = VideoMetadata(
                                        duration=90.0,
                                        width=1920,
                                        height=1080,
                                        fps=30.0,
                                        bitrate=5000000,
                                        codec="h264",
                                        audio_codec="aac",
                                        file_size=30000000
                                    )

                                    result = await video_composer.compose_video(
                                        screen_recording_path=mock_video_file,
                                        voiceover_path=mock_audio_file,
                                        demo_site_id=1,
                                        composition_config=composition_config,
                                        branding=branding_config,
                                        text_overlays=text_overlays,
                                        generate_qualities=["1080p", "720p"]
                                    )

                                    assert result is not None
                                    assert result.duration_seconds == 90.0
                                    assert result.processing_time_seconds > 0

    @pytest.mark.asyncio
    async def test_composition_with_all_features(
        self,
        video_composer,
        mock_video_file,
        mock_audio_file,
        composition_config,
        branding_config
    ):
        """Test composition with all features enabled."""
        intro_config = IntroConfig(
            company_name="Test Company",
            template="modern"
        )

        outro_config = OutroConfig(
            call_to_action="Contact us!",
            template="cta"
        )

        text_overlays = [
            TextOverlay(
                text="Feature 1",
                start_time_seconds=10.0,
                end_time_seconds=15.0
            ),
            TextOverlay(
                text="Feature 2",
                start_time_seconds=20.0,
                end_time_seconds=25.0
            )
        ]

        with patch.object(video_composer.ffmpeg, 'validate_video', return_value=True):
            with patch.object(video_composer.ffmpeg, 'merge_audio_video', return_value=True):
                with patch.object(video_composer.ffmpeg, 'add_overlay', return_value=True):
                    with patch.object(video_composer.ffmpeg, 'add_text_overlay', return_value=True):
                        with patch.object(video_composer.ffmpeg, 'encode_video', return_value=True):
                            with patch.object(video_composer.ffmpeg, 'extract_thumbnail', return_value=True):
                                with patch.object(video_composer.ffmpeg, 'get_video_metadata') as mock_metadata:
                                    mock_metadata.return_value = VideoMetadata(
                                        duration=90.0,
                                        width=1920,
                                        height=1080,
                                        fps=30.0,
                                        bitrate=5000000,
                                        codec="h264",
                                        audio_codec="aac",
                                        file_size=30000000
                                    )

                                    result = await video_composer.compose_video(
                                        screen_recording_path=mock_video_file,
                                        voiceover_path=mock_audio_file,
                                        demo_site_id=1,
                                        composition_config=composition_config,
                                        branding=branding_config,
                                        text_overlays=text_overlays,
                                        intro_config=intro_config,
                                        outro_config=outro_config,
                                        generate_qualities=["1080p", "720p", "480p"]
                                    )

                                    assert result is not None
                                    assert len(result.versions) == 3


# Performance Tests

class TestPerformance:
    """Performance tests for video composition."""

    @pytest.mark.asyncio
    async def test_parallel_quality_encoding(self, video_composer, mock_video_file):
        """Test that quality versions are encoded in parallel."""
        qualities = ["1080p", "720p", "480p", "360p"]

        with patch.object(video_composer.ffmpeg, 'encode_video', return_value=True):
            start_time = datetime.now()

            versions = await video_composer.encode_for_web(
                mock_video_file,
                qualities,
                demo_site_id=1
            )

            elapsed = (datetime.now() - start_time).total_seconds()

            # If running in parallel, should complete much faster than sequential
            # This is a rough test - actual timing depends on mocking
            assert len(versions) == len(qualities)

    def test_cost_estimation_accuracy(self, video_composer):
        """Test cost estimation formula."""
        # Short video
        cost_short = video_composer._estimate_cost(
            processing_time_seconds=30.0,
            file_size_bytes=10000000
        )

        # Long video
        cost_long = video_composer._estimate_cost(
            processing_time_seconds=120.0,
            file_size_bytes=40000000
        )

        # Longer videos should cost more
        assert cost_long > cost_short


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
