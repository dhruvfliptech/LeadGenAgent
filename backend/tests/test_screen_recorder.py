"""
Tests for Screen Recording Service.
"""

import pytest
import asyncio
from pathlib import Path
from app.services.video.screen_recorder import (
    ScreenRecorder,
    RecordingConfig,
    Interaction,
    InteractionSequence,
    RecordingQualityPresets
)
from app.services.video.interaction_generator import InteractionGenerator


class TestRecordingConfig:
    """Test RecordingConfig model."""

    def test_default_config(self):
        """Test default configuration."""
        config = RecordingConfig()
        assert config.resolution == "1920x1080"
        assert config.frame_rate == 30
        assert config.video_format == "mp4"
        assert config.quality == "high"

    def test_get_viewport(self):
        """Test viewport extraction from resolution."""
        config = RecordingConfig(resolution="1280x720")
        viewport = config.get_viewport()
        assert viewport["width"] == 1280
        assert viewport["height"] == 720

    def test_get_video_bitrate(self):
        """Test bitrate calculation based on quality."""
        config_high = RecordingConfig(quality="high")
        assert config_high.get_video_bitrate() == 5000

        config_medium = RecordingConfig(quality="medium")
        assert config_medium.get_video_bitrate() == 2500


class TestInteraction:
    """Test Interaction model."""

    def test_scroll_interaction(self):
        """Test scroll interaction creation."""
        interaction = Interaction(
            type="scroll",
            selector="header",
            duration_ms=1000
        )
        assert interaction.type == "scroll"
        assert interaction.selector == "header"
        assert interaction.duration_ms == 1000

    def test_click_interaction(self):
        """Test click interaction creation."""
        interaction = Interaction(
            type="click",
            selector=".cta-button",
            x=640,
            y=360,
            duration_ms=500
        )
        assert interaction.type == "click"
        assert interaction.x == 640
        assert interaction.y == 360


class TestInteractionSequence:
    """Test InteractionSequence model."""

    def test_calculate_duration(self):
        """Test duration calculation."""
        interactions = [
            Interaction(type="wait", duration_ms=1000),
            Interaction(type="scroll", selector="body", duration_ms=2000),
            Interaction(type="click", selector=".btn", duration_ms=500)
        ]
        sequence = InteractionSequence(interactions=interactions)
        sequence.calculate_duration()
        assert sequence.total_duration_seconds == 3.5


class TestRecordingQualityPresets:
    """Test quality presets."""

    def test_high_quality_preset(self):
        """Test high quality preset."""
        config = RecordingQualityPresets.high_quality()
        assert config.resolution == "1920x1080"
        assert config.frame_rate == 30
        assert config.quality == "high"

    def test_medium_quality_preset(self):
        """Test medium quality preset."""
        config = RecordingQualityPresets.medium_quality()
        assert config.resolution == "1280x720"
        assert config.frame_rate == 30
        assert config.quality == "medium"

    def test_low_quality_preset(self):
        """Test low quality preset."""
        config = RecordingQualityPresets.low_quality()
        assert config.frame_rate == 24
        assert config.quality == "low"


class TestInteractionGenerator:
    """Test InteractionGenerator."""

    def test_calculate_element_importance(self):
        """Test element importance scoring."""
        generator = InteractionGenerator()

        button_element = {
            "tag_name": "button",
            "text": "Sign Up Now",
            "visible": True,
            "width": 200,
            "height": 50
        }
        score = generator._calculate_element_importance(button_element)
        assert score > 0.8  # Buttons with CTA text should score high

    def test_create_smooth_mouse_path(self):
        """Test smooth mouse path generation."""
        generator = InteractionGenerator()
        path = generator.create_smooth_mouse_path(0, 0, 100, 100, steps=10)

        assert len(path) == 11  # steps + 1
        assert path[0] == (0, 0)  # Start point
        assert path[-1] == (100, 100)  # End point
        assert all(isinstance(p, tuple) and len(p) == 2 for p in path)

    def test_generate_scroll_interaction(self):
        """Test scroll interaction generation."""
        generator = InteractionGenerator()
        interaction = generator.generate_scroll_interaction(".content")

        assert interaction.type == "scroll"
        assert interaction.selector == ".content"
        assert interaction.duration_ms >= 500


class TestScreenRecorder:
    """Test ScreenRecorder class."""

    def test_recorder_initialization(self):
        """Test recorder initialization."""
        recorder = ScreenRecorder()
        assert recorder.storage_path.exists()
        assert recorder.browser is None
        assert recorder.context is None
        assert recorder.page is None

    def test_extract_demo_id_from_url(self):
        """Test demo ID extraction from URL."""
        recorder = ScreenRecorder()

        url1 = "https://demo-123.vercel.app"
        assert recorder._extract_demo_id_from_url(url1) == "123"

        url2 = "https://example.com"
        assert recorder._extract_demo_id_from_url(url2) == "unknown"


# Integration Tests (require Playwright)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_record_simple_page():
    """
    Test recording a simple webpage.
    
    This test requires Playwright to be installed and may be slow.
    Run with: pytest -m integration
    """
    recorder = ScreenRecorder()
    config = RecordingQualityPresets.low_quality()

    # Use a simple, stable webpage
    result = await recorder.record_demo_site(
        demo_site_url="https://example.com",
        recording_config=config
    )

    assert result.success
    assert result.video_file_path is not None
    assert Path(result.video_file_path).exists()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_record_with_interactions():
    """Test recording with custom interactions."""
    recorder = ScreenRecorder()
    config = RecordingQualityPresets.low_quality()

    interactions = InteractionSequence(
        interactions=[
            Interaction(type="wait", duration_ms=1000),
            Interaction(type="scroll", scroll_amount=300, duration_ms=1000),
            Interaction(type="wait", duration_ms=1000)
        ]
    )
    interactions.calculate_duration()

    result = await recorder.record_demo_site(
        demo_site_url="https://example.com",
        interactions=interactions,
        recording_config=config
    )

    assert result.success
    assert result.duration_seconds > 0


# Performance Tests

@pytest.mark.benchmark
def test_interaction_sequence_creation_performance(benchmark):
    """Benchmark interaction sequence creation."""
    def create_sequence():
        interactions = [
            Interaction(type="wait", duration_ms=1000)
            for _ in range(100)
        ]
        sequence = InteractionSequence(interactions=interactions)
        sequence.calculate_duration()
        return sequence

    result = benchmark(create_sequence)
    assert result.total_duration_seconds == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
