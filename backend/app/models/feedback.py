"""
Feedback model for storing user interactions with leads for ML training.
Also includes AI-GYM models for tracking AI model performance.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base


class LeadFeedback(Base):
    """Lead feedback model for storing user interactions and ratings."""
    
    __tablename__ = "lead_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Lead relationship
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    lead = relationship("Lead", backref="feedback")
    
    # User interaction data
    user_rating = Column(Float, nullable=True)  # 0-100 score from user
    action_type = Column(String(50), nullable=False, index=True)  # view, contact, archive, rate, convert
    interaction_duration = Column(Float, nullable=True)  # seconds spent viewing
    
    # Feedback context
    feedback_source = Column(String(50), nullable=False, default="manual")  # manual, implicit, conversion
    feedback_confidence = Column(Float, nullable=False, default=1.0)  # 0-1 confidence in feedback
    
    # Contact outcome (if applicable)
    contact_successful = Column(Boolean, nullable=True)
    contact_response_time = Column(Float, nullable=True)  # hours to response
    conversion_value = Column(Float, nullable=True)  # business value if converted
    
    # Additional metadata
    session_id = Column(String(255), nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Model tracking
    model_version = Column(String(50), nullable=True, index=True)
    prediction_score = Column(Float, nullable=True)  # Model's prediction at time of feedback
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<LeadFeedback(id={self.id}, lead_id={self.lead_id}, action='{self.action_type}', rating={self.user_rating})>"


class ModelMetrics(Base):
    """Model performance metrics tracking."""
    
    __tablename__ = "model_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Model identification
    model_version = Column(String(50), nullable=False, index=True)
    model_type = Column(String(50), nullable=False, default="xgboost")
    
    # Performance metrics
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    auc_roc = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    
    # Business metrics
    conversion_rate = Column(Float, nullable=True)
    contact_success_rate = Column(Float, nullable=True)
    avg_prediction_score = Column(Float, nullable=True)
    
    # Training details
    training_samples = Column(Integer, nullable=True)
    validation_samples = Column(Integer, nullable=True)
    feature_count = Column(Integer, nullable=True)
    training_duration = Column(Float, nullable=True)  # seconds
    
    # Deployment tracking
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ModelMetrics(version='{self.model_version}', f1={self.f1_score}, active={self.is_active})>"


class ABTestVariant(Base):
    """A/B testing variants for model comparison."""

    __tablename__ = "ab_test_variants"

    id = Column(Integer, primary_key=True, index=True)

    # Test configuration
    test_name = Column(String(100), nullable=False, index=True)
    variant_name = Column(String(50), nullable=False, index=True)
    model_version = Column(String(50), nullable=False, index=True)

    # Traffic allocation
    traffic_percentage = Column(Float, nullable=False, default=50.0)  # 0-100
    is_control = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Test results
    sample_size = Column(Integer, default=0, nullable=False)
    conversion_rate = Column(Float, nullable=True)
    avg_score = Column(Float, nullable=True)
    avg_quality_score = Column(Float, nullable=True)  # AI-GYM: Quality score
    avg_cost_usd = Column(Float, nullable=True)  # AI-GYM: Average cost
    confidence_interval_lower = Column(Float, nullable=True)
    confidence_interval_upper = Column(Float, nullable=True)
    statistical_significance = Column(Float, nullable=True)

    # Test timeline
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)

    # Metadata (stores task_type, target_metric, etc.)
    test_metadata = Column(JSON, nullable=True)

    # Model ID (for AI-GYM - full model identifier like "openai/gpt-4")
    model_id = Column(String(100), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<ABTestVariant(test='{self.test_name}', variant='{self.variant_name}', model='{self.model_version}')>"


class ModelMetric(Base):
    """
    AI-GYM: Execution metrics for AI model performance tracking.

    Records detailed metrics for every AI execution to enable:
    - Performance comparison
    - Cost analysis
    - Quality assessment
    - Continuous optimization
    """

    __tablename__ = "ai_model_metrics"

    id = Column(Integer, primary_key=True, index=True)

    # Model identification
    model_id = Column(String(100), nullable=False, index=True)  # e.g., "openai/gpt-4-turbo"
    task_type = Column(String(50), nullable=False, index=True)  # e.g., "website_analysis"

    # Token usage and cost
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    latency_ms = Column(Integer, nullable=False)
    cost_usd = Column(Float, nullable=False)

    # Quality metrics
    quality_score = Column(Float, nullable=True)  # 0-100 automated score
    user_approved = Column(Boolean, nullable=True)  # User feedback
    edit_distance = Column(Integer, nullable=True)  # Characters changed by user

    # Error tracking
    error_occurred = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text, nullable=True)

    # Additional context
    execution_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<ModelMetric(id={self.id}, model='{self.model_id}', task='{self.task_type}', cost=${self.cost_usd:.4f})>"