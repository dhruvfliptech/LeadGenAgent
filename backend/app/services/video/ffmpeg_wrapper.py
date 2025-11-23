"""
FFmpeg wrapper for video processing operations.

Provides a clean Python interface to FFmpeg commands with async support,
progress tracking, error handling, and validation.
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FFmpegProgress:
    """Progress information for FFmpeg operations."""
    process_id: str
    progress: float  # 0.0 to 1.0
    current_frame: int = 0
    total_frames: int = 0
    current_time: float = 0.0
    total_time: float = 0.0
    speed: str = "0x"
    bitrate: str = "0kbits/s"
    fps: float = 0.0
    started_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'process_id': self.process_id,
            'progress': self.progress,
            'current_frame': self.current_frame,
            'total_frames': self.total_frames,
            'current_time': self.current_time,
            'total_time': self.total_time,
            'speed': self.speed,
            'bitrate': self.bitrate,
            'fps': self.fps,
            'started_at': self.started_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class VideoMetadata:
    """Video file metadata."""
    duration: float
    width: int
    height: int
    fps: float
    bitrate: int
    codec: str
    audio_codec: Optional[str] = None
    audio_sample_rate: Optional[int] = None
    audio_channels: Optional[int] = None
    file_size: int = 0
    format: str = ""


class FFmpegWrapper:
    """
    Python wrapper around FFmpeg for video processing operations.

    Provides async support, progress tracking, error handling, and
    validation for common video operations.
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        """
        Initialize FFmpeg wrapper.

        Args:
            ffmpeg_path: Path to ffmpeg binary
            ffprobe_path: Path to ffprobe binary
        """
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self._progress_store: Dict[str, FFmpegProgress] = {}
        self._validate_installation()

    def _validate_installation(self) -> None:
        """Validate that FFmpeg and FFprobe are installed."""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"FFmpeg version: {result.stdout.splitlines()[0]}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"FFmpeg not found or invalid: {e}")
            raise RuntimeError(
                "FFmpeg is not installed or not in PATH. "
                "Install it with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)"
            )

        try:
            subprocess.run(
                [self.ffprobe_path, "-version"],
                capture_output=True,
                text=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"FFprobe not found or invalid: {e}")
            raise RuntimeError("FFprobe is not installed or not in PATH.")

    async def merge_audio_video(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        video_codec: str = "copy",
        audio_codec: str = "aac",
        audio_bitrate: str = "192k",
        shortest: bool = True
    ) -> bool:
        """
        Merge audio and video files.

        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            output_path: Path for output file
            video_codec: Video codec (copy, h264, etc.)
            audio_codec: Audio codec
            audio_bitrate: Audio bitrate
            shortest: End output at shortest input duration

        Returns:
            True if successful, False otherwise
        """
        process_id = str(uuid.uuid4())

        try:
            # Build command
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-i", audio_path,
                "-c:v", video_codec,
                "-c:a", audio_codec,
                "-b:a", audio_bitrate,
            ]

            if shortest:
                cmd.append("-shortest")

            cmd.extend([
                "-y",  # Overwrite output file
                output_path
            ])

            logger.info(f"Merging audio/video: {' '.join(cmd)}")

            # Execute command
            success = await self._run_ffmpeg_command(cmd, process_id)

            if success:
                logger.info(f"Successfully merged audio and video to: {output_path}")
            else:
                logger.error(f"Failed to merge audio and video")

            return success

        except Exception as e:
            logger.error(f"Error merging audio/video: {e}")
            return False

    async def add_overlay(
        self,
        video_path: str,
        overlay_path: str,
        output_path: str,
        position: str = "top-right",
        opacity: float = 0.8,
        scale: Optional[int] = 120
    ) -> bool:
        """
        Add image overlay (logo/watermark) to video.

        Args:
            video_path: Path to video file
            overlay_path: Path to overlay image
            output_path: Path for output file
            position: Position (top-left, top-right, bottom-left, bottom-right, center)
            opacity: Overlay opacity (0.0 to 1.0)
            scale: Scale overlay to width (pixels), maintains aspect ratio

        Returns:
            True if successful, False otherwise
        """
        process_id = str(uuid.uuid4())

        try:
            # Position mapping
            position_map = {
                "top-left": "10:10",
                "top-right": "W-w-10:10",
                "bottom-left": "10:H-h-10",
                "bottom-right": "W-w-10:H-h-10",
                "center": "(W-w)/2:(H-h)/2"
            }

            pos = position_map.get(position, "W-w-10:10")

            # Build filter complex
            filter_parts = []

            # Scale overlay if needed
            if scale:
                filter_parts.append(f"[1:v]scale={scale}:-1[logo]")
                overlay_input = "[logo]"
            else:
                overlay_input = "[1:v]"

            # Add overlay with opacity
            if opacity < 1.0:
                if filter_parts:
                    filter_parts.append(f"{overlay_input}format=rgba,colorchannelmixer=aa={opacity}[logo_opacity]")
                    overlay_input = "[logo_opacity]"
                else:
                    filter_parts.append(f"[1:v]format=rgba,colorchannelmixer=aa={opacity}[logo_opacity]")
                    overlay_input = "[logo_opacity]"

            # Add overlay to video
            filter_parts.append(f"[0:v]{overlay_input}overlay={pos}:format=auto")

            filter_complex = ";".join(filter_parts)

            # Build command
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-i", overlay_path,
                "-filter_complex", filter_complex,
                "-c:a", "copy",
                "-y",
                output_path
            ]

            logger.info(f"Adding overlay: {' '.join(cmd)}")

            # Execute command
            success = await self._run_ffmpeg_command(cmd, process_id)

            if success:
                logger.info(f"Successfully added overlay to: {output_path}")
            else:
                logger.error(f"Failed to add overlay")

            return success

        except Exception as e:
            logger.error(f"Error adding overlay: {e}")
            return False

    async def add_text_overlay(
        self,
        video_path: str,
        output_path: str,
        text: str,
        start_time: float,
        end_time: float,
        position: str = "bottom",
        font_size: int = 48,
        font_color: str = "white",
        background_color: Optional[str] = "black@0.7",
        font_file: Optional[str] = None
    ) -> bool:
        """
        Add text overlay to video.

        Args:
            video_path: Path to video file
            output_path: Path for output file
            text: Text to display
            start_time: Start time in seconds
            end_time: End time in seconds
            position: Position (top, center, bottom)
            font_size: Font size in pixels
            font_color: Font color
            background_color: Background color (None for transparent)
            font_file: Path to custom font file

        Returns:
            True if successful, False otherwise
        """
        process_id = str(uuid.uuid4())

        try:
            # Position mapping
            position_map = {
                "top": "y=50",
                "center": "y=(h-text_h)/2",
                "bottom": "y=h-text_h-50"
            }

            y_pos = position_map.get(position, "y=h-text_h-50")

            # Escape text for FFmpeg
            text_escaped = text.replace(":", r"\:")
            text_escaped = text_escaped.replace("'", r"\'")

            # Build drawtext filter
            drawtext_parts = [
                f"text='{text_escaped}'",
                f"fontsize={font_size}",
                f"fontcolor={font_color}",
                "x=(w-text_w)/2",
                y_pos,
                f"enable='between(t,{start_time},{end_time})'"
            ]

            if font_file:
                drawtext_parts.insert(0, f"fontfile={font_file}")

            if background_color:
                drawtext_parts.append(f"box=1")
                drawtext_parts.append(f"boxcolor={background_color}")
                drawtext_parts.append(f"boxborderw=10")

            drawtext_filter = "drawtext=" + ":".join(drawtext_parts)

            # Build command
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-vf", drawtext_filter,
                "-c:a", "copy",
                "-y",
                output_path
            ]

            logger.info(f"Adding text overlay: {text}")

            # Execute command
            success = await self._run_ffmpeg_command(cmd, process_id)

            if success:
                logger.info(f"Successfully added text overlay to: {output_path}")
            else:
                logger.error(f"Failed to add text overlay")

            return success

        except Exception as e:
            logger.error(f"Error adding text overlay: {e}")
            return False

    async def concat_videos(
        self,
        video_paths: List[str],
        output_path: str,
        safe: bool = False
    ) -> bool:
        """
        Concatenate multiple videos.

        Args:
            video_paths: List of video file paths
            output_path: Path for output file
            safe: Use safe mode (for paths with special characters)

        Returns:
            True if successful, False otherwise
        """
        process_id = str(uuid.uuid4())

        try:
            # Create temporary file list
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for video_path in video_paths:
                    f.write(f"file '{video_path}'\n")
                filelist_path = f.name

            try:
                # Build command
                cmd = [
                    self.ffmpeg_path,
                    "-f", "concat",
                    "-safe", "1" if safe else "0",
                    "-i", filelist_path,
                    "-c", "copy",
                    "-y",
                    output_path
                ]

                logger.info(f"Concatenating {len(video_paths)} videos")

                # Execute command
                success = await self._run_ffmpeg_command(cmd, process_id)

                if success:
                    logger.info(f"Successfully concatenated videos to: {output_path}")
                else:
                    logger.error(f"Failed to concatenate videos")

                return success

            finally:
                # Clean up temporary file
                os.unlink(filelist_path)

        except Exception as e:
            logger.error(f"Error concatenating videos: {e}")
            return False

    async def encode_video(
        self,
        input_path: str,
        output_path: str,
        resolution: Optional[str] = None,
        video_codec: str = "h264",
        audio_codec: str = "aac",
        video_bitrate: Optional[str] = None,
        audio_bitrate: str = "192k",
        crf: int = 23,
        preset: str = "fast",
        fps: Optional[int] = None
    ) -> bool:
        """
        Encode video with specified settings.

        Args:
            input_path: Path to input video
            output_path: Path for output file
            resolution: Target resolution (e.g., "1920:1080", "1280:720")
            video_codec: Video codec
            audio_codec: Audio codec
            video_bitrate: Video bitrate (e.g., "5M")
            audio_bitrate: Audio bitrate
            crf: Constant Rate Factor (18-28, lower is better quality)
            preset: Encoding preset (ultrafast, fast, medium, slow)
            fps: Target frame rate

        Returns:
            True if successful, False otherwise
        """
        process_id = str(uuid.uuid4())

        try:
            # Build command
            cmd = [self.ffmpeg_path, "-i", input_path]

            # Video filters
            filters = []
            if resolution:
                filters.append(f"scale={resolution}")
            if fps:
                filters.append(f"fps={fps}")

            if filters:
                cmd.extend(["-vf", ",".join(filters)])

            # Video encoding
            cmd.extend(["-c:v", video_codec])

            if video_bitrate:
                cmd.extend(["-b:v", video_bitrate])
            else:
                cmd.extend(["-crf", str(crf)])

            cmd.extend(["-preset", preset])

            # Audio encoding
            cmd.extend(["-c:a", audio_codec, "-b:a", audio_bitrate])

            # Output
            cmd.extend(["-y", output_path])

            logger.info(f"Encoding video: {resolution or 'original'} resolution")

            # Execute command
            success = await self._run_ffmpeg_command(cmd, process_id)

            if success:
                logger.info(f"Successfully encoded video to: {output_path}")
            else:
                logger.error(f"Failed to encode video")

            return success

        except Exception as e:
            logger.error(f"Error encoding video: {e}")
            return False

    async def extract_thumbnail(
        self,
        video_path: str,
        timestamp_seconds: float,
        output_path: str,
        width: int = 640
    ) -> bool:
        """
        Extract thumbnail from video at specific timestamp.

        Args:
            video_path: Path to video file
            timestamp_seconds: Timestamp in seconds
            output_path: Path for output image
            width: Thumbnail width (maintains aspect ratio)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build command
            cmd = [
                self.ffmpeg_path,
                "-ss", str(timestamp_seconds),
                "-i", video_path,
                "-vf", f"scale={width}:-1",
                "-vframes", "1",
                "-y",
                output_path
            ]

            logger.info(f"Extracting thumbnail at {timestamp_seconds}s")

            # Execute command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            _, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"Successfully extracted thumbnail to: {output_path}")
                return True
            else:
                logger.error(f"Failed to extract thumbnail: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error extracting thumbnail: {e}")
            return False

    async def add_background_music(
        self,
        video_path: str,
        music_path: str,
        output_path: str,
        music_volume: float = 0.15,
        fade_in: float = 2.0,
        fade_out: float = 2.0
    ) -> bool:
        """
        Add background music to video.

        Args:
            video_path: Path to video file
            music_path: Path to music file
            output_path: Path for output file
            music_volume: Music volume (0.0 to 1.0)
            fade_in: Fade in duration in seconds
            fade_out: Fade out duration in seconds

        Returns:
            True if successful, False otherwise
        """
        process_id = str(uuid.uuid4())

        try:
            # Get video duration to fade out music properly
            metadata = await self.get_video_metadata(video_path)
            duration = metadata.duration

            # Build filter complex for audio mixing
            filter_complex = (
                f"[1:a]volume={music_volume},"
                f"afade=t=in:st=0:d={fade_in},"
                f"afade=t=out:st={duration - fade_out}:d={fade_out}[music];"
                f"[0:a][music]amix=inputs=2:duration=shortest[aout]"
            )

            # Build command
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-i", music_path,
                "-filter_complex", filter_complex,
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                "-y",
                output_path
            ]

            logger.info(f"Adding background music: volume={music_volume}")

            # Execute command
            success = await self._run_ffmpeg_command(cmd, process_id)

            if success:
                logger.info(f"Successfully added background music to: {output_path}")
            else:
                logger.error(f"Failed to add background music")

            return success

        except Exception as e:
            logger.error(f"Error adding background music: {e}")
            return False

    async def get_video_metadata(self, video_path: str) -> VideoMetadata:
        """
        Get video metadata using ffprobe.

        Args:
            video_path: Path to video file

        Returns:
            VideoMetadata object
        """
        try:
            # Run ffprobe
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise RuntimeError(f"ffprobe failed: {stderr.decode()}")

            # Parse JSON output
            data = json.loads(stdout.decode())

            # Extract video stream
            video_stream = next(
                (s for s in data.get("streams", []) if s["codec_type"] == "video"),
                None
            )

            if not video_stream:
                raise ValueError("No video stream found")

            # Extract audio stream
            audio_stream = next(
                (s for s in data.get("streams", []) if s["codec_type"] == "audio"),
                None
            )

            # Get format info
            format_info = data.get("format", {})

            # Parse FPS
            fps_str = video_stream.get("r_frame_rate", "30/1")
            fps_parts = fps_str.split("/")
            fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0

            # Build metadata object
            metadata = VideoMetadata(
                duration=float(format_info.get("duration", 0)),
                width=int(video_stream.get("width", 0)),
                height=int(video_stream.get("height", 0)),
                fps=fps,
                bitrate=int(format_info.get("bit_rate", 0)),
                codec=video_stream.get("codec_name", "unknown"),
                audio_codec=audio_stream.get("codec_name") if audio_stream else None,
                audio_sample_rate=int(audio_stream.get("sample_rate", 0)) if audio_stream else None,
                audio_channels=int(audio_stream.get("channels", 0)) if audio_stream else None,
                file_size=int(format_info.get("size", 0)),
                format=format_info.get("format_name", "")
            )

            return metadata

        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")
            raise

    def validate_video(self, video_path: str) -> bool:
        """
        Validate that a video file is valid and playable.

        Args:
            video_path: Path to video file

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check file exists
            if not os.path.exists(video_path):
                logger.error(f"Video file does not exist: {video_path}")
                return False

            # Check file size
            file_size = os.path.getsize(video_path)
            if file_size == 0:
                logger.error(f"Video file is empty: {video_path}")
                return False

            # Try to read metadata
            cmd = [
                self.ffprobe_path,
                "-v", "error",
                "-show_entries", "stream=codec_type",
                "-of", "default=noprint_wrappers=1",
                video_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                logger.error(f"Video validation failed: {result.stderr}")
                return False

            # Check for video stream
            if "codec_type=video" not in result.stdout:
                logger.error(f"No video stream found in file: {video_path}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating video: {e}")
            return False

    def get_progress(self, process_id: str) -> Optional[FFmpegProgress]:
        """
        Get progress information for a running process.

        Args:
            process_id: Process identifier

        Returns:
            FFmpegProgress object or None if not found
        """
        return self._progress_store.get(process_id)

    async def _run_ffmpeg_command(self, cmd: List[str], process_id: str) -> bool:
        """
        Run FFmpeg command asynchronously with progress tracking.

        Args:
            cmd: Command to execute
            process_id: Process identifier for tracking

        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize progress
            progress = FFmpegProgress(process_id=process_id, progress=0.0)
            self._progress_store[process_id] = progress

            # Execute command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Read stderr for progress updates
            stderr_lines = []
            while True:
                line = await process.stderr.readline()
                if not line:
                    break

                line_str = line.decode().strip()
                stderr_lines.append(line_str)

                # Parse progress from FFmpeg output
                self._parse_progress(line_str, progress)

            # Wait for process to complete
            await process.wait()

            # Update final progress
            progress.progress = 1.0 if process.returncode == 0 else 0.0
            progress.updated_at = datetime.now()

            if process.returncode != 0:
                logger.error(f"FFmpeg command failed with code {process.returncode}")
                logger.error(f"Command: {' '.join(cmd)}")
                logger.error(f"Output: {chr(10).join(stderr_lines[-20:])}")  # Last 20 lines
                return False

            return True

        except Exception as e:
            logger.error(f"Error running FFmpeg command: {e}")
            return False
        finally:
            # Clean up progress after some time
            await asyncio.sleep(300)  # Keep for 5 minutes
            self._progress_store.pop(process_id, None)

    def _parse_progress(self, line: str, progress: FFmpegProgress) -> None:
        """
        Parse progress information from FFmpeg output line.

        Args:
            line: Output line from FFmpeg
            progress: Progress object to update
        """
        try:
            # Extract frame
            frame_match = re.search(r"frame=\s*(\d+)", line)
            if frame_match:
                progress.current_frame = int(frame_match.group(1))

            # Extract time
            time_match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
            if time_match:
                hours = int(time_match.group(1))
                minutes = int(time_match.group(2))
                seconds = float(time_match.group(3))
                progress.current_time = hours * 3600 + minutes * 60 + seconds

            # Extract speed
            speed_match = re.search(r"speed=\s*(\S+)", line)
            if speed_match:
                progress.speed = speed_match.group(1)

            # Extract bitrate
            bitrate_match = re.search(r"bitrate=\s*(\S+)", line)
            if bitrate_match:
                progress.bitrate = bitrate_match.group(1)

            # Extract fps
            fps_match = re.search(r"fps=\s*(\d+\.?\d*)", line)
            if fps_match:
                progress.fps = float(fps_match.group(1))

            # Calculate progress if we know total time
            if progress.total_time > 0 and progress.current_time > 0:
                progress.progress = min(progress.current_time / progress.total_time, 1.0)

            progress.updated_at = datetime.now()

        except Exception as e:
            # Ignore parsing errors, they're not critical
            pass


# Singleton instance
_ffmpeg_wrapper: Optional[FFmpegWrapper] = None


def get_ffmpeg_wrapper() -> FFmpegWrapper:
    """Get or create FFmpeg wrapper singleton."""
    global _ffmpeg_wrapper
    if _ffmpeg_wrapper is None:
        _ffmpeg_wrapper = FFmpegWrapper()
    return _ffmpeg_wrapper
