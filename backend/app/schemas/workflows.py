"""
N8N Workflow Automation Schemas

Pydantic schemas for N8N workflow integration including:
- Workflow configuration and management
- Execution tracking and monitoring
- Approval system (manual and auto-approval)
- Webhook processing
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum


# Enums
class WorkflowStatusEnum(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ApprovalStatusEnum(str, Enum):
    """Approval request status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalPriorityEnum(str, Enum):
    """Approval priority levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class QueueStatusEnum(str, Enum):
    """Webhook queue status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MonitoringSeverityEnum(str, Enum):
    """Monitoring event severity"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TriggerSourceEnum(str, Enum):
    """Workflow trigger source"""
    MANUAL = "manual"
    WEBHOOK = "webhook"
    SCHEDULED = "scheduled"
    EVENT = "event"
    API = "api"


# ============================================================================
# N8N WORKFLOW SCHEMAS
# ============================================================================

class N8NWorkflowBase(BaseModel):
    """Base schema for N8N Workflow"""
    workflow_name: str = Field(..., min_length=1, max_length=255)
    workflow_description: Optional[str] = None
    n8n_workflow_id: Optional[str] = Field(None, max_length=100)
    webhook_url: Optional[str] = Field(None, max_length=500)
    webhook_secret: Optional[str] = Field(None, max_length=255)
    trigger_events: Optional[List[str]] = Field(default_factory=list)
    trigger_conditions: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_active: bool = True
    requires_approval: bool = False
    auto_approval_enabled: bool = False
    timeout_seconds: int = Field(default=300, ge=10, le=3600)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=60, ge=10, le=3600)
    tags: Optional[List[str]] = Field(default_factory=list)
    config_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class N8NWorkflowCreate(N8NWorkflowBase):
    """Schema for creating a workflow"""
    pass


class N8NWorkflowUpdate(BaseModel):
    """Schema for updating a workflow"""
    workflow_name: Optional[str] = Field(None, min_length=1, max_length=255)
    workflow_description: Optional[str] = None
    n8n_workflow_id: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    trigger_events: Optional[List[str]] = None
    trigger_conditions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    requires_approval: Optional[bool] = None
    auto_approval_enabled: Optional[bool] = None
    timeout_seconds: Optional[int] = Field(None, ge=10, le=3600)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay_seconds: Optional[int] = Field(None, ge=10, le=3600)
    tags: Optional[List[str]] = None
    config_data: Optional[Dict[str, Any]] = None


class N8NWorkflowResponse(N8NWorkflowBase):
    """Schema for workflow response"""
    id: int
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_executed_at: Optional[datetime] = None
    average_duration_seconds: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class N8NWorkflowStats(BaseModel):
    """Workflow statistics"""
    workflow_id: int
    workflow_name: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    average_duration_seconds: float
    last_executed_at: Optional[datetime]


# ============================================================================
# WORKFLOW EXECUTION SCHEMAS
# ============================================================================

class WorkflowExecutionBase(BaseModel):
    """Base schema for workflow execution"""
    workflow_id: int
    trigger_event: Optional[str] = None
    trigger_source: Optional[TriggerSourceEnum] = TriggerSourceEnum.MANUAL
    input_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WorkflowExecutionCreate(WorkflowExecutionBase):
    """Schema for creating a workflow execution"""
    pass


class WorkflowExecutionUpdate(BaseModel):
    """Schema for updating a workflow execution"""
    status: Optional[WorkflowStatusEnum] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    current_step: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    execution_log: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None


class WorkflowExecutionResponse(WorkflowExecutionBase):
    """Schema for workflow execution response"""
    id: int
    n8n_execution_id: Optional[str] = None
    status: WorkflowStatusEnum
    progress_percentage: int = 0
    current_step: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    execution_log: Optional[str] = None
    duration_seconds: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    retry_count: int = 0
    is_retryable: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class WorkflowExecutionWithDetails(WorkflowExecutionResponse):
    """Workflow execution with workflow details"""
    workflow: N8NWorkflowResponse


class WorkflowExecutionRetry(BaseModel):
    """Schema for retrying a failed execution"""
    override_input_data: Optional[Dict[str, Any]] = None
    max_retries: Optional[int] = Field(None, ge=1, le=10)


# ============================================================================
# WORKFLOW APPROVAL SCHEMAS
# ============================================================================

class WorkflowApprovalBase(BaseModel):
    """Base schema for workflow approval"""
    execution_id: int
    approval_type: str = Field(..., min_length=1, max_length=100)
    approval_title: str = Field(..., min_length=1, max_length=255)
    approval_description: Optional[str] = None
    approval_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    priority: ApprovalPriorityEnum = ApprovalPriorityEnum.MEDIUM
    requires_manual: bool = False
    auto_approval_enabled: bool = True


class WorkflowApprovalCreate(WorkflowApprovalBase):
    """Schema for creating an approval request"""
    expires_in_hours: Optional[int] = Field(default=24, ge=1, le=168)


class WorkflowApprovalResponse(WorkflowApprovalBase):
    """Schema for approval response"""
    id: int
    status: ApprovalStatusEnum
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    approval_reason: Optional[str] = None
    approved_at: Optional[datetime] = None
    auto_approval_confidence: Optional[float] = None
    auto_approval_reason: Optional[str] = None
    expires_at: Optional[datetime] = None
    notification_sent: bool = False
    notification_sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WorkflowApprovalDecision(BaseModel):
    """Schema for approving/rejecting a request"""
    decision: ApprovalStatusEnum = Field(..., description="approved or rejected")
    approver_name: Optional[str] = None
    reason: Optional[str] = None

    @validator('decision')
    def validate_decision(cls, v):
        if v not in [ApprovalStatusEnum.APPROVED, ApprovalStatusEnum.REJECTED]:
            raise ValueError('Decision must be either approved or rejected')
        return v


class WorkflowApprovalBulkAction(BaseModel):
    """Schema for bulk approval actions"""
    approval_ids: List[int] = Field(..., min_items=1)
    action: ApprovalStatusEnum
    approver_name: Optional[str] = None
    reason: Optional[str] = None

    @validator('action')
    def validate_action(cls, v):
        if v not in [ApprovalStatusEnum.APPROVED, ApprovalStatusEnum.REJECTED]:
            raise ValueError('Action must be either approved or rejected')
        return v


class WorkflowApprovalStats(BaseModel):
    """Approval statistics"""
    total_pending: int
    total_approved: int
    total_rejected: int
    total_expired: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    average_approval_time_hours: Optional[float]
    auto_approval_rate: Optional[float]


# ============================================================================
# WEBHOOK QUEUE SCHEMAS
# ============================================================================

class WebhookQueueBase(BaseModel):
    """Base schema for webhook queue"""
    workflow_id: Optional[int] = None
    webhook_payload: Dict[str, Any]
    webhook_headers: Optional[Dict[str, str]] = Field(default_factory=dict)
    source: Optional[str] = Field(None, max_length=100)
    webhook_url: Optional[str] = Field(None, max_length=500)
    priority: int = Field(default=0, ge=0, le=100)


class WebhookQueueCreate(WebhookQueueBase):
    """Schema for creating a webhook queue entry"""
    max_retries: Optional[int] = Field(default=3, ge=0, le=10)


class WebhookQueueResponse(WebhookQueueBase):
    """Schema for webhook queue response"""
    id: int
    status: QueueStatusEnum
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    processing_duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    error_trace: Optional[str] = None
    last_error_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookReceive(BaseModel):
    """Schema for incoming webhook data"""
    event: Optional[str] = None
    data: Dict[str, Any]
    source: Optional[str] = "n8n"
    workflow_id: Optional[str] = None


# ============================================================================
# WORKFLOW MONITORING SCHEMAS
# ============================================================================

class WorkflowMonitoringBase(BaseModel):
    """Base schema for workflow monitoring"""
    workflow_id: Optional[int] = None
    execution_id: Optional[int] = None
    event_type: str = Field(..., min_length=1, max_length=100)
    event_name: Optional[str] = Field(None, max_length=255)
    event_description: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    severity: MonitoringSeverityEnum = MonitoringSeverityEnum.INFO
    step_name: Optional[str] = Field(None, max_length=255)
    step_number: Optional[int] = None
    duration_ms: Optional[int] = None
    memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None


class WorkflowMonitoringCreate(WorkflowMonitoringBase):
    """Schema for creating a monitoring event"""
    pass


class WorkflowMonitoringResponse(WorkflowMonitoringBase):
    """Schema for monitoring event response"""
    id: int
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class WorkflowMonitoringQuery(BaseModel):
    """Schema for querying monitoring events"""
    workflow_id: Optional[int] = None
    execution_id: Optional[int] = None
    event_type: Optional[str] = None
    severity: Optional[MonitoringSeverityEnum] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


# ============================================================================
# WORKFLOW TRIGGER SCHEMAS
# ============================================================================

class WorkflowTrigger(BaseModel):
    """Schema for triggering a workflow"""
    trigger_event: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    trigger_source: TriggerSourceEnum = TriggerSourceEnum.API
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    force_execution: bool = Field(default=False, description="Bypass approval if true")


class WorkflowTriggerResponse(BaseModel):
    """Response after triggering a workflow"""
    execution_id: int
    workflow_id: int
    workflow_name: str
    status: WorkflowStatusEnum
    requires_approval: bool
    approval_id: Optional[int] = None
    message: str


# ============================================================================
# DASHBOARD AND STATISTICS SCHEMAS
# ============================================================================

class WorkflowDashboard(BaseModel):
    """Workflow dashboard data"""
    total_workflows: int
    active_workflows: int
    total_executions_today: int
    successful_executions_today: int
    failed_executions_today: int
    pending_approvals: int
    queued_webhooks: int
    recent_executions: List[WorkflowExecutionResponse]
    recent_errors: List[WorkflowMonitoringResponse]


class WorkflowHealthCheck(BaseModel):
    """Workflow system health check"""
    n8n_connection: bool
    database_connection: bool
    webhook_queue_size: int
    pending_approvals: int
    failed_executions_last_hour: int
    average_execution_time_seconds: float
    status: str  # healthy, degraded, unhealthy


# ============================================================================
# LIST RESPONSE SCHEMAS
# ============================================================================

class WorkflowListResponse(BaseModel):
    """Paginated list of workflows"""
    items: List[N8NWorkflowResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ExecutionListResponse(BaseModel):
    """Paginated list of executions"""
    items: List[WorkflowExecutionResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ApprovalListResponse(BaseModel):
    """Paginated list of approvals"""
    items: List[WorkflowApprovalResponse]
    total: int
    page: int
    page_size: int
    pages: int


class MonitoringListResponse(BaseModel):
    """Paginated list of monitoring events"""
    items: List[WorkflowMonitoringResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# WORKFLOW TEMPLATE SCHEMAS
# ============================================================================

class WorkflowTemplateType(str, Enum):
    """Pre-built workflow template types"""
    LEAD_QUALIFICATION = "lead_qualification"
    VIDEO_DEMO_SITE = "video_demo_site"
    FOLLOW_UP_AUTOMATION = "follow_up_automation"
    EMAIL_CAMPAIGN = "email_campaign"
    CUSTOM = "custom"


class WorkflowTemplate(BaseModel):
    """Pre-built workflow template"""
    template_type: WorkflowTemplateType
    workflow_name: str
    workflow_description: str
    trigger_events: List[str]
    config_data: Dict[str, Any]
    requires_approval: bool
    auto_approval_enabled: bool


class WorkflowTemplateInstantiate(BaseModel):
    """Instantiate a workflow from template"""
    template_type: WorkflowTemplateType
    workflow_name: str
    custom_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
