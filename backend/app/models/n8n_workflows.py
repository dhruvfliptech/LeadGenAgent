"""
N8N Workflow Automation Models

Comprehensive database models for N8N workflow integration including:
- Workflow configuration and management
- Execution tracking with status and logs
- Approval system (manual and auto-approval)
- Webhook queue for async processing
- Monitoring events and error tracking
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    Float,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
import enum

from app.models.base import Base


class WorkflowStatus(str, enum.Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ApprovalStatus(str, enum.Enum):
    """Approval request status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalPriority(str, enum.Enum):
    """Approval priority levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class QueueStatus(str, enum.Enum):
    """Webhook queue status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MonitoringSeverity(str, enum.Enum):
    """Monitoring event severity"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class N8NWorkflow(Base):
    """
    N8N Workflow Configuration

    Stores configuration for N8N workflows that can be triggered
    from the backend or via webhooks.
    """
    __tablename__ = "n8n_workflows"

    id = Column(Integer, primary_key=True, index=True)
    workflow_name = Column(String(255), nullable=False, unique=True, index=True)
    workflow_description = Column(Text, nullable=True)

    # N8N integration
    n8n_workflow_id = Column(String(100), nullable=True, index=True)
    webhook_url = Column(String(500), nullable=True)
    webhook_secret = Column(String(255), nullable=True)

    # Trigger configuration
    trigger_events = Column(JSONB, nullable=True, default=list)  # List of events that trigger this workflow
    trigger_conditions = Column(JSONB, nullable=True, default=dict)  # Conditions to evaluate before triggering

    # Workflow settings
    is_active = Column(Boolean, default=True, index=True)
    requires_approval = Column(Boolean, default=False)
    auto_approval_enabled = Column(Boolean, default=False)
    timeout_seconds = Column(Integer, default=300)
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)

    # Metadata
    tags = Column(JSONB, nullable=True, default=list)
    config_data = Column(JSONB, nullable=True, default=dict)  # Additional configuration

    # Statistics
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_executed_at = Column(DateTime, nullable=True)
    average_duration_seconds = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    monitoring_events = relationship("WorkflowMonitoring", back_populates="workflow", cascade="all, delete-orphan")
    webhook_queue = relationship("WebhookQueue", back_populates="workflow", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_n8n_workflows_active', 'is_active', 'created_at'),
        Index('idx_n8n_workflows_execution', 'execution_count', 'last_executed_at'),
    )

    def __repr__(self) -> str:
        return f"<N8NWorkflow(id={self.id}, name='{self.workflow_name}', active={self.is_active})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "workflow_name": self.workflow_name,
            "workflow_description": self.workflow_description,
            "n8n_workflow_id": self.n8n_workflow_id,
            "webhook_url": self.webhook_url,
            "trigger_events": self.trigger_events,
            "is_active": self.is_active,
            "requires_approval": self.requires_approval,
            "auto_approval_enabled": self.auto_approval_enabled,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_executed_at": self.last_executed_at.isoformat() if self.last_executed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WorkflowExecution(Base):
    """
    Workflow Execution Records

    Tracks individual workflow executions with input/output data,
    status, and execution logs.
    """
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("n8n_workflows.id", ondelete="CASCADE"), nullable=False, index=True)

    # Execution details
    n8n_execution_id = Column(String(100), nullable=True, index=True)
    trigger_event = Column(String(255), nullable=True, index=True)
    trigger_source = Column(String(100), nullable=True)  # manual, webhook, scheduled, event

    # Data
    input_data = Column(JSONB, nullable=True, default=dict)
    output_data = Column(JSONB, nullable=True, default=dict)
    execution_log = Column(Text, nullable=True)

    # Status tracking
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING, nullable=False, index=True)
    progress_percentage = Column(Integer, default=0)
    current_step = Column(String(255), nullable=True)

    # Timing
    duration_seconds = Column(Float, nullable=True)
    started_at = Column(DateTime, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)
    retry_count = Column(Integer, default=0)
    is_retryable = Column(Boolean, default=True)

    # Metadata
    workflow_metadata = Column(JSONB, nullable=True, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    workflow = relationship("N8NWorkflow", back_populates="executions")
    approvals = relationship("WorkflowApproval", back_populates="execution", cascade="all, delete-orphan")
    monitoring_events = relationship("WorkflowMonitoring", back_populates="execution", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_workflow_executions_status_created', 'status', 'created_at'),
        Index('idx_workflow_executions_workflow_status', 'workflow_id', 'status'),
    )

    def __repr__(self) -> str:
        return f"<WorkflowExecution(id={self.id}, workflow_id={self.workflow_id}, status={self.status})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "n8n_execution_id": self.n8n_execution_id,
            "trigger_event": self.trigger_event,
            "status": self.status.value,
            "progress_percentage": self.progress_percentage,
            "current_step": self.current_step,
            "duration_seconds": self.duration_seconds,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WorkflowApproval(Base):
    """
    Workflow Approval Requests

    Manages approval gates for workflows requiring human approval
    or AI-powered auto-approval.
    """
    __tablename__ = "workflow_approvals"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Approval details
    approval_type = Column(String(100), nullable=False, index=True)  # email_send, video_create, demo_deploy, etc.
    approval_title = Column(String(255), nullable=False)
    approval_description = Column(Text, nullable=True)
    approval_data = Column(JSONB, nullable=True, default=dict)

    # Status
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False, index=True)
    priority = Column(Enum(ApprovalPriority), default=ApprovalPriority.MEDIUM, nullable=False, index=True)

    # Approval decision
    approver_id = Column(Integer, nullable=True)  # User ID who approved/rejected
    approver_name = Column(String(255), nullable=True)
    approval_reason = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Auto-approval
    requires_manual = Column(Boolean, default=False)
    auto_approval_enabled = Column(Boolean, default=True)
    auto_approval_confidence = Column(Float, nullable=True)  # 0-100 confidence score
    auto_approval_reason = Column(Text, nullable=True)

    # Timeout
    expires_at = Column(DateTime, nullable=True, index=True)

    # Notifications
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    execution = relationship("WorkflowExecution", back_populates="approvals")

    # Indexes
    __table_args__ = (
        Index('idx_workflow_approvals_pending', 'status', 'priority', 'created_at'),
        Index('idx_workflow_approvals_expires', 'status', 'expires_at'),
    )

    def __repr__(self) -> str:
        return f"<WorkflowApproval(id={self.id}, type='{self.approval_type}', status={self.status})>"

    def is_expired(self) -> bool:
        """Check if approval has expired"""
        if self.expires_at and self.status == ApprovalStatus.PENDING:
            return datetime.utcnow() > self.expires_at
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "approval_type": self.approval_type,
            "approval_title": self.approval_title,
            "status": self.status.value,
            "priority": self.priority.value,
            "approver_name": self.approver_name,
            "approval_reason": self.approval_reason,
            "auto_approval_confidence": self.auto_approval_confidence,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WebhookQueue(Base):
    """
    Webhook Queue for Async Processing

    Queues incoming webhooks for asynchronous processing with
    retry logic and error handling.
    """
    __tablename__ = "n8n_webhook_queue"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("n8n_workflows.id", ondelete="CASCADE"), nullable=True, index=True)

    # Webhook details
    webhook_payload = Column(JSONB, nullable=False)
    webhook_headers = Column(JSONB, nullable=True, default=dict)
    source = Column(String(100), nullable=True, index=True)  # n8n, zapier, custom, etc.
    webhook_url = Column(String(500), nullable=True)

    # Processing
    status = Column(Enum(QueueStatus), default=QueueStatus.QUEUED, nullable=False, index=True)
    priority = Column(Integer, default=0, index=True)  # Higher = more priority

    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime, nullable=True, index=True)

    # Timing
    processed_at = Column(DateTime, nullable=True)
    processing_duration_seconds = Column(Float, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)
    error_trace = Column(Text, nullable=True)
    last_error_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    workflow = relationship("N8NWorkflow", back_populates="webhook_queue")

    # Indexes
    __table_args__ = (
        Index('idx_n8n_webhook_queue_processing', 'status', 'priority', 'created_at'),
        Index('idx_n8n_webhook_queue_retry', 'status', 'next_retry_at'),
    )

    def __repr__(self) -> str:
        return f"<WebhookQueue(id={self.id}, status={self.status}, retry_count={self.retry_count})>"

    def should_retry(self) -> bool:
        """Check if webhook should be retried"""
        if self.status != QueueStatus.FAILED:
            return False
        if self.retry_count >= self.max_retries:
            return False
        if self.next_retry_at and datetime.utcnow() < self.next_retry_at:
            return False
        return True

    def calculate_next_retry(self) -> datetime:
        """Calculate next retry time with exponential backoff"""
        base_delay = 60  # 60 seconds
        delay = base_delay * (2 ** self.retry_count)  # Exponential backoff
        return datetime.utcnow() + timedelta(seconds=delay)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "source": self.source,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }


class WorkflowMonitoring(Base):
    """
    Workflow Monitoring Events

    Captures workflow events, errors, and monitoring data for
    debugging and analytics.
    """
    __tablename__ = "workflow_monitoring"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("n8n_workflows.id", ondelete="CASCADE"), nullable=True, index=True)
    execution_id = Column(Integer, ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=True, index=True)

    # Event details
    event_type = Column(String(100), nullable=False, index=True)  # started, completed, error, step_completed, etc.
    event_name = Column(String(255), nullable=True)
    event_description = Column(Text, nullable=True)
    event_data = Column(JSONB, nullable=True, default=dict)

    # Severity
    severity = Column(Enum(MonitoringSeverity), default=MonitoringSeverity.INFO, nullable=False, index=True)

    # Context
    step_name = Column(String(255), nullable=True)
    step_number = Column(Integer, nullable=True)

    # Performance
    duration_ms = Column(Integer, nullable=True)
    memory_mb = Column(Float, nullable=True)
    cpu_percent = Column(Float, nullable=True)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    workflow = relationship("N8NWorkflow", back_populates="monitoring_events")
    execution = relationship("WorkflowExecution", back_populates="monitoring_events")

    # Indexes
    __table_args__ = (
        Index('idx_workflow_monitoring_workflow_time', 'workflow_id', 'timestamp'),
        Index('idx_workflow_monitoring_severity_time', 'severity', 'timestamp'),
        Index('idx_workflow_monitoring_execution', 'execution_id', 'timestamp'),
    )

    def __repr__(self) -> str:
        return f"<WorkflowMonitoring(id={self.id}, type='{self.event_type}', severity={self.severity})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "event_type": self.event_type,
            "event_name": self.event_name,
            "severity": self.severity.value,
            "step_name": self.step_name,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
