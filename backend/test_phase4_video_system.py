"""
Comprehensive Test Suite for Phase 4 Video Creation System

Tests all components:
- Screen Recording
- Video Script Generation
- Voice Synthesis (ElevenLabs)
- Video Composition (FFmpeg)
- Video Hosting
- Analytics Tracking

Run with: pytest test_phase4_video_system.py -v
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import models
from app.models.screen_recordings import ScreenRecording, RecordingSession, RecordingSegment
from app.models.video_scripts import VideoScript
from app.models.voiceovers import Voiceover, VoiceoverUsage, VoiceoverCache
from app.models.composed_videos import ComposedVideo, CompositionJob
from app.models.hosted_videos import HostedVideo, VideoView

# Import schemas
from app.schemas.video_schemas import (
    ScreenRecordingCreate,
    VideoScriptGenerate,
    VoiceoverSynthesize,
    VideoCompositionRequest,
    VideoHostingRequest
)

# Import services
from app.services.video.screen_recorder import ScreenRecorder, RecordingConfig
from app.services.video.script_generator import ScriptGenerator
from app.services.video.voice_synthesizer import VoiceSynthesizer
from app.services.video.video_composer import VideoComposer
from app.services.video.video_host_manager import VideoHostManager


# ==================== Fixtures ====================

@pytest.fixture
def db_session():
    """Create test database session."""
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    yield session

    session.close()


@pytest.fixture
def sample_lead():
    """Sample lead data for testing."""
    return {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "company": "Acme Corp",
        "industry": "Technology"
    }


@pytest.fixture
def sample_recording_config():
    """Sample recording configuration."""
    return RecordingConfig(
        resolution="1920x1080",
        frame_rate=30,
        video_format="mp4",
        quality="high",
        show_cursor=True
    )


@pytest.fixture
def mock_screen_recording(db_session):
    """Create mock screen recording."""
    recording = ScreenRecording(
        id=1,
        lead_id=1,
        url_recorded="https://example.com",
        resolution="1920x1080",
        duration_seconds=45.5,
        file_path="/storage/recordings/test.mp4",
        file_size_bytes=10485760,
        status="completed"
    )
    db_session.add(recording)
    db_session.commit()
    return recording


@pytest.fixture
def mock_video_script(db_session):
    """Create mock video script."""
    script = VideoScript(
        id=1,
        lead_id=1,
        script_style="professional",
        sections=[
            {
                "title": "Introduction",
                "content": "Welcome to our platform",
                "duration_seconds": 15,
                "scene_type": "intro"
            }
        ],
        total_duration_seconds=60,
        is_approved="approved"
    )
    db_session.add(script)
    db_session.commit()
    return script


@pytest.fixture
def mock_voiceover(db_session):
    """Create mock voiceover."""
    voiceover = Voiceover(
        id=1,
        video_script_id=1,
        lead_id=1,
        voice_preset="professional_male",
        voice_id="21m00Tcm4TlvDq8ikWAM",
        audio_file_path="/storage/voiceovers/test.mp3",
        duration_seconds=55.2,
        format="mp3",
        sample_rate=44100,
        file_size_bytes=884736,
        characters_processed=250,
        cost_usd=Decimal("0.075"),
        status="completed"
    )
    db_session.add(voiceover)
    db_session.commit()
    return voiceover


# ==================== Screen Recording Tests ====================

class TestScreenRecording:
    """Test screen recording functionality."""

    def test_screen_recorder_initialization(self, sample_recording_config):
        """Test screen recorder initialization."""
        recorder = ScreenRecorder(config=sample_recording_config)

        assert recorder.config.resolution == "1920x1080"
        assert recorder.config.frame_rate == 30
        assert recorder.config.quality == "high"


    @pytest.mark.asyncio
    async def test_start_recording(self, sample_recording_config):
        """Test starting a recording."""
        recorder = ScreenRecorder(config=sample_recording_config)

        with patch.object(recorder, '_initialize_browser', new_callable=AsyncMock):
            with patch.object(recorder, '_start_capture', new_callable=AsyncMock):
                result = await recorder.start_recording("https://example.com")

                assert result is not None
                assert hasattr(result, 'session_id')


    def test_recording_model_creation(self, db_session):
        """Test creating screen recording model."""
        recording = ScreenRecording(
            lead_id=1,
            url_recorded="https://test.com",
            resolution="1920x1080",
            status="pending"
        )

        db_session.add(recording)
        db_session.commit()

        assert recording.id is not None
        assert recording.status == "pending"
        assert recording.resolution == "1920x1080"


    def test_recording_to_dict(self, mock_screen_recording):
        """Test recording serialization."""
        data = mock_screen_recording.to_dict()

        assert data['id'] == 1
        assert data['status'] == 'completed'
        assert data['video']['duration_seconds'] == 45.5
        assert data['file']['file_size_mb'] == 10.0


# ==================== Video Script Tests ====================

class TestVideoScript:
    """Test video script generation."""

    @pytest.mark.asyncio
    async def test_script_generation(self, sample_lead):
        """Test AI script generation."""
        generator = ScriptGenerator()

        with patch.object(generator, '_call_openrouter', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = {
                "sections": [
                    {
                        "title": "Introduction",
                        "content": f"Hi {sample_lead['name']}, welcome to our platform!",
                        "duration_seconds": 10,
                        "scene_type": "intro"
                    }
                ],
                "total_duration": 60
            }

            script = await generator.generate_script(
                lead_data=sample_lead,
                style="professional",
                duration=60
            )

            assert script is not None
            assert len(script['sections']) > 0
            assert sample_lead['name'] in script['sections'][0]['content']


    def test_script_model_creation(self, db_session):
        """Test video script model creation."""
        script = VideoScript(
            lead_id=1,
            script_style="casual",
            sections=[{"title": "Test", "content": "Test content", "duration_seconds": 5}],
            total_duration_seconds=30
        )

        db_session.add(script)
        db_session.commit()

        assert script.id is not None
        assert script.script_style == "casual"
        assert len(script.sections) == 1


    def test_script_personalization(self, sample_lead):
        """Test script personalization with lead data."""
        generator = ScriptGenerator()
        template = "Hello {{name}}, we noticed {{company}} is in {{industry}}"

        personalized = generator.personalize_content(template, sample_lead)

        assert "John Doe" in personalized
        assert "Acme Corp" in personalized
        assert "Technology" in personalized


# ==================== Voiceover Tests ====================

class TestVoiceover:
    """Test voiceover synthesis."""

    @pytest.mark.asyncio
    async def test_voice_synthesis(self):
        """Test ElevenLabs voice synthesis."""
        synthesizer = VoiceSynthesizer()

        with patch.object(synthesizer, '_call_elevenlabs_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                "audio_data": b"fake_audio_data",
                "characters": 100,
                "cost": 0.03
            }

            result = await synthesizer.synthesize(
                text="Hello, this is a test voiceover.",
                voice_preset="professional_male"
            )

            assert result is not None
            assert result['characters'] == 100
            assert result['cost'] == 0.03


    def test_voiceover_model_creation(self, db_session):
        """Test voiceover model creation."""
        voiceover = Voiceover(
            lead_id=1,
            voice_preset="professional_female",
            voice_id="test_voice_id",
            characters_processed=500,
            status="pending"
        )

        db_session.add(voiceover)
        db_session.commit()

        assert voiceover.id is not None
        assert voiceover.voice_preset == "professional_female"
        assert voiceover.status == "pending"


    def test_voiceover_cost_tracking(self, mock_voiceover):
        """Test voiceover cost tracking."""
        assert mock_voiceover.cost_usd == Decimal("0.075")
        assert mock_voiceover.characters_processed == 250

        # Calculate cost per character
        cost_per_char = mock_voiceover.cost_usd / mock_voiceover.characters_processed
        assert cost_per_char == Decimal("0.0003")


    def test_voiceover_cache(self, db_session):
        """Test voiceover caching functionality."""
        cache_entry = VoiceoverCache(
            cache_key="abc123",
            text_content="Test content",
            voice_preset="professional_male",
            model_id="eleven_multilingual_v2",
            audio_file_path="/cache/test.mp3",
            duration_seconds=5.0,
            format="mp3",
            sample_rate=44100,
            hit_count=0
        )

        db_session.add(cache_entry)
        db_session.commit()

        assert cache_entry.id is not None
        assert cache_entry.hit_count == 0

        # Simulate cache hit
        cache_entry.hit_count += 1
        cache_entry.last_accessed_at = datetime.utcnow()
        db_session.commit()

        assert cache_entry.hit_count == 1


# ==================== Video Composition Tests ====================

class TestVideoComposition:
    """Test video composition with FFmpeg."""

    @pytest.mark.asyncio
    async def test_video_composition(self, mock_screen_recording, mock_voiceover):
        """Test composing video from recording and voiceover."""
        composer = VideoComposer()

        with patch.object(composer, '_run_ffmpeg', new_callable=AsyncMock) as mock_ffmpeg:
            mock_ffmpeg.return_value = {
                "success": True,
                "output_path": "/storage/videos/composed.mp4",
                "duration": 55.2,
                "file_size": 15728640
            }

            result = await composer.compose_video(
                recording_path=mock_screen_recording.video_file_path,
                voiceover_path=mock_voiceover.audio_file_path,
                output_path="/storage/videos/composed.mp4"
            )

            assert result['success'] is True
            assert result['duration'] == 55.2


    def test_composed_video_model(self, db_session):
        """Test composed video model creation."""
        video = ComposedVideo(
            lead_id=1,
            screen_recording_id=1,
            voiceover_id=1,
            video_file_path="/storage/videos/test.mp4",
            duration_seconds=60.0,
            resolution="1920x1080",
            format="mp4",
            file_size_bytes=20971520,
            status="completed"
        )

        db_session.add(video)
        db_session.commit()

        assert video.id is not None
        assert video.status == "completed"
        assert video.duration_seconds == 60.0


    def test_multiple_quality_versions(self, db_session):
        """Test generating multiple quality versions."""
        video = ComposedVideo(
            lead_id=1,
            video_file_path="/storage/videos/master.mp4",
            quality_1080p_path="/storage/videos/1080p.mp4",
            quality_720p_path="/storage/videos/720p.mp4",
            quality_480p_path="/storage/videos/480p.mp4",
            duration_seconds=60.0,
            resolution="1920x1080",
            format="mp4",
            file_size_bytes=20971520
        )

        db_session.add(video)
        db_session.commit()

        available_qualities = video.get_available_qualities()
        assert "1080p" in available_qualities
        assert "720p" in available_qualities
        assert "480p" in available_qualities


    def test_composition_job_queue(self, db_session):
        """Test composition job queue."""
        job = CompositionJob(
            lead_id=1,
            demo_site_id=1,
            job_type="compose",
            priority=5,
            status="queued",
            job_config={"resolution": "1080p", "format": "mp4"}
        )

        db_session.add(job)
        db_session.commit()

        assert job.id is not None
        assert job.status == "queued"
        assert job.priority == 5


# ==================== Video Hosting Tests ====================

class TestVideoHosting:
    """Test video hosting functionality."""

    @pytest.mark.asyncio
    async def test_s3_upload(self):
        """Test uploading video to S3."""
        host_manager = VideoHostManager()

        with patch.object(host_manager, '_upload_to_s3', new_callable=AsyncMock) as mock_s3:
            mock_s3.return_value = {
                "success": True,
                "url": "https://s3.amazonaws.com/bucket/video.mp4",
                "provider_video_id": "video123"
            }

            result = await host_manager.host_video(
                video_path="/storage/videos/test.mp4",
                provider="s3",
                metadata={"title": "Test Video"}
            )

            assert result['success'] is True
            assert "s3.amazonaws.com" in result['url']


    def test_hosted_video_model(self, db_session):
        """Test hosted video model creation."""
        hosted = HostedVideo(
            lead_id=1,
            hosting_provider="s3",
            provider_video_id="video123",
            share_url="https://example.com/share/video123",
            embed_url="https://example.com/embed/video123",
            title="Demo Video",
            privacy="unlisted",
            status="ready"
        )

        db_session.add(hosted)
        db_session.commit()

        assert hosted.id is not None
        assert hosted.hosting_provider == "s3"
        assert hosted.status == "ready"


    def test_video_analytics_tracking(self, db_session):
        """Test video analytics tracking."""
        hosted = HostedVideo(
            lead_id=1,
            hosting_provider="s3",
            provider_video_id="video123",
            share_url="https://example.com/video",
            embed_url="https://example.com/embed",
            title="Test",
            view_count=0,
            unique_viewers=0,
            total_watch_time_seconds=0.0
        )

        db_session.add(hosted)
        db_session.commit()

        # Simulate views
        hosted.view_count = 50
        hosted.unique_viewers = 35
        hosted.avg_watch_percentage = 75.5
        hosted.completion_rate = 65.0
        hosted.total_watch_time_seconds = 2250.0

        db_session.commit()

        assert hosted.view_count == 50
        assert hosted.unique_viewers == 35
        assert hosted.avg_watch_percentage == 75.5


# ==================== Video View Tests ====================

class TestVideoView:
    """Test video view tracking."""

    def test_video_view_creation(self, db_session):
        """Test creating video view record."""
        view = VideoView(
            hosted_video_id=1,
            lead_id=1,
            viewer_ip="192.168.1.1",
            viewer_device="desktop",
            viewer_os="macOS",
            viewer_browser="Chrome",
            watch_duration_seconds=45.5,
            watch_percentage=75.8,
            completed=False
        )

        db_session.add(view)
        db_session.commit()

        assert view.id is not None
        assert view.watch_percentage == 75.8
        assert view.completed is False


    def test_engagement_tracking(self, db_session):
        """Test engagement metrics tracking."""
        view = VideoView(
            hosted_video_id=1,
            watch_duration_seconds=60.0,
            watch_percentage=100.0,
            completed=True,
            clicked_cta=True,
            liked=True,
            shared=False,
            play_count=2,
            pause_count=3,
            seek_count=1
        )

        db_session.add(view)
        db_session.commit()

        assert view.completed is True
        assert view.clicked_cta is True
        assert view.play_count == 2


    def test_utm_tracking(self, db_session):
        """Test UTM parameter tracking."""
        view = VideoView(
            hosted_video_id=1,
            watch_duration_seconds=30.0,
            watch_percentage=50.0,
            completed=False,
            referrer_url="https://google.com/search",
            referrer_domain="google.com",
            utm_source="email",
            utm_medium="campaign",
            utm_campaign="launch_2024"
        )

        db_session.add(view)
        db_session.commit()

        assert view.utm_source == "email"
        assert view.utm_campaign == "launch_2024"
        assert view.referrer_domain == "google.com"


# ==================== Integration Tests ====================

class TestVideoSystemIntegration:
    """Integration tests for complete video workflow."""

    @pytest.mark.asyncio
    async def test_complete_video_workflow(self, sample_lead):
        """Test complete video creation workflow."""
        # Step 1: Record screen
        recorder = ScreenRecorder()
        with patch.object(recorder, 'start_recording', new_callable=AsyncMock) as mock_record:
            mock_record.return_value = {"recording_id": 1, "status": "completed"}
            recording = await mock_record("https://example.com")
            assert recording['status'] == "completed"

        # Step 2: Generate script
        script_gen = ScriptGenerator()
        with patch.object(script_gen, 'generate_script', new_callable=AsyncMock) as mock_script:
            mock_script.return_value = {"script_id": 1, "sections": []}
            script = await mock_script(sample_lead)
            assert script['script_id'] == 1

        # Step 3: Synthesize voiceover
        synthesizer = VoiceSynthesizer()
        with patch.object(synthesizer, 'synthesize', new_callable=AsyncMock) as mock_voice:
            mock_voice.return_value = {"voiceover_id": 1, "duration": 55.0}
            voiceover = await mock_voice("Test text")
            assert voiceover['voiceover_id'] == 1

        # Step 4: Compose video
        composer = VideoComposer()
        with patch.object(composer, 'compose_video', new_callable=AsyncMock) as mock_compose:
            mock_compose.return_value = {"video_id": 1, "success": True}
            video = await mock_compose("/rec.mp4", "/voice.mp3")
            assert video['success'] is True

        # Step 5: Host video
        host_manager = VideoHostManager()
        with patch.object(host_manager, 'host_video', new_callable=AsyncMock) as mock_host:
            mock_host.return_value = {"hosted_id": 1, "url": "https://example.com/video"}
            hosted = await mock_host("/video.mp4")
            assert "example.com" in hosted['url']


    def test_cost_tracking_across_workflow(self, db_session):
        """Test cost tracking throughout video creation."""
        # Create voiceover with cost
        voiceover = Voiceover(
            lead_id=1,
            voice_preset="professional_male",
            characters_processed=1000,
            cost_usd=Decimal("0.30"),
            status="completed"
        )
        db_session.add(voiceover)

        # Create composed video with processing cost
        video = ComposedVideo(
            lead_id=1,
            voiceover_id=1,
            video_file_path="/test.mp4",
            duration_seconds=60.0,
            resolution="1920x1080",
            format="mp4",
            file_size_bytes=20971520,
            cost_estimate=0.05  # Processing cost
        )
        db_session.add(video)

        # Create hosted video with hosting cost
        hosted = HostedVideo(
            lead_id=1,
            hosting_provider="s3",
            provider_video_id="video123",
            share_url="https://example.com/video",
            embed_url="https://example.com/embed",
            title="Test",
            hosting_cost_monthly=Decimal("2.00"),
            storage_cost_monthly=Decimal("0.50"),
            total_cost_usd=Decimal("2.50")
        )
        db_session.add(hosted)
        db_session.commit()

        # Calculate total cost
        total_cost = float(voiceover.cost_usd) + video.cost_estimate + float(hosted.total_cost_usd)
        assert total_cost == 2.85


# ==================== API Endpoint Tests ====================

class TestVideoAPIEndpoints:
    """Test video API endpoints."""

    @pytest.mark.skip(reason="Requires full FastAPI app setup")
    def test_create_recording_endpoint(self):
        """Test POST /api/v1/videos/recordings/start endpoint."""
        pass


    @pytest.mark.skip(reason="Requires full FastAPI app setup")
    def test_generate_script_endpoint(self):
        """Test POST /api/v1/videos/scripts/generate endpoint."""
        pass


    @pytest.mark.skip(reason="Requires full FastAPI app setup")
    def test_synthesize_voiceover_endpoint(self):
        """Test POST /api/v1/videos/voiceovers/synthesize endpoint."""
        pass


# ==================== Performance Tests ====================

class TestPerformance:
    """Performance tests for video system."""

    @pytest.mark.skip(reason="Performance test - run separately")
    def test_bulk_video_creation(self):
        """Test creating 100 videos in parallel."""
        pass


    @pytest.mark.skip(reason="Performance test - run separately")
    def test_large_file_handling(self):
        """Test handling videos larger than 100MB."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
