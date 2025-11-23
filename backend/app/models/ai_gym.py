"""
AI Gym Performance Tracking Models.

Tracks AI model usage, costs, and performance metrics.
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from typing import Optional

from .base import Base


class AIGymPerformance(Base):
    """Track AI model performance, costs, and quality metrics."""

    __tablename__ = "ai_gym_performance"

    id = Column(Integer, primary_key=True, index=True)

    # Request context
    task_type = Column(String(100), nullable=False, index=True)  # e.g., "website_analysis", "email_generation"
    model_name = Column(String(100), nullable=False, index=True)  # e.g., "anthropic/claude-sonnet-4"
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)
    request_metadata = Column("metadata", JSON, nullable=True)  # Additional context

    # Token usage
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    # Cost tracking
    cost = Column(Float, nullable=True)  # Cost in dollars

    # Performance metrics
    duration_seconds = Column(Float, nullable=True)  # Request duration

    # Response data
    response_text = Column(Text, nullable=True)  # Generated response

    # Quality scores (0.0 to 1.0)
    faithfulness_score = Column(Float, nullable=True)  # Accuracy of information
    relevance_score = Column(Float, nullable=True)  # Relevance to task
    coherence_score = Column(Float, nullable=True)  # Logical flow
    conciseness_score = Column(Float, nullable=True)  # Brevity
    composite_score = Column(Float, nullable=True)  # Overall quality

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<AIGymPerformance(id={self.id}, task={self.task_type}, model={self.model_name}, cost=${self.cost})>"
