"""
Tags system for categorizing and managing leads.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base


class Tag(Base):
    """Tag model for organizing and categorizing leads."""

    __tablename__ = "tags"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Tag information
    name = Column(String(255), unique=True, nullable=False, index=True)
    color = Column(String(7), default="#808080", nullable=False)  # Hex color code
    category = Column(String(100), nullable=True, index=True)  # e.g., "priority", "status", "type"

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    lead_tags = relationship("LeadTag", back_populates="tag", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}', category='{self.category}')>"


class LeadTag(Base):
    """Junction table for many-to-many relationship between leads and tags."""

    __tablename__ = "lead_tags"

    # Foreign keys
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, nullable=False)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tag = relationship("Tag", back_populates="lead_tags")

    def __repr__(self):
        return f"<LeadTag(lead_id={self.lead_id}, tag_id={self.tag_id})>"
