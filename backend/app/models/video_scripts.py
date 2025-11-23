"""
VideoScript model for Phase 4 video automation.

Stores AI-generated video scripts with sections, timing, and metadata.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base


class VideoScript(Base):
    """
    VideoScript model for storing AI-generated video scripts.

    Stores complete video scripts with sections, timing estimates,
    and generation metadata for demo site videos.
    """

    __tablename__ = "video_scripts"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    demo_site_id = Column(Integer, ForeignKey("demo_sites.id"), nullable=False, index=True)
    demo_site = relationship("DemoSite", backref="video_scripts")

    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    lead = relationship("Lead", backref="video_scripts")

    # Script configuration
    script_style = Column(String(50), nullable=False, index=True)
    # Styles: professional, casual, technical, sales

    # Script content
    sections = Column(JSON, nullable=False)
    # Array of ScriptSection objects: [{title, content, duration_seconds, scene_type, visual_cues, camera_instructions}, ...]

    # Duration
    total_duration_seconds = Column(Integer, nullable=False, index=True)

    # Messaging
    target_audience = Column(Text, nullable=True)
    key_messages = Column(JSON, nullable=True)
    # Array of key message strings

    # AI generation metadata
    ai_model_used = Column(String(100), nullable=True)
    ai_cost = Column(Float, nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    generation_time_seconds = Column(Float, nullable=True)

    # Script metadata
    script_metadata = Column(JSON, nullable=True)
    # Additional metadata: {improvement_plan_id, demo_site_url, custom_instructions, etc.}

    # Validation and quality
    validation_warnings = Column(JSON, nullable=True)
    # Array of validation warning strings

    is_approved = Column(String(50), nullable=False, default="pending", index=True)
    # Values: pending, approved, rejected, needs_revision

    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)

    # Versioning
    version = Column(Integer, nullable=False, default=1)
    parent_script_id = Column(Integer, ForeignKey("video_scripts.id"), nullable=True)
    # Reference to previous version if regenerated

    # Usage tracking
    video_generated = Column(String(50), nullable=False, default="pending", index=True)
    # Values: pending, generating, completed, failed
    video_id = Column(Integer, nullable=True)  # FK to videos table (Phase 4 Task 2)
    video_url = Column(Text, nullable=True)

    times_viewed = Column(Integer, nullable=False, default=0)
    last_viewed_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Flags
    is_active = Column(String(50), nullable=False, default="active", index=True)
    is_deleted = Column(String(50), nullable=False, default="false", index=True)

    def __repr__(self):
        return f"<VideoScript(id={self.id}, lead_id={self.lead_id}, style='{self.script_style}', duration={self.total_duration_seconds}s)>"

    def to_dict(self):
        """Convert video script to dictionary for API responses."""
        return {
            'id': self.id,
            'demo_site_id': self.demo_site_id,
            'lead_id': self.lead_id,
            'script_style': self.script_style,
            'sections': self.sections or [],
            'total_duration_seconds': self.total_duration_seconds,
            'target_audience': self.target_audience,
            'key_messages': self.key_messages or [],
            'ai_generation': {
                'model_used': self.ai_model_used,
                'cost': self.ai_cost,
                'prompt_tokens': self.prompt_tokens,
                'completion_tokens': self.completion_tokens,
                'generation_time_seconds': self.generation_time_seconds
            },
            'metadata': self.metadata or {},
            'validation': {
                'warnings': self.validation_warnings or [],
                'is_approved': self.is_approved,
                'approved_by': self.approved_by,
                'approved_at': self.approved_at.isoformat() if self.approved_at else None,
                'approval_notes': self.approval_notes
            },
            'version': self.version,
            'parent_script_id': self.parent_script_id,
            'video': {
                'status': self.video_generated,
                'video_id': self.video_id,
                'video_url': self.video_url
            },
            'usage': {
                'times_viewed': self.times_viewed,
                'last_viewed_at': self.last_viewed_at.isoformat() if self.last_viewed_at else None
            },
            'timestamps': {
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
            },
            'flags': {
                'is_active': self.is_active,
                'is_deleted': self.is_deleted
            }
        }

    def get_script_summary(self):
        """Get brief summary of script for listings."""
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'demo_site_id': self.demo_site_id,
            'style': self.script_style,
            'duration': self.total_duration_seconds,
            'sections_count': len(self.sections) if self.sections else 0,
            'is_approved': self.is_approved,
            'video_status': self.video_generated,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
