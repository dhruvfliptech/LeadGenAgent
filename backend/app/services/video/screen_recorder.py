"""
Screen Recording Service using Playwright.

Automatically records demo site interactions with smooth animations,
cursor movements, and configurable video quality settings.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RecordingConfig(BaseModel):
    """Configuration for screen recording."""

    resolution: str = "1920x1080"
    frame_rate: int = 30
    video_format: str = "mp4"
    video_codec: str = "h264"
    quality: str = "high"  # low, medium, high, ultra
    show_cursor: bool = True
    scroll_speed: int = 1000  # Pixels per second
    transition_duration_ms: int = 300
    highlight_clicks: bool = True
    highlight_color: str = "#FF0000"
    viewport_width: int = 1920
    viewport_height: int = 1080

    def get_viewport(self) -> Dict[str, int]:
        """Get viewport dimensions from resolution."""
        if 'x' in self.resolution.lower():
            width, height = map(int, self.resolution.lower().split('x'))
            return {"width": width, "height": height}
        return {"width": self.viewport_width, "height": self.viewport_height}

    def get_video_bitrate(self) -> int:
        """Get video bitrate based on quality setting."""
        bitrates = {
            "low": 1500,
            "medium": 2500,
            "high": 5000,
            "ultra": 10000
        }
        return bitrates.get(self.quality, 5000)


class Interaction(BaseModel):
    """Represents a single interaction in the recording."""

    type: str  # "click", "scroll", "hover", "type", "wait", "highlight"
    selector: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    duration_ms: int = 1000
    smooth: bool = True
    text: Optional[str] = None  # For "type" interactions
    scroll_amount: Optional[int] = None  # For "scroll" interactions


class InteractionSequence(BaseModel):
    """Sequence of interactions to perform."""

    interactions: List[Interaction]
    total_duration_seconds: float = 0.0

    def calculate_duration(self):
        """Calculate total duration from interactions."""
        self.total_duration_seconds = sum(i.duration_ms for i in self.interactions) / 1000


class RecordingResult(BaseModel):
    """Result of a recording session."""

    success: bool
    video_file_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    duration_seconds: float = 0.0
    file_size_bytes: int = 0
    resolution: str = "1920x1080"
    frame_rate: int = 30
    total_frames: int = 0
    segments_count: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScreenRecorder:
    """
    Screen recorder for demo sites using Playwright.

    Captures automated interactions with smooth animations and
    exports as high-quality video files.
    """

    def __init__(self, storage_path: str = "/Users/greenmachine2.0/Craigslist/backend/storage/recordings"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def initialize_browser(self, config: RecordingConfig) -> BrowserContext:
        """Initialize Playwright browser with recording capabilities."""
        playwright = await async_playwright().start()

        # Launch browser in headless mode for production
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )

        # Create context with viewport
        viewport = config.get_viewport()
        self.context = await self.browser.new_context(
            viewport=viewport,
            record_video_dir=str(self.storage_path / "temp"),
            record_video_size=viewport,
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )

        return self.context

    async def record_demo_site(
        self,
        demo_site_url: str,
        interactions: Optional[InteractionSequence] = None,
        recording_config: Optional[RecordingConfig] = None
    ) -> RecordingResult:
        """
        Record a demo site with optional interaction sequence.

        Args:
            demo_site_url: URL of the demo site to record
            interactions: Optional sequence of interactions to perform
            recording_config: Recording configuration

        Returns:
            RecordingResult with video file path and metadata
        """
        if recording_config is None:
            recording_config = RecordingConfig()

        result = RecordingResult(
            success=False,
            resolution=recording_config.resolution,
            frame_rate=recording_config.frame_rate
        )

        start_time = time.time()
        session_id = str(uuid.uuid4())

        try:
            # Initialize browser
            await self.initialize_browser(recording_config)

            # Create new page
            self.page = await self.context.new_page()

            # Navigate to demo site
            logger.info(f"Recording demo site: {demo_site_url}")
            await self.page.goto(demo_site_url, wait_until="networkidle", timeout=30000)

            # Wait for page to stabilize
            await asyncio.sleep(2)

            # Perform interactions if provided
            if interactions:
                logger.info(f"Performing {len(interactions.interactions)} interactions")
                await self._perform_interactions(self.page, interactions, recording_config)
            else:
                # Default: scroll through page
                logger.info("No interactions provided, performing default scroll")
                await self._default_page_scroll(self.page, recording_config)

            # Close page to stop recording
            await self.page.close()

            # Get recorded video path
            video_path = await self._get_video_path()

            if video_path and os.path.exists(video_path):
                # Move video to final location
                demo_id = self._extract_demo_id_from_url(demo_site_url)
                final_path = await self._save_recording(video_path, demo_id, session_id)

                # Generate thumbnail
                thumbnail_path = await self._generate_thumbnail(final_path)

                # Calculate metrics
                duration = time.time() - start_time
                file_size = os.path.getsize(final_path)

                result.success = True
                result.video_file_path = str(final_path)
                result.thumbnail_path = str(thumbnail_path) if thumbnail_path else None
                result.duration_seconds = duration
                result.file_size_bytes = file_size
                result.total_frames = int(duration * recording_config.frame_rate)
                result.segments_count = len(interactions.interactions) if interactions else 1
                result.metadata = {
                    "session_id": session_id,
                    "demo_site_url": demo_site_url,
                    "recording_config": recording_config.dict(),
                    "browser_version": "Playwright Chromium"
                }

                logger.info(f"Recording completed: {final_path} ({file_size / 1024 / 1024:.2f} MB)")
            else:
                raise Exception("Video recording failed - no video file generated")

        except Exception as e:
            logger.error(f"Recording failed: {str(e)}", exc_info=True)
            result.error_message = str(e)

        finally:
            # Cleanup
            await self._cleanup()

        return result

    async def record_scene(
        self,
        url: str,
        scene_config: Dict[str, Any],
        browser_context: Optional[BrowserContext] = None
    ) -> bytes:
        """
        Record a specific scene from a video script.

        Args:
            url: URL to record
            scene_config: Scene configuration with interactions
            browser_context: Optional existing browser context

        Returns:
            Video segment as bytes
        """
        if browser_context:
            self.context = browser_context
        else:
            config = RecordingConfig()
            await self.initialize_browser(config)

        page = await self.context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Perform scene-specific interactions
            if "interactions" in scene_config:
                interactions = InteractionSequence(
                    interactions=[Interaction(**i) for i in scene_config["interactions"]]
                )
                await self._perform_interactions(page, interactions, RecordingConfig())

            # Wait for scene duration
            duration = scene_config.get("duration_seconds", 5)
            await asyncio.sleep(duration)

            await page.close()

            # Return video bytes
            video_path = await self._get_video_path()
            if video_path:
                with open(video_path, 'rb') as f:
                    return f.read()

            return b""

        finally:
            await page.close()

    async def record_with_interactions(
        self,
        url: str,
        interactions: List[Interaction],
        duration_seconds: int
    ) -> bytes:
        """
        Record with a specific list of interactions.

        Args:
            url: URL to record
            interactions: List of interactions to perform
            duration_seconds: Total duration

        Returns:
            Video segment as bytes
        """
        sequence = InteractionSequence(interactions=interactions)
        config = RecordingConfig()

        result = await self.record_demo_site(url, sequence, config)

        if result.success and result.video_file_path:
            with open(result.video_file_path, 'rb') as f:
                return f.read()

        return b""

    async def _perform_interactions(
        self,
        page: Page,
        interactions: InteractionSequence,
        config: RecordingConfig
    ):
        """Perform a sequence of interactions on the page."""
        for interaction in interactions.interactions:
            try:
                await self._perform_single_interaction(page, interaction, config)
            except Exception as e:
                logger.warning(f"Interaction failed: {interaction.type} - {str(e)}")
                continue

    async def _perform_single_interaction(
        self,
        page: Page,
        interaction: Interaction,
        config: RecordingConfig
    ):
        """Perform a single interaction."""
        if interaction.type == "wait":
            await asyncio.sleep(interaction.duration_ms / 1000)

        elif interaction.type == "scroll":
            if interaction.selector:
                # Scroll to element
                element = await page.query_selector(interaction.selector)
                if element:
                    await element.scroll_into_view_if_needed()
                    await asyncio.sleep(interaction.duration_ms / 1000)
            elif interaction.scroll_amount:
                # Scroll by amount
                await page.evaluate(f"window.scrollBy(0, {interaction.scroll_amount})")
                await asyncio.sleep(interaction.duration_ms / 1000)

        elif interaction.type == "hover":
            if interaction.selector:
                await page.hover(interaction.selector)
                await asyncio.sleep(interaction.duration_ms / 1000)
            elif interaction.x and interaction.y:
                await page.mouse.move(interaction.x, interaction.y)
                await asyncio.sleep(interaction.duration_ms / 1000)

        elif interaction.type == "click":
            if interaction.selector:
                # Highlight if enabled
                if config.highlight_clicks:
                    await self._highlight_element(page, interaction.selector, config.highlight_color)
                await page.click(interaction.selector)
                await asyncio.sleep(interaction.duration_ms / 1000)
            elif interaction.x and interaction.y:
                await page.mouse.click(interaction.x, interaction.y)
                await asyncio.sleep(interaction.duration_ms / 1000)

        elif interaction.type == "type":
            if interaction.selector and interaction.text:
                await page.fill(interaction.selector, interaction.text)
                await asyncio.sleep(interaction.duration_ms / 1000)

        elif interaction.type == "highlight":
            if interaction.selector:
                await self._highlight_element(page, interaction.selector, config.highlight_color)
                await asyncio.sleep(interaction.duration_ms / 1000)
                await self._remove_highlight(page, interaction.selector)

    async def _highlight_element(self, page: Page, selector: str, color: str = "#FF0000"):
        """Add a highlight border to an element."""
        try:
            await page.evaluate(f"""
                (selector) => {{
                    const element = document.querySelector(selector);
                    if (element) {{
                        element.style.outline = '3px solid {color}';
                        element.style.outlineOffset = '2px';
                    }}
                }}
            """, selector)
        except Exception as e:
            logger.warning(f"Failed to highlight element {selector}: {str(e)}")

    async def _remove_highlight(self, page: Page, selector: str):
        """Remove highlight from an element."""
        try:
            await page.evaluate("""
                (selector) => {
                    const element = document.querySelector(selector);
                    if (element) {
                        element.style.outline = '';
                        element.style.outlineOffset = '';
                    }
                }
            """, selector)
        except Exception as e:
            logger.warning(f"Failed to remove highlight from {selector}: {str(e)}")

    async def _default_page_scroll(self, page: Page, config: RecordingConfig):
        """Perform default page scroll animation."""
        # Get page height
        height = await page.evaluate("document.body.scrollHeight")

        # Scroll in smooth increments
        scroll_increment = 300
        total_scrolls = min(height // scroll_increment, 10)  # Max 10 scrolls

        for i in range(total_scrolls):
            await page.evaluate(f"window.scrollBy(0, {scroll_increment})")
            await asyncio.sleep(0.5)

        # Scroll back to top
        await asyncio.sleep(1)
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)

    async def _get_video_path(self) -> Optional[str]:
        """Get the path to the recorded video."""
        if self.page:
            video = self.page.video
            if video:
                return await video.path()
        return None

    def _extract_demo_id_from_url(self, url: str) -> str:
        """Extract demo ID from URL or generate one."""
        # Try to extract from URL patterns like demo-123.vercel.app
        import re
        match = re.search(r'demo-(\d+)', url)
        if match:
            return match.group(1)
        return "unknown"

    async def _save_recording(self, temp_path: str, demo_id: str, session_id: str) -> Path:
        """Save recording to final location."""
        # Create demo-specific directory
        demo_dir = self.storage_path / demo_id
        demo_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{session_id}_{timestamp}.webm"
        final_path = demo_dir / filename

        # Move file
        import shutil
        shutil.move(temp_path, final_path)

        return final_path

    async def _generate_thumbnail(self, video_path: Path) -> Optional[Path]:
        """Generate thumbnail from video (placeholder - requires ffmpeg)."""
        # This would use ffmpeg to extract a thumbnail frame
        # For now, return None
        # TODO: Implement with ffmpeg
        return None

    async def _cleanup(self):
        """Cleanup browser resources."""
        try:
            if self.page and not self.page.is_closed():
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.warning(f"Cleanup error: {str(e)}")

    def merge_video_segments(
        self,
        segments: List[bytes],
        transitions: List[str]
    ) -> bytes:
        """
        Merge video segments with transitions.

        This is a placeholder for future implementation using ffmpeg.

        Args:
            segments: List of video segment bytes
            transitions: List of transition types

        Returns:
            Merged video as bytes
        """
        # TODO: Implement with ffmpeg
        # For now, just return the first segment
        if segments:
            return segments[0]
        return b""


class RecordingQualityPresets:
    """Predefined quality presets for common use cases."""

    @staticmethod
    def high_quality() -> RecordingConfig:
        """High quality preset (1080p, 30 FPS, 5 Mbps)."""
        return RecordingConfig(
            resolution="1920x1080",
            frame_rate=30,
            quality="high",
            video_format="mp4",
            video_codec="h264"
        )

    @staticmethod
    def medium_quality() -> RecordingConfig:
        """Medium quality preset (720p, 30 FPS, 2.5 Mbps)."""
        return RecordingConfig(
            resolution="1280x720",
            frame_rate=30,
            quality="medium",
            video_format="mp4",
            video_codec="h264",
            viewport_width=1280,
            viewport_height=720
        )

    @staticmethod
    def low_quality() -> RecordingConfig:
        """Low quality preset (720p, 24 FPS, 1.5 Mbps)."""
        return RecordingConfig(
            resolution="1280x720",
            frame_rate=24,
            quality="low",
            video_format="mp4",
            video_codec="h264",
            viewport_width=1280,
            viewport_height=720
        )

    @staticmethod
    def ultra_quality() -> RecordingConfig:
        """Ultra quality preset (4K, 60 FPS, 10 Mbps)."""
        return RecordingConfig(
            resolution="3840x2160",
            frame_rate=60,
            quality="ultra",
            video_format="mp4",
            video_codec="h264",
            viewport_width=3840,
            viewport_height=2160
        )
