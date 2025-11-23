"""
Notes system for lead annotations and management tracking.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base


class Note(Base):
    """Note model for storing lead annotations and notes."""

    __tablename__ = "notes"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)

    # Note content
    content = Column(Text, nullable=False)
    author_id = Column(String(255), nullable=True)  # User ID or email of note author

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    lead = relationship("Lead", backref="notes")

    def __repr__(self):
        return f"<Note(id={self.id}, lead_id={self.lead_id}, author='{self.author_id}')>"
