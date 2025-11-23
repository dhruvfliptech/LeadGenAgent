"""
Campaign Management Models for Email Campaigns.
"""

from sqlalchemy import Column, Integer, String, VARCHAR, Boolean, DateTime, Text, ForeignKey, Float, JSON, TIMESTAMP
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base


class Campaign(Base):
    """Email campaign model for managing campaign execution and metrics."""

    __tablename__ = "campaigns"

    # Primary identifiers
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(VARCHAR(100), unique=True, nullable=False, index=True)

    # Campaign details
    name = Column(VARCHAR(255), nullable=False, index=True)
    template_id = Column(Integer, nullable=True)
    status = Column(VARCHAR(50), default='draft', nullable=False, index=True)
    # Status values: draft, scheduled, running, paused, completed, failed

    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Campaign metrics
    total_recipients = Column(Integer, default=0, nullable=False)
    emails_sent = Column(Integer, default=0, nullable=False)
    emails_opened = Column(Integer, default=0, nullable=False)
    emails_clicked = Column(Integer, default=0, nullable=False)
    emails_replied = Column(Integer, default=0, nullable=False)
    emails_bounced = Column(Integer, default=0, nullable=False)

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    recipients = relationship("CampaignRecipient", back_populates="campaign", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])

    # Computed properties
    @property
    def open_rate(self):
        """Calculate email open rate."""
        if self.emails_sent == 0:
            return 0.0
        return (self.emails_opened / self.emails_sent) * 100

    @property
    def click_rate(self):
        """Calculate email click rate."""
        if self.emails_sent == 0:
            return 0.0
        return (self.emails_clicked / self.emails_sent) * 100

    @property
    def reply_rate(self):
        """Calculate email reply rate."""
        if self.emails_sent == 0:
            return 0.0
        return (self.emails_replied / self.emails_sent) * 100

    @property
    def bounce_rate(self):
        """Calculate email bounce rate."""
        if self.emails_sent == 0:
            return 0.0
        return (self.emails_bounced / self.emails_sent) * 100

    def __repr__(self):
        return f"<Campaign(id={self.id}, campaign_id='{self.campaign_id}', name='{self.name}', status='{self.status}')>"

    def to_dict(self):
        """Convert campaign to dictionary for API responses."""
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'name': self.name,
            'template_id': self.template_id,
            'status': self.status,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_recipients': self.total_recipients,
            'metrics': {
                'emails_sent': self.emails_sent,
                'emails_opened': self.emails_opened,
                'emails_clicked': self.emails_clicked,
                'emails_replied': self.emails_replied,
                'emails_bounced': self.emails_bounced,
                'open_rate': round(self.open_rate, 2),
                'click_rate': round(self.click_rate, 2),
                'reply_rate': round(self.reply_rate, 2),
                'bounce_rate': round(self.bounce_rate, 2),
            },
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class CampaignRecipient(Base):
    """Recipient tracking for campaign emails with event timestamps."""

    __tablename__ = "campaign_recipients"

    # Primary identifiers
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)

    # Contact information (cached for historical accuracy)
    email_address = Column(VARCHAR(255), nullable=False, index=True)

    # Recipient status and tracking
    status = Column(VARCHAR(50), default='pending', nullable=False, index=True)
    # Status values: pending, queued, sent, failed, bounced, unsubscribed

    # Event timestamps
    sent_at = Column(DateTime(timezone=True), nullable=True, index=True)
    opened_at = Column(DateTime(timezone=True), nullable=True, index=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True, index=True)
    replied_at = Column(DateTime(timezone=True), nullable=True, index=True)
    bounced_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    campaign = relationship("Campaign", back_populates="recipients")
    tracking_events = relationship("EmailTracking", back_populates="recipient", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CampaignRecipient(id={self.id}, campaign_id={self.campaign_id}, email='{self.email_address}', status='{self.status}')>"

    def to_dict(self):
        """Convert recipient to dictionary for API responses."""
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'lead_id': self.lead_id,
            'email_address': self.email_address,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'replied_at': self.replied_at.isoformat() if self.replied_at else None,
            'bounced_at': self.bounced_at.isoformat() if self.bounced_at else None,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class EmailTracking(Base):
    """Granular email event tracking for opens, clicks, and bounces."""

    __tablename__ = "email_tracking"

    # Primary identifiers
    id = Column(Integer, primary_key=True, index=True)
    campaign_recipient_id = Column(Integer, ForeignKey("campaign_recipients.id"), nullable=False, index=True)

    # Event information
    event_type = Column(VARCHAR(50), nullable=False, index=True)
    # Event types: open, click, bounce, reply, forward, unsubscribe, complain
    event_data = Column(JSON, nullable=True)  # Flexible data storage for event details

    # Client information
    user_agent = Column(Text, nullable=True)
    ip_address = Column(INET, nullable=True, index=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    recipient = relationship("CampaignRecipient", back_populates="tracking_events")

    def __repr__(self):
        return f"<EmailTracking(id={self.id}, recipient_id={self.campaign_recipient_id}, event='{self.event_type}')>"

    def to_dict(self):
        """Convert tracking event to dictionary for API responses."""
        return {
            'id': self.id,
            'campaign_recipient_id': self.campaign_recipient_id,
            'event_type': self.event_type,
            'event_data': self.event_data or {},
            'user_agent': self.user_agent,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
