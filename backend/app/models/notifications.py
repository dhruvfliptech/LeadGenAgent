"""
Notification models for real-time alerts and messaging.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base
from enum import Enum
from typing import Dict, Any, List


class NotificationType(str, Enum):
    """Types of notifications."""
    NEW_LEAD = "new_lead"
    HIGH_QUALITY_LEAD = "high_quality_lead"
    AUTO_RESPONSE_SENT = "auto_response_sent"
    AUTO_RESPONSE_REPLIED = "auto_response_replied"
    SCHEDULE_SUCCESS = "schedule_success"
    SCHEDULE_FAILURE = "schedule_failure"
    SYSTEM_ALERT = "system_alert"
    RULE_TRIGGERED = "rule_triggered"
    EXPORT_READY = "export_ready"


class NotificationChannel(str, Enum):
    """Available notification channels."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    SMS = "sms"
    WEBSOCKET = "websocket"
    PUSH = "push"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationPreference(Base):
    """User notification preferences."""
    
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User identification (for future user system)
    user_id = Column(String(50), nullable=False, index=True)  # Can be email or user ID
    
    # Notification type preferences
    notification_type = Column(String(50), nullable=False, index=True)  # NotificationType
    enabled = Column(Boolean, default=True, nullable=False)
    
    # Channel preferences
    channels = Column(JSON, nullable=False)  # List of enabled channels
    priority_threshold = Column(String(20), default="normal", nullable=False)  # NotificationPriority
    
    # Timing preferences
    quiet_hours_enabled = Column(Boolean, default=False, nullable=False)
    quiet_start_hour = Column(Integer, default=22, nullable=False)  # 10 PM
    quiet_end_hour = Column(Integer, default=8, nullable=False)  # 8 AM
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # Frequency limits
    max_per_hour = Column(Integer, nullable=True)
    max_per_day = Column(Integer, nullable=True)
    digest_enabled = Column(Boolean, default=False, nullable=False)
    digest_frequency_hours = Column(Integer, default=24, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<NotificationPreference(id={self.id}, user='{self.user_id}', type='{self.notification_type}')>"


class NotificationChannel(Base):
    """Notification channel configurations."""
    
    __tablename__ = "notification_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Channel metadata
    name = Column(String(255), nullable=False, index=True)
    channel_type = Column(String(50), nullable=False, index=True)  # NotificationChannel
    description = Column(Text, nullable=True)
    
    # Channel configuration
    is_active = Column(Boolean, default=True, nullable=False)
    configuration = Column(JSON, nullable=False)  # Channel-specific config
    
    # Authentication/credentials (encrypted)
    credentials = Column(JSON, nullable=True)  # Encrypted credentials
    webhook_url = Column(String(500), nullable=True)
    api_key_encrypted = Column(Text, nullable=True)
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60, nullable=False)
    rate_limit_per_hour = Column(Integer, default=1000, nullable=False)
    
    # Performance tracking
    total_sent = Column(Integer, default=0, nullable=False)
    successful_sent = Column(Integer, default=0, nullable=False)
    failed_sent = Column(Integer, default=0, nullable=False)
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error tracking
    consecutive_failures = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    is_healthy = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_sent == 0:
            return 0.0
        return (self.successful_sent / self.total_sent) * 100
    
    def __repr__(self):
        return f"<NotificationChannel(id={self.id}, name='{self.name}', type='{self.channel_type}')>"


class Notification(Base):
    """Individual notification record."""
    
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Notification metadata
    notification_type = Column(String(50), nullable=False, index=True)  # NotificationType
    priority = Column(String(20), default="normal", nullable=False, index=True)  # NotificationPriority
    
    # Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # Additional data for the notification
    
    # Targeting
    user_id = Column(String(50), nullable=True, index=True)  # Specific user
    broadcast = Column(Boolean, default=False, nullable=False)  # Send to all users
    
    # Source tracking
    source_type = Column(String(50), nullable=True)  # lead, schedule, system
    source_id = Column(Integer, nullable=True)  # ID of the source object
    
    # Delivery settings
    channels = Column(JSON, nullable=False)  # Channels to send to
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status tracking
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, sent, failed, expired
    sent_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type='{self.notification_type}', status='{self.status}')>"


class NotificationDelivery(Base):
    """Delivery tracking for notifications across channels."""
    
    __tablename__ = "notification_deliveries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("notification_channels.id"), nullable=False, index=True)
    
    # Delivery details
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, sent, failed, delivered, read
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Channel-specific data
    external_id = Column(String(255), nullable=True)  # ID from external service
    response_data = Column(JSON, nullable=True)  # Response from channel API
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Performance tracking
    delivery_time_ms = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    notification = relationship("Notification", backref="deliveries")
    channel = relationship("NotificationChannel", backref="deliveries")
    
    def __repr__(self):
        return f"<NotificationDelivery(id={self.id}, notification_id={self.notification_id}, status='{self.status}')>"


class NotificationTemplate(Base):
    """Templates for notification messages."""
    
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Template metadata
    name = Column(String(255), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False, index=True)  # NotificationType
    channel_type = Column(String(50), nullable=False, index=True)  # NotificationChannel
    
    # Template content
    title_template = Column(String(255), nullable=False)
    message_template = Column(Text, nullable=False)
    variables = Column(JSON, nullable=True)  # Available template variables
    
    # Channel-specific formatting
    format_config = Column(JSON, nullable=True)  # Channel-specific formatting options
    
    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<NotificationTemplate(id={self.id}, name='{self.name}', type='{self.notification_type}')>"


class NotificationDigest(Base):
    """Digest notifications for batch delivery."""
    
    __tablename__ = "notification_digests"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Digest metadata
    user_id = Column(String(50), nullable=False, index=True)
    digest_type = Column(String(50), nullable=False, index=True)  # daily, weekly, custom
    
    # Content
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    notification_count = Column(Integer, nullable=False)
    notification_ids = Column(JSON, nullable=False)  # List of notification IDs in digest
    
    # Timing
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    
    # Delivery
    status = Column(String(50), default="pending", nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    channels = Column(JSON, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<NotificationDigest(id={self.id}, user='{self.user_id}', count={self.notification_count})>"


class WebSocketConnection(Base):
    """Active WebSocket connections for real-time notifications."""
    
    __tablename__ = "websocket_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Connection details
    connection_id = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    
    # Connection metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(String(500), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_ping_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    connected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    disconnected_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<WebSocketConnection(id={self.id}, connection_id='{self.connection_id}', user='{self.user_id}')>"