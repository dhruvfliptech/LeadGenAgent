"""
Webhook queue models for reliable webhook delivery.

This module provides models for queuing, tracking, and logging webhook
deliveries to ensure reliable communication with external services like n8n.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Text, Float, Index
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from app.models import Base
import enum


class WebhookStatus(str, enum.Enum):
    """Webhook delivery status."""
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WebhookDirection(str, enum.Enum):
    """Webhook direction."""
    OUTGOING = "outgoing"
    INCOMING = "incoming"


class WebhookQueueItem(Base):
    """
    WebhookQueueItem model for queuing webhooks with retry logic.

    This model stores webhooks that need to be delivered to external services,
    with support for retries, prioritization, and error tracking.
    """

    __tablename__ = "webhook_queue"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Webhook destination
    webhook_url = Column(String(500), nullable=False, index=True)

    # Webhook payload and headers
    payload = Column(JSON, nullable=False)
    headers = Column(JSON, nullable=True)  # Custom headers to include

    # Webhook type/event
    event_type = Column(String(100), nullable=False, index=True)
    # Event types: lead_scraped, demo_completed, video_completed, email_sent, lead_responded

    # Entity tracking (for reference)
    entity_type = Column(String(50), nullable=True, index=True)  # lead, demo_site, video, email
    entity_id = Column(Integer, nullable=True, index=True)

    # Delivery status
    status = Column(String(50), default="pending", nullable=False, index=True)
    # Status values: pending, sending, sent, failed, cancelled

    # Retry logic
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    next_retry_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Priority (higher = more important)
    priority = Column(Integer, default=0, nullable=False, index=True)

    # Error tracking
    last_error = Column(String(1000), nullable=True)
    error_details = Column(JSON, nullable=True)  # Detailed error information

    # Response tracking
    response_status = Column(Integer, nullable=True)  # HTTP status code
    response_body = Column(Text, nullable=True)  # Response body
    response_time_ms = Column(Integer, nullable=True)  # Response time in milliseconds

    # Security
    signature = Column(String(255), nullable=True)  # HMAC signature for security

    # Metadata
    queue_metadata = Column(JSON, nullable=True)  # Additional metadata

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True, index=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)

    # Indexes for query performance
    __table_args__ = (
        Index('idx_webhook_queue_processing', 'status', 'priority', 'next_retry_at'),
        Index('idx_webhook_queue_entity', 'entity_type', 'entity_id'),
    )

    def __repr__(self):
        return f"<WebhookQueueItem(id={self.id}, event_type='{self.event_type}', status='{self.status}', retry_count={self.retry_count})>"

    def to_dict(self):
        """Convert webhook queue item to dictionary for API responses."""
        return {
            'id': self.id,
            'webhook_url': self.webhook_url,
            'event_type': self.event_type,
            'entity': {
                'type': self.entity_type,
                'id': self.entity_id
            },
            'status': self.status,
            'retry': {
                'retry_count': self.retry_count,
                'max_retries': self.max_retries,
                'next_retry_at': self.next_retry_at.isoformat() if self.next_retry_at else None
            },
            'priority': self.priority,
            'error': {
                'last_error': self.last_error,
                'error_details': self.error_details
            } if self.last_error else None,
            'response': {
                'status': self.response_status,
                'time_ms': self.response_time_ms
            } if self.response_status else None,
            'timestamps': {
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'sent_at': self.sent_at.isoformat() if self.sent_at else None,
                'failed_at': self.failed_at.isoformat() if self.failed_at else None
            },
            'metadata': self.metadata or {}
        }

    def should_retry(self) -> bool:
        """Check if webhook should be retried."""
        return (
            self.status in ["pending", "failed"] and
            self.retry_count < self.max_retries and
            (self.next_retry_at is None or self.next_retry_at <= datetime.utcnow())
        )

    def calculate_next_retry(self, retry_delays: list = None) -> datetime:
        """Calculate next retry time with exponential backoff."""
        if retry_delays is None:
            retry_delays = [5, 30, 300]  # 5s, 30s, 5m

        delay_index = min(self.retry_count, len(retry_delays) - 1)
        delay_seconds = retry_delays[delay_index]

        return datetime.utcnow() + timedelta(seconds=delay_seconds)


class WebhookLog(Base):
    """
    WebhookLog model for tracking all webhook activity.

    This model provides a comprehensive audit log of all webhook
    communications (both incoming and outgoing) for debugging and monitoring.
    """

    __tablename__ = "webhook_logs"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Direction and type
    direction = Column(String(20), nullable=False, index=True)  # incoming, outgoing
    event_type = Column(String(100), nullable=True, index=True)

    # Request details
    webhook_url = Column(String(500), nullable=True, index=True)
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE
    headers = Column(JSON, nullable=True)
    payload = Column(JSON, nullable=True)

    # Response details
    response_status = Column(Integer, nullable=True, index=True)
    response_headers = Column(JSON, nullable=True)
    response_body = Column(JSON, nullable=True)

    # Performance metrics
    duration_ms = Column(Integer, nullable=True)  # Total request duration

    # Error tracking
    error_message = Column(String(1000), nullable=True)
    error_details = Column(JSON, nullable=True)

    # Security
    signature_valid = Column(Boolean, nullable=True)  # For incoming webhooks
    signature = Column(String(255), nullable=True)  # Signature used/received

    # Entity tracking (for reference)
    entity_type = Column(String(50), nullable=True, index=True)
    entity_id = Column(Integer, nullable=True, index=True)

    # Queue reference (for outgoing webhooks)
    webhook_queue_id = Column(Integer, nullable=True, index=True)

    # Source tracking
    source_ip = Column(String(45), nullable=True)  # For incoming webhooks (IPv4/IPv6)
    user_agent = Column(String(255), nullable=True)  # For incoming webhooks

    # Metadata
    log_metadata = Column(JSON, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Indexes for query performance
    __table_args__ = (
        Index('idx_webhook_logs_lookup', 'direction', 'event_type', 'created_at'),
        Index('idx_webhook_logs_entity', 'entity_type', 'entity_id'),
        Index('idx_webhook_logs_queue', 'webhook_queue_id'),
        Index('idx_webhook_logs_status', 'response_status', 'created_at'),
    )

    def __repr__(self):
        return f"<WebhookLog(id={self.id}, direction='{self.direction}', event_type='{self.event_type}', status={self.response_status})>"

    def to_dict(self):
        """Convert webhook log to dictionary for API responses."""
        return {
            'id': self.id,
            'direction': self.direction,
            'event_type': self.event_type,
            'request': {
                'webhook_url': self.webhook_url,
                'method': self.method,
                'headers': self.headers,
                'payload': self.payload
            },
            'response': {
                'status': self.response_status,
                'headers': self.response_headers,
                'body': self.response_body
            } if self.response_status else None,
            'performance': {
                'duration_ms': self.duration_ms
            },
            'error': {
                'message': self.error_message,
                'details': self.error_details
            } if self.error_message else None,
            'security': {
                'signature_valid': self.signature_valid,
                'signature': self.signature
            } if self.signature else None,
            'entity': {
                'type': self.entity_type,
                'id': self.entity_id
            } if self.entity_type else None,
            'source': {
                'ip': self.source_ip,
                'user_agent': self.user_agent
            } if self.source_ip else None,
            'webhook_queue_id': self.webhook_queue_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'metadata': self.metadata or {}
        }

    @property
    def is_success(self) -> bool:
        """Check if webhook was successful."""
        return self.response_status is not None and 200 <= self.response_status < 300

    @property
    def is_error(self) -> bool:
        """Check if webhook had an error."""
        return self.error_message is not None or (
            self.response_status is not None and self.response_status >= 400
        )


class WebhookRetryHistory(Base):
    """
    WebhookRetryHistory model for tracking retry attempts.

    This model provides detailed history of each retry attempt for debugging
    and monitoring webhook reliability.
    """

    __tablename__ = "webhook_retry_history"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Reference to webhook queue item
    webhook_queue_id = Column(Integer, nullable=False, index=True)

    # Retry attempt number
    attempt_number = Column(Integer, nullable=False)

    # Attempt details
    status = Column(String(50), nullable=False)  # sent, failed
    error_message = Column(String(1000), nullable=True)
    response_status = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    # Timestamp
    attempted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Indexes
    __table_args__ = (
        Index('idx_webhook_retry_queue', 'webhook_queue_id', 'attempted_at'),
    )

    def __repr__(self):
        return f"<WebhookRetryHistory(id={self.id}, webhook_queue_id={self.webhook_queue_id}, attempt={self.attempt_number}, status='{self.status}')>"

    def to_dict(self):
        """Convert retry history to dictionary."""
        return {
            'id': self.id,
            'webhook_queue_id': self.webhook_queue_id,
            'attempt_number': self.attempt_number,
            'status': self.status,
            'error_message': self.error_message,
            'response_status': self.response_status,
            'response_time_ms': self.response_time_ms,
            'attempted_at': self.attempted_at.isoformat() if self.attempted_at else None
        }
