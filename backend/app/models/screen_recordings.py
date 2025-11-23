"""
ScreenRecording model for tracking demo site screen recordings.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base
import enum


class RecordingStatus(str, enum.Enum):
    """Recording status values."""
    PENDING = "pending"
    RECORDING = "recording"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoFormat(str, enum.Enum):
    """Supported video formats."""
    MP4 = "mp4"
    WEBM = "webm"
    AVI = "avi"


class VideoQuality(str, enum.Enum):
    """Video quality presets."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


class ScreenRecording(Base):
    """
    ScreenRecording model for tracking demo site screen recordings.

    Stores information about screen recordings of demo sites, including
    recording configuration, file paths, and processing metadata.
    """

    __tablename__ = "screen_recordings"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    demo_site_id = Column(Integer, ForeignKey("demo_sites.id"), nullable=False, index=True)
    demo_site = relationship("DemoSite", backref="screen_recordings")

    video_script_id = Column(Integer, nullable=True, index=True)  # FK to video_scripts (future)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    lead = relationship("Lead", backref="screen_recordings")

    # File information
    video_file_path = Column(Text, nullable=True)  # Storage path
    thumbnail_path = Column(Text, nullable=True)  # Preview thumbnail path
    file_size_bytes = Column(Integer, nullable=True)

    # Video metadata
    duration_seconds = Column(Float, nullable=True)
    resolution = Column(String(50), nullable=False, default="1920x1080")  # "1920x1080", "1280x720", etc.
    frame_rate = Column(Integer, nullable=False, default=30)  # FPS
    format = Column(String(20), nullable=False, default="mp4")  # "mp4", "webm", "avi"

    # Recording status
    status = Column(String(50), default="pending", nullable=False, index=True)
    # Status values: pending, recording, processing, completed, failed

    # Recording configuration
    recording_config = Column(JSON, nullable=True)  # Recording settings
    # {
    #   "resolution": "1920x1080",
    #   "frame_rate": 30,
    #   "video_format": "mp4",
    #   "video_codec": "h264",
    #   "quality": "high",
    #   "show_cursor": true,
    #   "scroll_speed": 1000,
    #   "transition_duration_ms": 300,
    #   "highlight_clicks": true,
    #   "highlight_color": "#FF0000"
    # }

    # Interactions performed
    interactions_performed = Column(JSON, nullable=True)  # List of interactions
    # [
    #   {"type": "scroll", "selector": "header", "duration_ms": 2000, "x": null, "y": null},
    #   {"type": "click", "selector": ".cta-button", "duration_ms": 500, "x": 640, "y": 360}
    # ]

    # Recording session details
    recording_session_id = Column(Integer, ForeignKey("recording_sessions.id"), nullable=True, index=True)

    # Processing information
    processing_time_seconds = Column(Float, nullable=True)  # Time taken to process/encode
    segments_count = Column(Integer, default=0, nullable=False)  # Number of video segments
    total_frames = Column(Integer, nullable=True)  # Total frames captured

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)  # Detailed error information
    retry_count = Column(Integer, default=0, nullable=False)  # Number of retry attempts

    # Quality metrics
    video_bitrate = Column(Integer, nullable=True)  # Video bitrate in kbps
    audio_bitrate = Column(Integer, nullable=True)  # Audio bitrate in kbps (if audio is added)
    video_codec = Column(String(50), nullable=True)  # e.g., "h264", "vp9"

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    recording_started_at = Column(DateTime(timezone=True), nullable=True, index=True)
    recording_completed_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Flags
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    def __repr__(self):
        return f"<ScreenRecording(id={self.id}, demo_site_id={self.demo_site_id}, status='{self.status}')>"

    def to_dict(self):
        """Convert screen recording to dictionary for API responses."""
        return {
            'id': self.id,
            'demo_site_id': self.demo_site_id,
            'video_script_id': self.video_script_id,
            'lead_id': self.lead_id,
            'file': {
                'video_file_path': self.video_file_path,
                'thumbnail_path': self.thumbnail_path,
                'file_size_bytes': self.file_size_bytes,
                'file_size_mb': round(self.file_size_bytes / (1024 * 1024), 2) if self.file_size_bytes else None
            },
            'video': {
                'duration_seconds': self.duration_seconds,
                'resolution': self.resolution,
                'frame_rate': self.frame_rate,
                'format': self.format,
                'video_codec': self.video_codec,
                'video_bitrate': self.video_bitrate,
                'audio_bitrate': self.audio_bitrate
            },
            'status': self.status,
            'recording_config': self.recording_config or {},
            'interactions_performed': self.interactions_performed or [],
            'recording_session_id': self.recording_session_id,
            'processing': {
                'processing_time_seconds': self.processing_time_seconds,
                'segments_count': self.segments_count,
                'total_frames': self.total_frames
            },
            'error': {
                'error_message': self.error_message,
                'error_details': self.error_details,
                'retry_count': self.retry_count
            } if self.status == 'failed' else None,
            'timestamps': {
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'recording_started_at': self.recording_started_at.isoformat() if self.recording_started_at else None,
                'recording_completed_at': self.recording_completed_at.isoformat() if self.recording_completed_at else None
            },
            'is_deleted': self.is_deleted
        }


class RecordingSession(Base):
    """
    RecordingSession model for tracking individual recording sessions.

    Stores detailed information about each recording session including
    segments, frames, and performance metrics.
    """

    __tablename__ = "recording_sessions"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys (one-to-many relationship - a session can have multiple recordings if retried)
    recordings = relationship("ScreenRecording", backref="session")

    # Session details
    session_id = Column(String(255), nullable=False, unique=True, index=True)  # Unique session identifier
    browser_context_id = Column(String(255), nullable=True)  # Playwright browser context ID

    # Session timing
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=True, index=True)
    duration_seconds = Column(Float, nullable=True)

    # Recording metrics
    segments_count = Column(Integer, default=0, nullable=False)
    total_frames = Column(Integer, default=0, nullable=False)
    frames_per_second = Column(Float, nullable=True)  # Actual FPS achieved
    dropped_frames = Column(Integer, default=0, nullable=False)

    # Performance metrics
    processing_time_seconds = Column(Float, nullable=True)
    cpu_usage_percent = Column(Float, nullable=True)  # Average CPU usage during recording
    memory_usage_mb = Column(Float, nullable=True)  # Peak memory usage

    # Session status
    status = Column(String(50), default="active", nullable=False, index=True)
    # Status values: active, completed, failed, cancelled

    # Metadata
    session_metadata = Column(JSON, nullable=True)
    # {
    #   "browser_version": "1.40.0",
    #   "os": "darwin",
    #   "viewport": {"width": 1920, "height": 1080},
    #   "user_agent": "Mozilla/5.0...",
    #   "network_conditions": "online",
    #   "screenshots_taken": 45
    # }

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_stack_trace = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<RecordingSession(id={self.id}, session_id='{self.session_id}', status='{self.status}')>"

    def to_dict(self):
        """Convert recording session to dictionary for API responses."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'browser_context_id': self.browser_context_id,
            'timing': {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None,
                'duration_seconds': self.duration_seconds
            },
            'metrics': {
                'segments_count': self.segments_count,
                'total_frames': self.total_frames,
                'frames_per_second': self.frames_per_second,
                'dropped_frames': self.dropped_frames
            },
            'performance': {
                'processing_time_seconds': self.processing_time_seconds,
                'cpu_usage_percent': self.cpu_usage_percent,
                'memory_usage_mb': self.memory_usage_mb
            },
            'status': self.status,
            'metadata': self.metadata or {},
            'error': {
                'error_message': self.error_message,
                'error_stack_trace': self.error_stack_trace
            } if self.status == 'failed' else None,
            'timestamps': {
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }
        }


class RecordingSegment(Base):
    """
    RecordingSegment model for tracking individual video segments.

    Stores information about each segment of a recording before they
    are merged into the final video.
    """

    __tablename__ = "recording_segments"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    recording_session_id = Column(Integer, ForeignKey("recording_sessions.id"), nullable=False, index=True)
    recording_session = relationship("RecordingSession", backref="segments")

    # Segment details
    segment_number = Column(Integer, nullable=False)  # Order in sequence
    segment_file_path = Column(Text, nullable=True)  # Path to segment file
    duration_seconds = Column(Float, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)

    # Segment type
    segment_type = Column(String(50), nullable=False)  # "scene", "transition", "interaction"
    scene_name = Column(String(255), nullable=True)  # Name of the scene being recorded

    # Quality metrics
    frames_count = Column(Integer, nullable=True)
    average_frame_time_ms = Column(Float, nullable=True)

    # Status
    status = Column(String(50), default="pending", nullable=False)
    # Status values: pending, recording, completed, failed

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<RecordingSegment(id={self.id}, session_id={self.recording_session_id}, segment_number={self.segment_number})>"

    def to_dict(self):
        """Convert recording segment to dictionary for API responses."""
        return {
            'id': self.id,
            'recording_session_id': self.recording_session_id,
            'segment_number': self.segment_number,
            'segment_file_path': self.segment_file_path,
            'duration_seconds': self.duration_seconds,
            'file_size_bytes': self.file_size_bytes,
            'segment_type': self.segment_type,
            'scene_name': self.scene_name,
            'frames_count': self.frames_count,
            'average_frame_time_ms': self.average_frame_time_ms,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
