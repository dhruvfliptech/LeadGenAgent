"""
ComposedVideo model for tracking final composed demo videos.

This model stores information about videos composed from screen recordings
and voiceovers, including multiple quality versions, branding, and metadata.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base
import enum


class CompositionStatus(str, enum.Enum):
    """Video composition status values."""
    PENDING = "pending"
    COMPOSING = "composing"
    ENCODING = "encoding"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoQuality(str, enum.Enum):
    """Video quality presets."""
    ULTRA_HD = "2160p"  # 4K
    FULL_HD = "1080p"
    HD = "720p"
    SD = "480p"
    LOW = "360p"


class ComposedVideo(Base):
    """
    ComposedVideo model for tracking final composed demo videos.

    Stores information about videos that have been composed from screen recordings
    and voiceovers, including multiple quality versions, branding, overlays, and
    comprehensive metadata about the composition process.
    """

    __tablename__ = "composed_videos"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys - linking to related entities
    demo_site_id = Column(Integer, ForeignKey("demo_sites.id"), nullable=False, index=True)
    demo_site = relationship("DemoSite", backref="composed_videos")

    # Note: These would link to screen_recordings and voiceovers tables when they exist
    screen_recording_id = Column(Integer, nullable=True, index=True)  # FK when recordings table exists
    voiceover_id = Column(Integer, nullable=True, index=True)  # FK when voiceovers table exists
    video_script_id = Column(Integer, nullable=True, index=True)  # FK when scripts table exists

    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    lead = relationship("Lead", backref="composed_videos")

    # File paths - primary video and quality versions
    video_file_path = Column(Text, nullable=False)  # Primary/highest quality version
    video_versions = Column(JSON, nullable=True)  # {quality: path} mapping for all versions

    # Individual quality version paths (for easy access)
    quality_2160p_path = Column(Text, nullable=True)  # 4K
    quality_1080p_path = Column(Text, nullable=True)  # Full HD
    quality_720p_path = Column(Text, nullable=True)   # HD
    quality_480p_path = Column(Text, nullable=True)   # SD
    quality_360p_path = Column(Text, nullable=True)   # Low

    # Thumbnail
    thumbnail_path = Column(Text, nullable=True)
    thumbnail_timestamp = Column(Float, default=5.0)  # Timestamp used for thumbnail

    # Video metadata
    duration_seconds = Column(Float, nullable=False)
    resolution = Column(String(20), nullable=False)  # e.g., "1920x1080"
    format = Column(String(20), default="mp4", nullable=False)
    fps = Column(Integer, default=30)  # Frames per second

    # File sizes (in bytes)
    file_size_bytes = Column(Integer, nullable=False)
    total_size_all_versions = Column(Integer, nullable=True)  # Sum of all quality versions

    # Audio metadata
    audio_codec = Column(String(20), default="aac")
    audio_bitrate = Column(String(20), default="192k")
    audio_sample_rate = Column(Integer, default=44100)

    # Video metadata
    video_codec = Column(String(20), default="h264")
    video_bitrate = Column(String(20), nullable=True)
    crf = Column(Integer, nullable=True)  # Constant Rate Factor used

    # Processing status
    status = Column(String(50), default="pending", nullable=False, index=True)
    # Status values: pending, composing, encoding, completed, failed

    processing_time_seconds = Column(Float, nullable=True)
    encoding_time_seconds = Column(Float, nullable=True)
    total_processing_time = Column(Float, nullable=True)

    # Composition configuration
    composition_config = Column(JSON, nullable=True)  # Full CompositionConfig as JSON

    # Branding and overlays
    branding_applied = Column(Boolean, default=False, nullable=False)
    logo_used = Column(String(255), nullable=True)  # Path to logo file used
    logo_position = Column(String(50), nullable=True)  # Position where logo was placed
    watermark_text = Column(String(255), nullable=True)

    overlays_count = Column(Integer, default=0, nullable=False)
    overlays_data = Column(JSON, nullable=True)  # Array of overlay configurations

    # Intro/Outro
    has_intro = Column(Boolean, default=False, nullable=False)
    intro_duration = Column(Float, nullable=True)
    intro_config = Column(JSON, nullable=True)

    has_outro = Column(Boolean, default=False, nullable=False)
    outro_duration = Column(Float, nullable=True)
    outro_config = Column(JSON, nullable=True)

    # Background music
    has_background_music = Column(Boolean, default=False, nullable=False)
    background_music_path = Column(Text, nullable=True)
    background_music_volume = Column(Float, nullable=True)

    # Quality and optimization
    web_optimized = Column(Boolean, default=True, nullable=False)
    preset = Column(String(50), default="fast")  # FFmpeg preset used

    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)  # Detailed error information
    retry_count = Column(Integer, default=0, nullable=False)
    last_retry_at = Column(DateTime(timezone=True), nullable=True)

    # Cost tracking
    cost_estimate = Column(Float, default=0.0, nullable=False)  # Processing cost estimate
    cpu_time_seconds = Column(Float, nullable=True)
    memory_peak_mb = Column(Float, nullable=True)

    # Analytics
    download_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)

    # Version tracking
    version = Column(Integer, default=1, nullable=False)
    parent_video_id = Column(Integer, ForeignKey("composed_videos.id"), nullable=True)  # Recomposed from

    # Source file tracking
    source_recording_path = Column(Text, nullable=True)
    source_voiceover_path = Column(Text, nullable=True)
    source_files_validated = Column(Boolean, default=False)

    # FFmpeg details
    ffmpeg_command = Column(Text, nullable=True)  # Command used for composition
    ffmpeg_version = Column(String(100), nullable=True)
    ffmpeg_output = Column(Text, nullable=True)  # FFmpeg output/logs

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)  # When composition started
    completed_at = Column(DateTime(timezone=True), nullable=True, index=True)  # When composition completed
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Soft delete

    # Flags
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    is_public = Column(Boolean, default=False, nullable=False)  # Public sharing enabled

    def __repr__(self):
        return f"<ComposedVideo(id={self.id}, demo_site_id={self.demo_site_id}, status='{self.status}', duration={self.duration_seconds}s)>"

    def to_dict(self):
        """Convert composed video to dictionary for API responses."""
        return {
            'id': self.id,
            'demo_site_id': self.demo_site_id,
            'lead_id': self.lead_id,
            'screen_recording_id': self.screen_recording_id,
            'voiceover_id': self.voiceover_id,
            'video_script_id': self.video_script_id,
            'files': {
                'video_file_path': self.video_file_path,
                'thumbnail_path': self.thumbnail_path,
                'video_versions': self.video_versions or {},
                'quality_versions': {
                    '2160p': self.quality_2160p_path,
                    '1080p': self.quality_1080p_path,
                    '720p': self.quality_720p_path,
                    '480p': self.quality_480p_path,
                    '360p': self.quality_360p_path,
                }
            },
            'metadata': {
                'duration_seconds': self.duration_seconds,
                'resolution': self.resolution,
                'format': self.format,
                'fps': self.fps,
                'file_size_bytes': self.file_size_bytes,
                'total_size_all_versions': self.total_size_all_versions
            },
            'audio': {
                'codec': self.audio_codec,
                'bitrate': self.audio_bitrate,
                'sample_rate': self.audio_sample_rate
            },
            'video': {
                'codec': self.video_codec,
                'bitrate': self.video_bitrate,
                'crf': self.crf
            },
            'status': self.status,
            'processing': {
                'processing_time_seconds': self.processing_time_seconds,
                'encoding_time_seconds': self.encoding_time_seconds,
                'total_processing_time': self.total_processing_time,
                'retry_count': self.retry_count,
                'last_retry_at': self.last_retry_at.isoformat() if self.last_retry_at else None
            },
            'composition_config': self.composition_config or {},
            'branding': {
                'branding_applied': self.branding_applied,
                'logo_used': self.logo_used,
                'logo_position': self.logo_position,
                'watermark_text': self.watermark_text,
                'overlays_count': self.overlays_count,
                'overlays_data': self.overlays_data or []
            },
            'intro_outro': {
                'has_intro': self.has_intro,
                'intro_duration': self.intro_duration,
                'intro_config': self.intro_config,
                'has_outro': self.has_outro,
                'outro_duration': self.outro_duration,
                'outro_config': self.outro_config
            },
            'background_music': {
                'has_background_music': self.has_background_music,
                'background_music_path': self.background_music_path,
                'background_music_volume': self.background_music_volume
            },
            'optimization': {
                'web_optimized': self.web_optimized,
                'preset': self.preset
            },
            'cost': {
                'cost_estimate': self.cost_estimate,
                'cpu_time_seconds': self.cpu_time_seconds,
                'memory_peak_mb': self.memory_peak_mb
            },
            'analytics': {
                'download_count': self.download_count,
                'view_count': self.view_count,
                'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None
            },
            'version': self.version,
            'parent_video_id': self.parent_video_id,
            'timestamps': {
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'started_at': self.started_at.isoformat() if self.started_at else None,
                'completed_at': self.completed_at.isoformat() if self.completed_at else None,
                'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
            },
            'flags': {
                'is_active': self.is_active,
                'is_deleted': self.is_deleted,
                'is_public': self.is_public
            },
            'error_message': self.error_message if self.status == 'failed' else None,
            'error_details': self.error_details if self.status == 'failed' else None
        }

    def get_file_path_for_quality(self, quality: str) -> str:
        """Get the file path for a specific quality version."""
        quality_map = {
            '2160p': self.quality_2160p_path,
            '1080p': self.quality_1080p_path,
            '720p': self.quality_720p_path,
            '480p': self.quality_480p_path,
            '360p': self.quality_360p_path,
        }
        return quality_map.get(quality) or self.video_file_path

    def get_available_qualities(self) -> list:
        """Get list of available quality versions."""
        qualities = []
        if self.quality_2160p_path:
            qualities.append('2160p')
        if self.quality_1080p_path:
            qualities.append('1080p')
        if self.quality_720p_path:
            qualities.append('720p')
        if self.quality_480p_path:
            qualities.append('480p')
        if self.quality_360p_path:
            qualities.append('360p')
        return qualities


class CompositionJob(Base):
    """
    CompositionJob model for tracking video composition jobs in queue.

    Manages the job queue for video composition, allowing for background
    processing and tracking of long-running composition tasks.
    """

    __tablename__ = "composition_jobs"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    composed_video_id = Column(Integer, ForeignKey("composed_videos.id"), nullable=True, index=True)
    composed_video = relationship("ComposedVideo", backref="jobs")

    demo_site_id = Column(Integer, ForeignKey("demo_sites.id"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)

    # Job details
    job_type = Column(String(50), nullable=False)  # compose, recompose, encode_quality, thumbnail
    priority = Column(Integer, default=5, nullable=False)  # 1-10, higher is more important

    # Status
    status = Column(String(50), default="queued", nullable=False, index=True)
    # Status values: queued, processing, completed, failed, cancelled

    progress = Column(Float, default=0.0, nullable=False)  # 0.0 to 1.0

    # Configuration
    job_config = Column(JSON, nullable=True)  # Job-specific configuration

    # Processing details
    worker_id = Column(String(100), nullable=True)  # ID of worker processing this job
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_time_seconds = Column(Float, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    last_retry_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<CompositionJob(id={self.id}, job_type='{self.job_type}', status='{self.status}', progress={self.progress})>"

    def to_dict(self):
        """Convert composition job to dictionary for API responses."""
        return {
            'id': self.id,
            'composed_video_id': self.composed_video_id,
            'demo_site_id': self.demo_site_id,
            'lead_id': self.lead_id,
            'job_type': self.job_type,
            'priority': self.priority,
            'status': self.status,
            'progress': self.progress,
            'job_config': self.job_config or {},
            'processing': {
                'worker_id': self.worker_id,
                'started_at': self.started_at.isoformat() if self.started_at else None,
                'completed_at': self.completed_at.isoformat() if self.completed_at else None,
                'processing_time_seconds': self.processing_time_seconds
            },
            'error': {
                'error_message': self.error_message,
                'retry_count': self.retry_count,
                'max_retries': self.max_retries,
                'last_retry_at': self.last_retry_at.isoformat() if self.last_retry_at else None
            },
            'timestamps': {
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }
        }
