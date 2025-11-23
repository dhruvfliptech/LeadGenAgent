"""
Approval Workflow models for human-in-the-loop response review.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base


class ResponseApproval(Base):
    """Model for tracking response approvals and modifications."""
    
    __tablename__ = "response_approvals"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Lead and Template references
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("response_templates.id"), nullable=True)
    
    # Generated response
    generated_subject = Column(String(500), nullable=True)
    generated_body = Column(Text, nullable=False)
    
    # Modified response (if edited)
    modified_subject = Column(String(500), nullable=True)
    modified_body = Column(Text, nullable=True)
    
    # Approval status
    status = Column(String(50), default="pending")  # pending, approved, rejected, sent
    approval_method = Column(String(50), nullable=True)  # slack, web, api, auto
    
    # Reviewer information
    reviewer_id = Column(String(100), nullable=True)  # Slack user ID or email
    reviewer_name = Column(String(255), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Scoring from reviewer
    quality_score = Column(Float, nullable=True)  # 1-5 rating
    relevance_score = Column(Float, nullable=True)  # 1-5 rating
    
    # Auto-approval criteria
    auto_approval_score = Column(Float, nullable=True)
    auto_approval_reason = Column(Text, nullable=True)
    
    # Notification settings
    slack_channel = Column(String(100), nullable=True)
    slack_message_ts = Column(String(100), nullable=True)  # Slack message timestamp
    notification_sent = Column(Boolean, default=False)
    
    # Response tracking
    response_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivery_status = Column(String(50), nullable=True)  # delivered, bounced, failed
    
    # Metadata
    variables_used = Column(JSON, nullable=True)
    generation_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    lead = relationship("Lead", backref="approvals")
    
    def __repr__(self):
        return f"<ResponseApproval(id={self.id}, lead_id={self.lead_id}, status='{self.status}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'template_id': self.template_id,
            'generated_subject': self.generated_subject,
            'generated_body': self.generated_body,
            'modified_subject': self.modified_subject,
            'modified_body': self.modified_body,
            'status': self.status,
            'approval_method': self.approval_method,
            'reviewer': {
                'id': self.reviewer_id,
                'name': self.reviewer_name,
                'notes': self.review_notes
            },
            'scores': {
                'quality': self.quality_score,
                'relevance': self.relevance_score,
                'auto_approval': self.auto_approval_score
            },
            'slack': {
                'channel': self.slack_channel,
                'message_ts': self.slack_message_ts,
                'notification_sent': self.notification_sent
            },
            'delivery': {
                'sent': self.response_sent,
                'sent_at': self.sent_at.isoformat() if self.sent_at else None,
                'status': self.delivery_status
            },
            'metadata': {
                'variables_used': self.variables_used,
                'generation': self.generation_metadata
            },
            'timestamps': {
                'created': self.created_at.isoformat() if self.created_at else None,
                'reviewed': self.reviewed_at.isoformat() if self.reviewed_at else None,
                'updated': self.updated_at.isoformat() if self.updated_at else None
            }
        }


class ApprovalRule(Base):
    """Model for defining auto-approval rules."""
    
    __tablename__ = "approval_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Rule conditions
    min_qualification_score = Column(Float, nullable=True)
    required_keywords = Column(JSON, nullable=True)  # List of keywords
    excluded_keywords = Column(JSON, nullable=True)  # List of keywords
    
    # Lead criteria
    lead_categories = Column(JSON, nullable=True)  # List of categories
    compensation_min = Column(Float, nullable=True)
    compensation_max = Column(Float, nullable=True)
    
    # Template criteria
    template_types = Column(JSON, nullable=True)  # List of template types
    
    # Auto-approval settings
    auto_approve = Column(Boolean, default=False)
    auto_approve_threshold = Column(Float, default=0.9)
    
    # Notification settings
    require_slack_review = Column(Boolean, default=True)
    slack_channels = Column(JSON, nullable=True)  # List of channels
    notification_priority = Column(String(50), default="normal")  # low, normal, high, urgent
    
    # Rule configuration
    priority = Column(Integer, default=0)  # Higher priority rules evaluated first
    is_active = Column(Boolean, default=True)
    
    # Statistics
    times_triggered = Column(Integer, default=0)
    auto_approved_count = Column(Integer, default=0)
    manual_review_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ApprovalRule(id={self.id}, name='{self.name}', auto_approve={self.auto_approve})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'conditions': {
                'min_qualification_score': self.min_qualification_score,
                'required_keywords': self.required_keywords,
                'excluded_keywords': self.excluded_keywords,
                'lead_categories': self.lead_categories,
                'compensation_range': {
                    'min': self.compensation_min,
                    'max': self.compensation_max
                },
                'template_types': self.template_types
            },
            'approval': {
                'auto_approve': self.auto_approve,
                'threshold': self.auto_approve_threshold
            },
            'notifications': {
                'require_slack': self.require_slack_review,
                'channels': self.slack_channels,
                'priority': self.notification_priority
            },
            'configuration': {
                'priority': self.priority,
                'is_active': self.is_active
            },
            'statistics': {
                'times_triggered': self.times_triggered,
                'auto_approved': self.auto_approved_count,
                'manual_review': self.manual_review_count
            },
            'timestamps': {
                'created': self.created_at.isoformat() if self.created_at else None,
                'updated': self.updated_at.isoformat() if self.updated_at else None
            }
        }


class ApprovalQueue(Base):
    """Model for managing the approval queue."""

    __tablename__ = "approval_queue"

    id = Column(Integer, primary_key=True, index=True)
    approval_id = Column(Integer, ForeignKey("response_approvals.id"), nullable=False)

    # Queue management
    priority = Column(String(50), default="normal")  # low, normal, high, urgent
    queue_position = Column(Integer, nullable=True)

    # Assignment
    assigned_to = Column(String(100), nullable=True)  # Slack user ID or email
    assigned_at = Column(DateTime(timezone=True), nullable=True)

    # SLA tracking
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    sla_status = Column(String(50), default="on_track")  # on_track, at_risk, breached

    # Reminder settings
    reminder_sent = Column(Boolean, default=False)
    reminder_count = Column(Integer, default=0)
    last_reminder_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    status = Column(String(50), default="queued")  # queued, in_review, completed, expired

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    approval = relationship("ResponseApproval", backref="queue_entry")

    def __repr__(self):
        return f"<ApprovalQueue(id={self.id}, approval_id={self.approval_id}, status='{self.status}')>"


class ApprovalHistory(Base):
    """Model for tracking approval history and audit trail."""

    __tablename__ = "approval_history"

    id = Column(Integer, primary_key=True, index=True)
    approval_request_id = Column(Integer, ForeignKey("response_approvals.id"), nullable=False, index=True)

    # Action details
    action = Column(String(100), nullable=False)  # created, assigned, reviewed, approved, rejected, modified, escalated
    actor_email = Column(String(255), nullable=True)
    actor_name = Column(String(255), nullable=True)

    # Action data
    action_data = Column(JSON, nullable=True)  # Additional context for the action

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    approval = relationship("ResponseApproval", backref="history")

    def __repr__(self):
        return f"<ApprovalHistory(id={self.id}, action='{self.action}', actor='{self.actor_email}')>"