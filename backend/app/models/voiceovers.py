"""
Voiceover models for video script audio generation.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base
from decimal import Decimal
from typing import Optional, Dict, Any
import enum


class VoiceoverStatus(str, enum.Enum):
    """Voiceover generation status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AudioFormat(str, enum.Enum):
    """Supported audio formats."""
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"


class Voiceover(Base):
    """
    Voiceover model for storing generated audio files.

    Stores information about voiceovers generated for video scripts,
    including audio file metadata, cost tracking, and generation status.
    """

    __tablename__ = "voiceovers"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys - Note: video_script_id will be added when video scripts are implemented
    # For now, we'll make it optional to allow standalone voiceover generation
    video_script_id = Column(Integer, nullable=True, index=True)  # FK to video_scripts (future)
    demo_site_id = Column(Integer, ForeignKey("demo_sites.id"), nullable=True, index=True)
    demo_site = relationship("DemoSite", backref="voiceovers")
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    lead = relationship("Lead", backref="voiceovers")

    # Voice configuration
    voice_preset = Column(String(100), nullable=False, index=True)
    # Presets: professional_male, professional_female, casual_male, casual_female, etc.
    voice_id = Column(String(100), nullable=True)  # ElevenLabs voice ID
    voice_name = Column(String(255), nullable=True)  # Voice name for reference

    # Voice settings
    voice_settings = Column(JSON, nullable=True)  # Stability, similarity_boost, style, etc.

    # Model configuration
    model_id = Column(String(100), nullable=False, default="eleven_multilingual_v2")
    # Models: eleven_multilingual_v2, eleven_turbo_v2, etc.

    # Audio file information
    audio_file_path = Column(Text, nullable=True)  # Local storage path or S3 URL
    audio_url = Column(Text, nullable=True)  # Public URL if hosted
    duration_seconds = Column(Float, nullable=True)  # Audio duration
    format = Column(String(10), default="mp3", nullable=False)  # mp3, wav, ogg
    sample_rate = Column(Integer, default=44100, nullable=False)  # Sample rate in Hz
    file_size_bytes = Column(Integer, nullable=True)  # File size in bytes

    # Text content
    text_content = Column(Text, nullable=True)  # The text that was converted to speech
    characters_processed = Column(Integer, nullable=False)  # Number of characters processed

    # Cost tracking
    cost_usd = Column(Numeric(10, 4), nullable=True)  # Cost in USD
    api_provider = Column(String(50), default="elevenlabs", nullable=False)

    # Processing status
    status = Column(
        String(50),
        default=VoiceoverStatus.PENDING,
        nullable=False,
        index=True
    )
    error_message = Column(Text, nullable=True)  # Error details if failed

    # Metadata
    voice_metadata = Column(JSON, nullable=True)  # Additional metadata (sections, pauses, etc.)

    # Audio processing options
    merge_sections = Column(Boolean, default=True, nullable=False)
    add_section_pauses = Column(Boolean, default=True, nullable=False)
    pause_duration_ms = Column(Integer, default=500, nullable=False)

    # Quality metrics
    quality_score = Column(Float, nullable=True)  # Quality rating (0-1)
    user_rating = Column(Integer, nullable=True)  # User rating (1-5)
    user_feedback = Column(Text, nullable=True)  # User feedback

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)

    # Flags
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return (
            f"<Voiceover(id={self.id}, lead_id={self.lead_id}, "
            f"voice_preset='{self.voice_preset}', status='{self.status}', "
            f"duration={self.duration_seconds}s)>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert voiceover to dictionary for API responses."""
        return {
            'id': self.id,
            'video_script_id': self.video_script_id,
            'demo_site_id': self.demo_site_id,
            'lead_id': self.lead_id,
            'voice': {
                'preset': self.voice_preset,
                'voice_id': self.voice_id,
                'voice_name': self.voice_name,
                'settings': self.voice_settings or {},
                'model_id': self.model_id
            },
            'audio': {
                'file_path': self.audio_file_path,
                'url': self.audio_url,
                'duration_seconds': self.duration_seconds,
                'format': self.format,
                'sample_rate': self.sample_rate,
                'file_size_bytes': self.file_size_bytes
            },
            'text': {
                'content': self.text_content[:100] + '...' if self.text_content and len(self.text_content) > 100 else self.text_content,
                'characters_processed': self.characters_processed
            },
            'cost': {
                'cost_usd': float(self.cost_usd) if self.cost_usd else None,
                'api_provider': self.api_provider
            },
            'status': self.status,
            'error_message': self.error_message if self.status == VoiceoverStatus.FAILED else None,
            'processing_options': {
                'merge_sections': self.merge_sections,
                'add_section_pauses': self.add_section_pauses,
                'pause_duration_ms': self.pause_duration_ms
            },
            'quality': {
                'quality_score': self.quality_score,
                'user_rating': self.user_rating,
                'user_feedback': self.user_feedback
            },
            'metadata': self.metadata or {},
            'timestamps': {
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'processing_started_at': self.processing_started_at.isoformat() if self.processing_started_at else None,
                'processing_completed_at': self.processing_completed_at.isoformat() if self.processing_completed_at else None
            },
            'is_deleted': self.is_deleted
        }

    def get_processing_duration(self) -> Optional[float]:
        """Calculate processing duration in seconds."""
        if self.processing_started_at and self.processing_completed_at:
            delta = self.processing_completed_at - self.processing_started_at
            return delta.total_seconds()
        return None


class VoiceoverUsage(Base):
    """
    VoiceoverUsage model for tracking daily usage statistics.

    Aggregates voiceover usage by date for analytics and quota management.
    """

    __tablename__ = "voiceover_usage"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Date tracking
    date = Column(Date, nullable=False, unique=True, index=True)

    # Usage statistics
    characters_used = Column(Integer, default=0, nullable=False)
    requests_count = Column(Integer, default=0, nullable=False)
    successful_requests = Column(Integer, default=0, nullable=False)
    failed_requests = Column(Integer, default=0, nullable=False)

    # Cost tracking
    cost_usd = Column(Numeric(10, 4), default=0, nullable=False)

    # Audio statistics
    total_duration_seconds = Column(Float, default=0, nullable=False)
    avg_duration_seconds = Column(Float, nullable=True)
    total_file_size_bytes = Column(Integer, default=0, nullable=False)

    # Voice preset usage breakdown
    voice_preset_usage = Column(JSON, nullable=True)  # Dict of preset -> count

    # Provider breakdown
    provider_usage = Column(JSON, nullable=True)  # Dict of provider -> stats

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return (
            f"<VoiceoverUsage(date={self.date}, characters={self.characters_used}, "
            f"requests={self.requests_count}, cost=${self.cost_usd})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert usage to dictionary for API responses."""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'usage': {
                'characters_used': self.characters_used,
                'requests_count': self.requests_count,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'success_rate': (
                    self.successful_requests / self.requests_count * 100
                    if self.requests_count > 0 else 0
                )
            },
            'cost': {
                'total_usd': float(self.cost_usd) if self.cost_usd else 0,
                'cost_per_character': (
                    float(self.cost_usd) / self.characters_used
                    if self.characters_used > 0 else 0
                )
            },
            'audio': {
                'total_duration_seconds': self.total_duration_seconds,
                'avg_duration_seconds': self.avg_duration_seconds,
                'total_file_size_bytes': self.total_file_size_bytes,
                'avg_file_size_bytes': (
                    self.total_file_size_bytes / self.successful_requests
                    if self.successful_requests > 0 else 0
                )
            },
            'voice_preset_usage': self.voice_preset_usage or {},
            'provider_usage': self.provider_usage or {},
            'timestamps': {
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }
        }

    def update_stats(self, voiceover: Voiceover):
        """
        Update usage statistics with a new voiceover.

        Args:
            voiceover: Voiceover instance to add to stats
        """
        self.requests_count += 1

        if voiceover.status == VoiceoverStatus.COMPLETED:
            self.successful_requests += 1
            self.characters_used += voiceover.characters_processed
            if voiceover.cost_usd:
                self.cost_usd += voiceover.cost_usd
            if voiceover.duration_seconds:
                self.total_duration_seconds += voiceover.duration_seconds
            if voiceover.file_size_bytes:
                self.total_file_size_bytes += voiceover.file_size_bytes

            # Update voice preset usage
            if not self.voice_preset_usage:
                self.voice_preset_usage = {}
            preset = voiceover.voice_preset
            self.voice_preset_usage[preset] = self.voice_preset_usage.get(preset, 0) + 1

        elif voiceover.status == VoiceoverStatus.FAILED:
            self.failed_requests += 1

        # Update average duration
        if self.successful_requests > 0:
            self.avg_duration_seconds = self.total_duration_seconds / self.successful_requests


class VoiceoverCache(Base):
    """
    VoiceoverCache model for caching frequently used audio segments.

    Caches audio for identical text/voice combinations to save API costs.
    """

    __tablename__ = "voiceover_cache"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Cache key (hash of text + voice settings)
    cache_key = Column(String(64), unique=True, nullable=False, index=True)

    # Cached content
    text_content = Column(Text, nullable=False)
    voice_preset = Column(String(100), nullable=False, index=True)
    model_id = Column(String(100), nullable=False)

    # Audio information
    audio_file_path = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    format = Column(String(10), nullable=False)
    sample_rate = Column(Integer, nullable=False)
    file_size_bytes = Column(Integer, nullable=True)

    # Usage statistics
    hit_count = Column(Integer, default=0, nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    def __repr__(self):
        return (
            f"<VoiceoverCache(id={self.id}, cache_key='{self.cache_key[:16]}...', "
            f"hits={self.hit_count})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert cache entry to dictionary."""
        return {
            'id': self.id,
            'cache_key': self.cache_key,
            'text_content': self.text_content[:100] + '...' if len(self.text_content) > 100 else self.text_content,
            'voice_preset': self.voice_preset,
            'model_id': self.model_id,
            'audio': {
                'file_path': self.audio_file_path,
                'duration_seconds': self.duration_seconds,
                'format': self.format,
                'sample_rate': self.sample_rate,
                'file_size_bytes': self.file_size_bytes
            },
            'usage': {
                'hit_count': self.hit_count,
                'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None
            },
            'timestamps': {
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'expires_at': self.expires_at.isoformat() if self.expires_at else None
            }
        }
