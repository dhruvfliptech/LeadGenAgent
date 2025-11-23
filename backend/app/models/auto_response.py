"""
Auto-Response Models for Template-Based Lead Responses

This module provides models for automated response generation and tracking:
- AutoResponse: Generated responses with delivery tracking
- ResponseVariable: Template variable definitions for personalization
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float, Index
from sqlalchemy.orm import relationship
from app.models.base import Base


class AutoResponse(Base):
    """
    AutoResponse Model

    Stores generated auto-responses for leads with template personalization,
    delivery tracking, and engagement metrics.
    """
    __tablename__ = "auto_responses"

    id = Column(Integer, primary_key=True, index=True)

    # References
    lead_id = Column(Integer, ForeignKey('leads.id'), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey('response_templates.id'), nullable=False, index=True)

    # Generated content
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)

    # Personalization
    personalization_data = Column(JSON, default=dict)  # Extracted lead data used for personalization
    variables_used = Column(JSON, default=list)  # List of variable names used

    # Scheduling
    delay_minutes = Column(Integer, default=0)
    scheduled_at = Column(DateTime, nullable=True, index=True)
    sent_at = Column(DateTime, nullable=True, index=True)

    # Delivery status
    status = Column(String(50), default='pending', index=True)  # pending, scheduled, sending, sent, failed, cancelled
    delivery_status = Column(String(50), nullable=True)  # delivered, bounced, rejected
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Engagement tracking
    email_opened = Column(Boolean, default=False)
    opened_at = Column(DateTime, nullable=True)
    open_count = Column(Integer, default=0)

    email_clicked = Column(Boolean, default=False)
    clicked_at = Column(DateTime, nullable=True)
    click_count = Column(Integer, default=0)

    lead_responded = Column(Boolean, default=False)
    responded_at = Column(DateTime, nullable=True)
    response_content = Column(Text, nullable=True)

    # A/B Testing
    variant_id = Column(String(100), nullable=True, index=True)  # For tracking template variants

    # AI Enhancement
    ai_enhanced = Column(Boolean, default=False)
    ai_model_used = Column(String(100), nullable=True)
    ai_enhancement_cost = Column(Float, nullable=True)

    # Email headers and metadata
    message_id = Column(String(255), unique=True, index=True)  # Email message ID
    from_address = Column(String(255))
    to_address = Column(String(255))
    cc_addresses = Column(JSON, default=list)
    bcc_addresses = Column(JSON, default=list)

    # Tracking
    tracking_token = Column(String(255), unique=True, index=True)  # For open/click tracking
    unsubscribe_token = Column(String(255), unique=True, index=True)

    # Metrics
    send_duration_ms = Column(Integer, nullable=True)  # Time to send in milliseconds
    quality_score = Column(Float, nullable=True)  # 0-100 AI quality score

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lead = relationship("Lead", backref="auto_responses", foreign_keys=[lead_id])
    template = relationship("ResponseTemplate", backref="auto_responses", foreign_keys=[template_id])

    # Indexes for common queries
    __table_args__ = (
        Index('idx_auto_response_lead_template', 'lead_id', 'template_id'),
        Index('idx_auto_response_status_scheduled', 'status', 'scheduled_at'),
        Index('idx_auto_response_engagement', 'email_opened', 'email_clicked', 'lead_responded'),
        Index('idx_auto_response_variant', 'variant_id', 'status'),
    )

    def __repr__(self):
        return f"<AutoResponse(id={self.id}, lead_id={self.lead_id}, status='{self.status}')>"

    @property
    def is_pending(self) -> bool:
        """Check if response is pending delivery."""
        return self.status in ['pending', 'scheduled']

    @property
    def is_delivered(self) -> bool:
        """Check if response was successfully delivered."""
        return self.status == 'sent' and self.delivery_status == 'delivered'

    @property
    def engagement_score(self) -> float:
        """Calculate engagement score (0-100)."""
        score = 0
        if self.email_opened:
            score += 40
        if self.email_clicked:
            score += 30
        if self.lead_responded:
            score += 30
        return score


class ResponseVariable(Base):
    """
    ResponseVariable Model

    Defines available variables for template personalization with type
    information, default values, and extraction logic.
    """
    __tablename__ = "response_variables"

    id = Column(Integer, primary_key=True, index=True)

    # Variable definition
    name = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "lead_name", "company_name"
    display_name = Column(String(200), nullable=False)  # Human-readable name
    description = Column(Text, nullable=True)

    # Type information
    variable_type = Column(String(50), default='text', nullable=False)  # text, number, date, boolean, url, email
    format_hint = Column(String(100), nullable=True)  # e.g., "phone", "currency", "date_short"

    # Default values
    default_value = Column(Text, nullable=True)
    fallback_value = Column(Text, nullable=True)  # Used when data extraction fails

    # Extraction configuration
    source_field = Column(String(100), nullable=True)  # Lead model field to extract from
    source_path = Column(String(255), nullable=True)  # JSON path for nested data
    extraction_function = Column(String(100), nullable=True)  # Custom extraction function name

    # Validation
    required = Column(Boolean, default=False)
    validation_regex = Column(String(500), nullable=True)
    min_length = Column(Integer, nullable=True)
    max_length = Column(Integer, nullable=True)

    # Transformation
    transform = Column(String(50), nullable=True)  # upper, lower, title, capitalize
    truncate_at = Column(Integer, nullable=True)
    sanitize_html = Column(Boolean, default=True)

    # Usage tracking
    usage_count = Column(Integer, default=0)  # How many times used
    last_used_at = Column(DateTime, nullable=True)

    # Categorization
    category = Column(String(100), default='general', index=True)  # general, lead, company, contact, custom
    is_system = Column(Boolean, default=False)  # System variables cannot be deleted
    is_active = Column(Boolean, default=True, index=True)

    # Examples
    example_value = Column(String(500), nullable=True)  # For documentation

    # Metadata
    variable_metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_variable_category_active', 'category', 'is_active'),
    )

    def __repr__(self):
        return f"<ResponseVariable(name='{self.name}', type='{self.variable_type}')>"

    def to_dict(self) -> dict:
        """Convert variable to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'type': self.variable_type,
            'format_hint': self.format_hint,
            'default_value': self.default_value,
            'fallback_value': self.fallback_value,
            'required': self.required,
            'category': self.category,
            'example_value': self.example_value,
            'is_system': self.is_system,
            'is_active': self.is_active,
        }
