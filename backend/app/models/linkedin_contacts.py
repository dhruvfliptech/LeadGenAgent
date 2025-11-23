"""
LinkedIn Contacts Database Models

This module defines SQLAlchemy models for LinkedIn contact import and messaging:
- LinkedInContact: Imported contacts from LinkedIn CSV exports
- LinkedInMessage: Message history and tracking
- LinkedInConnection: OAuth tokens and connection status

These models integrate with the existing leads system while maintaining
LinkedIn-specific metadata and messaging capabilities.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models import Base


class LinkedInContact(Base):
    """
    LinkedIn Contact Model

    Stores contacts imported from LinkedIn CSV exports or added manually.
    Integrates with the leads table for unified contact management.

    CSV Import Fields (LinkedIn Connections.csv):
    - First Name, Last Name
    - Email Address
    - Company
    - Position
    - Connected On
    - Profile URL
    """
    __tablename__ = "linkedin_contacts"

    id = Column(Integer, primary_key=True, index=True)

    # Core Contact Information
    first_name = Column(String(255), nullable=False, index=True)
    last_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), index=True)
    linkedin_url = Column(String(500), unique=True, index=True)

    # Professional Information
    company = Column(String(500))
    position = Column(String(500))
    headline = Column(Text)  # LinkedIn headline
    location = Column(String(255))
    industry = Column(String(255))

    # LinkedIn Metadata
    profile_picture_url = Column(String(1000))
    connected_on = Column(DateTime)  # When connection was made
    mutual_connections_count = Column(Integer, default=0)
    profile_data = Column(JSON)  # Additional LinkedIn profile data

    # Import Tracking
    imported_from = Column(String(50), default='csv')  # csv, manual, api
    import_batch_id = Column(String(100), index=True)  # Group imports together
    csv_filename = Column(String(500))  # Original CSV filename

    # Messaging Status
    last_messaged_at = Column(DateTime)
    total_messages_sent = Column(Integer, default=0)
    last_message_status = Column(String(50))  # sent, delivered, read, failed
    can_message = Column(Boolean, default=True)  # LinkedIn messaging availability

    # Campaign Integration
    lead_id = Column(Integer, ForeignKey('leads.id'), nullable=True, index=True)
    campaign_ids = Column(JSON, default=list)  # List of campaign IDs this contact is part of
    tags = Column(JSON, default=list)  # Custom tags for organization

    # Engagement Tracking
    response_received = Column(Boolean, default=False)
    last_response_at = Column(DateTime)
    engagement_score = Column(Integer, default=0)  # 0-100 engagement score
    notes = Column(Text)  # User notes about this contact

    # Status and Lifecycle
    status = Column(String(50), default='active', index=True)  # active, archived, blocked, bounced
    is_premium = Column(Boolean, default=False)  # LinkedIn Premium member
    unsubscribed = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lead = relationship("Lead", backref="linkedin_contact", foreign_keys=[lead_id])
    messages = relationship("LinkedInMessage", back_populates="contact", cascade="all, delete-orphan")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_linkedin_name', 'first_name', 'last_name'),
        Index('idx_linkedin_company', 'company'),
        Index('idx_linkedin_status', 'status', 'can_message'),
        Index('idx_linkedin_import', 'imported_from', 'import_batch_id'),
    )

    @property
    def full_name(self) -> str:
        """Get full name of contact."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def can_send_message(self) -> bool:
        """Check if contact can receive messages."""
        return (
            self.can_message and
            self.status == 'active' and
            not self.unsubscribed
        )

    def to_dict(self) -> dict:
        """Convert contact to dictionary."""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'linkedin_url': self.linkedin_url,
            'company': self.company,
            'position': self.position,
            'headline': self.headline,
            'location': self.location,
            'industry': self.industry,
            'profile_picture_url': self.profile_picture_url,
            'connected_on': self.connected_on.isoformat() if self.connected_on else None,
            'mutual_connections_count': self.mutual_connections_count,
            'imported_from': self.imported_from,
            'import_batch_id': self.import_batch_id,
            'last_messaged_at': self.last_messaged_at.isoformat() if self.last_messaged_at else None,
            'total_messages_sent': self.total_messages_sent,
            'last_message_status': self.last_message_status,
            'can_message': self.can_message,
            'can_send_message': self.can_send_message,
            'lead_id': self.lead_id,
            'campaign_ids': self.campaign_ids,
            'tags': self.tags,
            'response_received': self.response_received,
            'last_response_at': self.last_response_at.isoformat() if self.last_response_at else None,
            'engagement_score': self.engagement_score,
            'notes': self.notes,
            'status': self.status,
            'is_premium': self.is_premium,
            'unsubscribed': self.unsubscribed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class LinkedInMessage(Base):
    """
    LinkedIn Message Model

    Tracks all messages sent to LinkedIn contacts with delivery status,
    campaign association, and engagement metrics.
    """
    __tablename__ = "linkedin_messages"

    id = Column(Integer, primary_key=True, index=True)

    # Contact Reference
    contact_id = Column(Integer, ForeignKey('linkedin_contacts.id'), nullable=False, index=True)

    # Message Content
    subject = Column(String(500))  # Message subject (if applicable)
    message_content = Column(Text, nullable=False)
    message_type = Column(String(50), default='direct')  # direct, connection_request, inmail

    # LinkedIn Message ID
    linkedin_message_id = Column(String(255), unique=True, index=True)  # LinkedIn API message ID
    conversation_id = Column(String(255), index=True)  # Thread/conversation ID

    # Campaign Integration
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=True, index=True)
    template_id = Column(Integer, nullable=True)  # Message template used

    # Personalization
    personalized_fields = Column(JSON, default=dict)  # Fields used for personalization

    # Delivery and Status
    status = Column(String(50), default='pending', index=True)  # pending, sending, sent, delivered, read, failed, bounced
    sent_at = Column(DateTime, index=True)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    failed_at = Column(DateTime)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Engagement Tracking
    replied = Column(Boolean, default=False)
    reply_at = Column(DateTime)
    reply_content = Column(Text)
    clicked_link = Column(Boolean, default=False)
    click_count = Column(Integer, default=0)

    # Rate Limiting and Queue
    scheduled_for = Column(DateTime, index=True)  # When message should be sent
    priority = Column(Integer, default=0)  # Higher priority = sent first
    rate_limit_group = Column(String(100))  # Group for rate limiting

    # Metadata
    user_agent = Column(String(500))  # If sent via browser automation
    ip_address = Column(String(50))
    contact_metadata = Column(JSON, default=dict)  # Additional metadata

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contact = relationship("LinkedInContact", back_populates="messages")
    campaign = relationship("Campaign", backref="linkedin_messages", foreign_keys=[campaign_id])

    # Indexes for analytics queries
    __table_args__ = (
        Index('idx_message_status_date', 'status', 'created_at'),
        Index('idx_message_campaign', 'campaign_id', 'status'),
        Index('idx_message_scheduled', 'scheduled_for', 'status'),
    )

    def to_dict(self) -> dict:
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'subject': self.subject,
            'message_content': self.message_content,
            'message_type': self.message_type,
            'linkedin_message_id': self.linkedin_message_id,
            'conversation_id': self.conversation_id,
            'campaign_id': self.campaign_id,
            'template_id': self.template_id,
            'status': self.status,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'replied': self.replied,
            'reply_at': self.reply_at.isoformat() if self.reply_at else None,
            'reply_content': self.reply_content,
            'clicked_link': self.clicked_link,
            'click_count': self.click_count,
            'scheduled_for': self.scheduled_for.isoformat() if self.scheduled_for else None,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class LinkedInConnection(Base):
    """
    LinkedIn OAuth Connection Model

    Stores OAuth tokens and connection status for LinkedIn API access.
    Supports multiple user accounts and token refresh.
    """
    __tablename__ = "linkedin_connections"

    id = Column(Integer, primary_key=True, index=True)

    # User/Account Information
    user_id = Column(Integer, nullable=True, index=True)  # Link to app user if applicable
    account_name = Column(String(255))  # Friendly name for this connection
    linkedin_user_id = Column(String(255), unique=True, index=True)  # LinkedIn user ID

    # LinkedIn Profile Info
    profile_email = Column(String(255))
    profile_name = Column(String(500))
    profile_picture_url = Column(String(1000))
    profile_url = Column(String(500))

    # OAuth Tokens (should be encrypted in production)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    token_type = Column(String(50), default='Bearer')
    expires_at = Column(DateTime)
    scope = Column(String(500))  # Granted scopes

    # Connection Status
    is_active = Column(Boolean, default=True, index=True)
    is_valid = Column(Boolean, default=True)  # Token is valid
    last_validated_at = Column(DateTime)

    # Rate Limiting Tracking
    daily_messages_sent = Column(Integer, default=0)
    daily_limit_reset_at = Column(DateTime)
    rate_limit_exceeded = Column(Boolean, default=False)

    # Usage Statistics
    total_messages_sent = Column(Integer, default=0)
    total_connections_imported = Column(Integer, default=0)
    last_used_at = Column(DateTime)

    # Error Tracking
    last_error = Column(Text)
    error_count = Column(Integer, default=0)

    # Metadata
    connection_metadata = Column(JSON, default=dict)

    # Timestamps
    connected_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_connection_active', 'is_active', 'is_valid'),
    )

    @property
    def is_token_expired(self) -> bool:
        """Check if access token is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at

    @property
    def can_send_messages(self) -> bool:
        """Check if connection can send messages."""
        return (
            self.is_active and
            self.is_valid and
            not self.is_token_expired and
            not self.rate_limit_exceeded
        )

    @property
    def messages_remaining_today(self) -> int:
        """Calculate remaining messages for today."""
        from app.core.config import settings
        daily_limit = getattr(settings, 'LINKEDIN_DAILY_MESSAGE_LIMIT', 100)

        # Reset counter if past reset time
        if self.daily_limit_reset_at and datetime.utcnow() >= self.daily_limit_reset_at:
            return daily_limit

        return max(0, daily_limit - self.daily_messages_sent)

    def to_dict(self) -> dict:
        """Convert connection to dictionary (excluding sensitive tokens)."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_name': self.account_name,
            'linkedin_user_id': self.linkedin_user_id,
            'profile_email': self.profile_email,
            'profile_name': self.profile_name,
            'profile_picture_url': self.profile_picture_url,
            'profile_url': self.profile_url,
            'is_active': self.is_active,
            'is_valid': self.is_valid,
            'is_token_expired': self.is_token_expired,
            'can_send_messages': self.can_send_messages,
            'last_validated_at': self.last_validated_at.isoformat() if self.last_validated_at else None,
            'daily_messages_sent': self.daily_messages_sent,
            'messages_remaining_today': self.messages_remaining_today,
            'rate_limit_exceeded': self.rate_limit_exceeded,
            'total_messages_sent': self.total_messages_sent,
            'total_connections_imported': self.total_connections_imported,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'last_error': self.last_error,
            'error_count': self.error_count,
            'connected_at': self.connected_at.isoformat() if self.connected_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
