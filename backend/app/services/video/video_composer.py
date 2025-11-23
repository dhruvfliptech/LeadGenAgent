"""
Video composer service for merging recordings with voiceovers.

Combines screen recordings and voiceover audio into final demo videos
with branding, overlays, transitions, and multiple quality versions.
"""

import asyncio
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.services.video.ffmpeg_wrapper import get_ffmpeg_wrapper, VideoMetadata

logger = logging.getLogger(__name__)


class TextOverlay(BaseModel):
    """Text overlay configuration."""
    text: str
    start_time_seconds: float
    end_time_seconds: float
    position: str = "bottom"  # top, center, bottom
    font_size: int = 48
    font_color: str = "#FFFFFF"
    background_color: Optional[str] = "rgba(0,0,0,0.7)"
    animation: str = "fade"  # fade, slide, none


class BrandingConfig(BaseModel):
    """Branding configuration."""
    logo_path: Optional[str] = None
    logo_position: str = "top-right"  # top-left, top-right, bottom-left, bottom-right, center
    logo_opacity: float = 0.8
    watermark_text: Optional[str] = None
    company_name: str
    primary_color: str = "#FF6600"


class IntroConfig(BaseModel):
    """Intro sequence configuration."""
    duration_seconds: int = 3
    template: str = "modern"  # modern, minimal, corporate
    company_name: str
    tagline: Optional[str] = None
    background_color: str = "#000000"


class OutroConfig(BaseModel):
    """Outro sequence configuration."""
    duration_seconds: int = 5
    template: str = "cta"  # cta, contact, simple
    call_to_action: str = "Schedule a demo today"
    contact_info: Dict[str, str] = Field(default_factory=dict)  # email, phone, website
    background_color: str = "#000000"


class CompositionConfig(BaseModel):
    """Video composition configuration."""
    output_format: str = "mp4"
    video_codec: str = "h264"
    audio_codec: str = "aac"
    video_bitrate: Optional[str] = None  # None = use CRF
    audio_bitrate: str = "192k"
    preset: str = "fast"  # ultrafast, fast, medium, slow
    crf: int = 23  # Constant Rate Factor (18-28, lower = better quality)
    resolution: Optional[str] = None  # Scale video if needed (e.g., "1920:1080")
    fps: Optional[int] = None  # Target frame rate


class CompositionResult(BaseModel):
    """Result of video composition."""
    video_path: str
    duration_seconds: float
    file_size_bytes: int
    resolution: str
    format: str
    versions: Dict[str, str] = Field(default_factory=dict)  # quality -> path mapping
    processing_time_seconds: float
    cost_estimate: float = 0.0
    thumbnail_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VideoComposer:
    """
    Service for composing final demo videos.

    Merges screen recordings and voiceovers, adds branding, overlays,
    intro/outro sequences, and generates multiple quality versions.
    """

    def __init__(self, storage_base_path: str = "/Users/greenmachine2.0/Craigslist/backend/storage"):
        """
        Initialize video composer.

        Args:
            storage_base_path: Base path for storage directories
        """
        self.storage_base = Path(storage_base_path)
        self.ffmpeg = get_ffmpeg_wrapper()

        # Ensure storage directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure all required storage directories exist."""
        directories = [
            self.storage_base / "recordings",
            self.storage_base / "voiceovers",
            self.storage_base / "composed_videos",
            self.storage_base / "thumbnails",
            self.storage_base / "temp",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    async def compose_video(
        self,
        screen_recording_path: str,
        voiceover_path: str,
        demo_site_id: int,
        composition_config: Optional[CompositionConfig] = None,
        branding: Optional[BrandingConfig] = None,
        text_overlays: Optional[List[TextOverlay]] = None,
        intro_config: Optional[IntroConfig] = None,
        outro_config: Optional[OutroConfig] = None,
        background_music_path: Optional[str] = None,
        background_music_volume: float = 0.15,
        generate_qualities: Optional[List[str]] = None
    ) -> CompositionResult:
        """
        Compose final demo video from recording and voiceover.

        Args:
            screen_recording_path: Path to screen recording
            voiceover_path: Path to voiceover audio
            demo_site_id: Demo site identifier
            composition_config: Composition settings
            branding: Branding configuration
            text_overlays: List of text overlays to add
            intro_config: Intro sequence configuration
            outro_config: Outro sequence configuration
            background_music_path: Path to background music
            background_music_volume: Music volume (0.0 to 1.0)
            generate_qualities: List of quality versions to generate (e.g., ["1080p", "720p"])

        Returns:
            CompositionResult with paths and metadata

        Raises:
            ValueError: If input files are invalid
            RuntimeError: If composition fails
        """
        start_time = time.time()

        try:
            # Validate inputs
            if not self.ffmpeg.validate_video(screen_recording_path):
                raise ValueError(f"Invalid screen recording: {screen_recording_path}")

            if not os.path.exists(voiceover_path):
                raise ValueError(f"Voiceover file not found: {voiceover_path}")

            # Use default config if not provided
            if composition_config is None:
                composition_config = CompositionConfig()

            # Create output directory
            output_dir = self.storage_base / "composed_videos" / str(demo_site_id)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"video_{timestamp}.{composition_config.output_format}"
            output_path = str(output_dir / output_filename)

            # Temporary file for intermediate steps
            temp_dir = self.storage_base / "temp"
            temp_files = []

            try:
                # Step 1: Merge audio and video
                logger.info("Step 1: Merging audio and video")
                merged_path = str(temp_dir / f"merged_{timestamp}.mp4")
                temp_files.append(merged_path)

                success = await self.ffmpeg.merge_audio_video(
                    video_path=screen_recording_path,
                    audio_path=voiceover_path,
                    output_path=merged_path,
                    video_codec=composition_config.video_codec,
                    audio_codec=composition_config.audio_codec,
                    audio_bitrate=composition_config.audio_bitrate,
                    shortest=True
                )

                if not success:
                    raise RuntimeError("Failed to merge audio and video")

                current_video = merged_path

                # Step 2: Add logo/watermark if branding provided
                if branding and branding.logo_path:
                    logger.info("Step 2: Adding logo/watermark")
                    branded_path = str(temp_dir / f"branded_{timestamp}.mp4")
                    temp_files.append(branded_path)

                    success = await self.ffmpeg.add_overlay(
                        video_path=current_video,
                        overlay_path=branding.logo_path,
                        output_path=branded_path,
                        position=branding.logo_position,
                        opacity=branding.logo_opacity
                    )

                    if not success:
                        logger.warning("Failed to add logo, continuing without it")
                    else:
                        current_video = branded_path

                # Step 3: Add text overlays
                if text_overlays:
                    logger.info(f"Step 3: Adding {len(text_overlays)} text overlays")
                    for i, overlay in enumerate(text_overlays):
                        overlaid_path = str(temp_dir / f"overlay_{i}_{timestamp}.mp4")
                        temp_files.append(overlaid_path)

                        # Convert hex color to FFmpeg format
                        font_color = overlay.font_color.replace("#", "0x")

                        success = await self.ffmpeg.add_text_overlay(
                            video_path=current_video,
                            output_path=overlaid_path,
                            text=overlay.text,
                            start_time=overlay.start_time_seconds,
                            end_time=overlay.end_time_seconds,
                            position=overlay.position,
                            font_size=overlay.font_size,
                            font_color=font_color,
                            background_color=overlay.background_color
                        )

                        if not success:
                            logger.warning(f"Failed to add text overlay {i}, continuing")
                        else:
                            current_video = overlaid_path

                # Step 4: Add background music if provided
                if background_music_path and os.path.exists(background_music_path):
                    logger.info("Step 4: Adding background music")
                    music_path = str(temp_dir / f"music_{timestamp}.mp4")
                    temp_files.append(music_path)

                    success = await self.ffmpeg.add_background_music(
                        video_path=current_video,
                        music_path=background_music_path,
                        output_path=music_path,
                        music_volume=background_music_volume
                    )

                    if not success:
                        logger.warning("Failed to add background music, continuing without it")
                    else:
                        current_video = music_path

                # Step 5: Add intro/outro sequences (if provided)
                if intro_config or outro_config:
                    logger.info("Step 5: Adding intro/outro sequences")
                    video_with_sequences = await self.add_intro_outro(
                        video_path=current_video,
                        intro_config=intro_config,
                        outro_config=outro_config
                    )
                    if video_with_sequences:
                        temp_files.append(video_with_sequences)
                        current_video = video_with_sequences

                # Step 6: Final encoding with target settings
                logger.info("Step 6: Final encoding")
                success = await self.ffmpeg.encode_video(
                    input_path=current_video,
                    output_path=output_path,
                    resolution=composition_config.resolution,
                    video_codec=composition_config.video_codec,
                    audio_codec=composition_config.audio_codec,
                    video_bitrate=composition_config.video_bitrate,
                    audio_bitrate=composition_config.audio_bitrate,
                    crf=composition_config.crf,
                    preset=composition_config.preset,
                    fps=composition_config.fps
                )

                if not success:
                    raise RuntimeError("Failed to encode final video")

                # Step 7: Generate quality versions
                versions = {}
                if generate_qualities:
                    logger.info(f"Step 7: Generating {len(generate_qualities)} quality versions")
                    versions = await self.encode_for_web(
                        video_path=output_path,
                        qualities=generate_qualities,
                        demo_site_id=demo_site_id
                    )

                # Step 8: Extract thumbnail
                logger.info("Step 8: Extracting thumbnail")
                thumbnail_path = await self.extract_thumbnail(output_path, demo_site_id)

                # Get final video metadata
                metadata = await self.ffmpeg.get_video_metadata(output_path)
                file_size = os.path.getsize(output_path)

                # Calculate processing time and cost
                processing_time = time.time() - start_time
                cost_estimate = self._estimate_cost(processing_time, file_size)

                # Build result
                result = CompositionResult(
                    video_path=output_path,
                    duration_seconds=metadata.duration,
                    file_size_bytes=file_size,
                    resolution=f"{metadata.width}x{metadata.height}",
                    format=composition_config.output_format,
                    versions=versions,
                    processing_time_seconds=processing_time,
                    cost_estimate=cost_estimate,
                    thumbnail_path=thumbnail_path,
                    metadata={
                        'fps': metadata.fps,
                        'video_codec': metadata.codec,
                        'audio_codec': metadata.audio_codec,
                        'bitrate': metadata.bitrate
                    }
                )

                logger.info(f"Video composition completed in {processing_time:.2f}s")
                return result

            finally:
                # Clean up temporary files
                await self._cleanup_temp_files(temp_files)

        except Exception as e:
            logger.error(f"Error composing video: {e}")
            raise

    async def add_intro_outro(
        self,
        video_path: str,
        intro_config: Optional[IntroConfig] = None,
        outro_config: Optional[OutroConfig] = None
    ) -> Optional[str]:
        """
        Add intro and/or outro sequences to video.

        Args:
            video_path: Path to video file
            intro_config: Intro configuration
            outro_config: Outro configuration

        Returns:
            Path to video with intro/outro, or None if failed
        """
        try:
            videos_to_concat = []
            temp_files = []

            # Generate intro if configured
            if intro_config:
                intro_path = await self._generate_intro(intro_config)
                if intro_path:
                    videos_to_concat.append(intro_path)
                    temp_files.append(intro_path)

            # Add main video
            videos_to_concat.append(video_path)

            # Generate outro if configured
            if outro_config:
                outro_path = await self._generate_outro(outro_config)
                if outro_path:
                    videos_to_concat.append(outro_path)
                    temp_files.append(outro_path)

            # If no intro/outro, return original
            if len(videos_to_concat) == 1:
                return None

            # Concatenate videos
            temp_dir = self.storage_base / "temp"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(temp_dir / f"with_sequences_{timestamp}.mp4")

            success = await self.ffmpeg.concat_videos(
                video_paths=videos_to_concat,
                output_path=output_path
            )

            if not success:
                logger.error("Failed to concatenate intro/outro")
                return None

            return output_path

        except Exception as e:
            logger.error(f"Error adding intro/outro: {e}")
            return None

    async def add_text_overlays(
        self,
        video_path: str,
        overlays: List[TextOverlay]
    ) -> str:
        """
        Add multiple text overlays to video.

        Args:
            video_path: Path to video file
            overlays: List of text overlays

        Returns:
            Path to video with overlays
        """
        try:
            current_video = video_path
            temp_dir = self.storage_base / "temp"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            for i, overlay in enumerate(overlays):
                output_path = str(temp_dir / f"overlay_{i}_{timestamp}.mp4")

                success = await self.ffmpeg.add_text_overlay(
                    video_path=current_video,
                    output_path=output_path,
                    text=overlay.text,
                    start_time=overlay.start_time_seconds,
                    end_time=overlay.end_time_seconds,
                    position=overlay.position,
                    font_size=overlay.font_size,
                    font_color=overlay.font_color,
                    background_color=overlay.background_color
                )

                if success:
                    current_video = output_path

            return current_video

        except Exception as e:
            logger.error(f"Error adding text overlays: {e}")
            return video_path

    async def add_background_music(
        self,
        video_path: str,
        music_path: str,
        volume: float = 0.15
    ) -> str:
        """
        Add background music to video.

        Args:
            video_path: Path to video file
            music_path: Path to music file
            volume: Music volume (0.0 to 1.0)

        Returns:
            Path to video with background music
        """
        try:
            temp_dir = self.storage_base / "temp"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(temp_dir / f"with_music_{timestamp}.mp4")

            success = await self.ffmpeg.add_background_music(
                video_path=video_path,
                music_path=music_path,
                output_path=output_path,
                music_volume=volume
            )

            if success:
                return output_path
            else:
                return video_path

        except Exception as e:
            logger.error(f"Error adding background music: {e}")
            return video_path

    async def encode_for_web(
        self,
        video_path: str,
        qualities: List[str],
        demo_site_id: int
    ) -> Dict[str, str]:
        """
        Generate multiple quality versions for web playback.

        Args:
            video_path: Path to source video
            qualities: List of quality versions to generate (e.g., ["1080p", "720p", "480p"])
            demo_site_id: Demo site identifier

        Returns:
            Dictionary mapping quality to file path
        """
        quality_settings = {
            "2160p": {"resolution": "3840:2160", "bitrate": "12M", "suffix": "_2160p"},
            "1080p": {"resolution": "1920:1080", "bitrate": "5M", "suffix": "_1080p"},
            "720p": {"resolution": "1280:720", "bitrate": "3M", "suffix": "_720p"},
            "480p": {"resolution": "854:480", "bitrate": "1.5M", "suffix": "_480p"},
            "360p": {"resolution": "640:360", "bitrate": "800k", "suffix": "_360p"},
        }

        versions = {}
        output_dir = self.storage_base / "composed_videos" / str(demo_site_id)

        # Generate each quality version in parallel
        tasks = []
        for quality in qualities:
            if quality in quality_settings:
                tasks.append(self._encode_quality(
                    video_path, quality, quality_settings[quality], output_dir
                ))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect successful results
        for quality, result in zip(qualities, results):
            if isinstance(result, str):
                versions[quality] = result
            else:
                logger.warning(f"Failed to generate {quality} version: {result}")

        return versions

    async def _encode_quality(
        self,
        video_path: str,
        quality: str,
        settings: Dict[str, str],
        output_dir: Path
    ) -> str:
        """Encode a specific quality version."""
        try:
            # Generate output filename
            video_name = Path(video_path).stem
            output_filename = f"{video_name}{settings['suffix']}.mp4"
            output_path = str(output_dir / output_filename)

            success = await self.ffmpeg.encode_video(
                input_path=video_path,
                output_path=output_path,
                resolution=settings["resolution"],
                video_bitrate=settings["bitrate"],
                preset="fast",
                crf=23
            )

            if success:
                logger.info(f"Generated {quality} version: {output_path}")
                return output_path
            else:
                raise RuntimeError(f"Failed to encode {quality}")

        except Exception as e:
            logger.error(f"Error encoding {quality}: {e}")
            raise

    async def extract_thumbnail(
        self,
        video_path: str,
        demo_site_id: int,
        timestamp_seconds: float = 5.0
    ) -> Optional[str]:
        """
        Extract thumbnail from video.

        Args:
            video_path: Path to video file
            demo_site_id: Demo site identifier
            timestamp_seconds: Timestamp for thumbnail

        Returns:
            Path to thumbnail image or None if failed
        """
        try:
            output_dir = self.storage_base / "thumbnails" / str(demo_site_id)
            output_dir.mkdir(parents=True, exist_ok=True)

            video_name = Path(video_path).stem
            output_path = str(output_dir / f"{video_name}_thumb.jpg")

            success = await self.ffmpeg.extract_thumbnail(
                video_path=video_path,
                timestamp_seconds=timestamp_seconds,
                output_path=output_path,
                width=640
            )

            if success:
                return output_path
            else:
                return None

        except Exception as e:
            logger.error(f"Error extracting thumbnail: {e}")
            return None

    def get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        Get video metadata.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with video metadata
        """
        try:
            # This is synchronous, so we need to use asyncio.run or create_task
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, create a task
                task = loop.create_task(self.ffmpeg.get_video_metadata(video_path))
                # Note: This won't work in sync context, caller should use async version
                raise RuntimeError("get_video_metadata should be called from async context")
            else:
                metadata = loop.run_until_complete(self.ffmpeg.get_video_metadata(video_path))
                return {
                    'duration': metadata.duration,
                    'width': metadata.width,
                    'height': metadata.height,
                    'fps': metadata.fps,
                    'bitrate': metadata.bitrate,
                    'codec': metadata.codec,
                    'audio_codec': metadata.audio_codec,
                    'file_size': metadata.file_size
                }
        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")
            return {}

    async def _generate_intro(self, intro_config: IntroConfig) -> Optional[str]:
        """
        Generate intro sequence.

        Args:
            intro_config: Intro configuration

        Returns:
            Path to intro video or None if failed
        """
        # This is a placeholder - actual implementation would use intro templates
        # or generate intro dynamically using FFmpeg filters
        logger.warning("Intro generation not yet implemented")
        return None

    async def _generate_outro(self, outro_config: OutroConfig) -> Optional[str]:
        """
        Generate outro sequence.

        Args:
            outro_config: Outro configuration

        Returns:
            Path to outro video or None if failed
        """
        # This is a placeholder - actual implementation would use outro templates
        # or generate outro dynamically using FFmpeg filters
        logger.warning("Outro generation not yet implemented")
        return None

    def _estimate_cost(self, processing_time_seconds: float, file_size_bytes: int) -> float:
        """
        Estimate processing cost.

        Args:
            processing_time_seconds: Processing time in seconds
            file_size_bytes: Output file size in bytes

        Returns:
            Estimated cost in USD
        """
        # Simple cost model: $0.01 per minute of processing time
        cost_per_second = 0.01 / 60
        return processing_time_seconds * cost_per_second

    async def _cleanup_temp_files(self, temp_files: List[str]) -> None:
        """
        Clean up temporary files.

        Args:
            temp_files: List of temporary file paths
        """
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    logger.debug(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {temp_file}: {e}")


# Singleton instance
_video_composer: Optional[VideoComposer] = None


def get_video_composer() -> VideoComposer:
    """Get or create video composer singleton."""
    global _video_composer
    if _video_composer is None:
        _video_composer = VideoComposer()
    return _video_composer
