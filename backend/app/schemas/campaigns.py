"""
Campaign Management API Schemas.

Pydantic models for request/response validation in campaign endpoints.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class CampaignStatusEnum(str, Enum):
    """Campaign status enum for API."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class RecipientStatusEnum(str, Enum):
    """Campaign recipient status enum for API."""
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"


class EmailEventTypeEnum(str, Enum):
    """Email tracking event types."""
    OPEN = "open"
    CLICK = "click"
    BOUNCE = "bounce"
    REPLY = "reply"
    FORWARD = "forward"
    UNSUBSCRIBE = "unsubscribe"
    COMPLAIN = "complain"


# ============================================================================
# CAMPAIGN SCHEMAS
# ============================================================================

class CampaignBase(BaseModel):
    """Base campaign schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Campaign name")
    template_id: Optional[int] = Field(None, description="Email template ID to use")


class CampaignCreate(CampaignBase):
    """Schema for creating a new campaign."""
    scheduled_at: Optional[datetime] = Field(None, description="Schedule campaign for future send")

    @validator("scheduled_at")
    def validate_scheduled_at(cls, v):
        """Ensure scheduled time is in the future."""
        if v and v <= datetime.utcnow():
            raise ValueError("scheduled_at must be in the future")
        return v


class CampaignUpdate(BaseModel):
    """Schema for updating an existing campaign."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    template_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[CampaignStatusEnum] = None

    @validator("scheduled_at")
    def validate_scheduled_at(cls, v):
        """Ensure scheduled time is in the future."""
        if v and v <= datetime.utcnow():
            raise ValueError("scheduled_at must be in the future")
        return v


class CampaignMetrics(BaseModel):
    """Campaign performance metrics."""
    emails_sent: int = 0
    emails_opened: int = 0
    emails_clicked: int = 0
    emails_replied: int = 0
    emails_bounced: int = 0
    open_rate: float = Field(..., ge=0.0, le=100.0, description="Percentage")
    click_rate: float = Field(..., ge=0.0, le=100.0, description="Percentage")
    reply_rate: float = Field(..., ge=0.0, le=100.0, description="Percentage")
    bounce_rate: float = Field(..., ge=0.0, le=100.0, description="Percentage")


class CampaignResponse(CampaignBase):
    """Schema for campaign API responses."""
    id: int
    campaign_id: str
    status: CampaignStatusEnum
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_recipients: int
    metrics: CampaignMetrics
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    """Paginated campaign list response."""
    campaigns: List[CampaignResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================================================
# CAMPAIGN RECIPIENT SCHEMAS
# ============================================================================

class CampaignRecipientBase(BaseModel):
    """Base recipient schema."""
    lead_id: int = Field(..., description="Lead ID to add as recipient")


class AddRecipientsRequest(BaseModel):
    """Request to add multiple recipients to a campaign."""
    lead_ids: List[int] = Field(..., min_items=1, description="List of lead IDs to add")

    @validator("lead_ids")
    def validate_unique_leads(cls, v):
        """Ensure no duplicate lead IDs."""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate lead IDs found")
        return v


class CampaignRecipientResponse(BaseModel):
    """Schema for campaign recipient responses."""
    id: int
    campaign_id: int
    lead_id: int
    email_address: str
    status: RecipientStatusEnum
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    bounced_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecipientListResponse(BaseModel):
    """Paginated recipient list response."""
    recipients: List[CampaignRecipientResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================================================
# CAMPAIGN CONTROL SCHEMAS
# ============================================================================

class LaunchCampaignRequest(BaseModel):
    """Request to launch a campaign."""
    send_immediately: bool = Field(True, description="Send now or use scheduled time")
    test_mode: bool = Field(False, description="Test mode - only sends to test recipients")
    test_email: Optional[str] = Field(None, description="Test email address (required if test_mode=true)")

    @validator("test_email", always=True)
    def validate_test_email(cls, v, values):
        """Ensure test email is provided when test_mode is true."""
        if values.get("test_mode") and not v:
            raise ValueError("test_email is required when test_mode is true")
        return v


class SendTestEmailRequest(BaseModel):
    """Request to send a test email."""
    test_email: str = Field(..., description="Email address to send test to")


class PauseCampaignResponse(BaseModel):
    """Response for pause/resume campaign actions."""
    success: bool = True
    message: str
    campaign_id: str
    status: CampaignStatusEnum
    paused_at: Optional[datetime] = None


# ============================================================================
# CAMPAIGN STATISTICS SCHEMAS
# ============================================================================

class CampaignStatsResponse(BaseModel):
    """Real-time campaign statistics."""
    campaign_id: str
    campaign_name: str
    status: CampaignStatusEnum

    # Recipient stats
    total_recipients: int
    pending: int
    queued: int
    sent: int
    failed: int
    bounced: int

    # Engagement stats
    opened: int
    clicked: int
    replied: int

    # Performance metrics
    metrics: CampaignMetrics

    # Timing
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None

    # Progress
    progress_percentage: float = Field(..., ge=0.0, le=100.0)
    emails_per_hour: Optional[float] = None
    average_send_time_seconds: Optional[float] = None


class CampaignAnalyticsResponse(BaseModel):
    """Detailed campaign analytics."""
    campaign: CampaignResponse
    stats: CampaignStatsResponse

    # Time series data
    hourly_sends: List[Dict[str, Any]] = Field(default_factory=list, description="Hourly send volume")
    hourly_opens: List[Dict[str, Any]] = Field(default_factory=list, description="Hourly open rate")
    hourly_clicks: List[Dict[str, Any]] = Field(default_factory=list, description="Hourly click rate")

    # Geographic data (if available)
    opens_by_location: Dict[str, int] = Field(default_factory=dict, description="Opens by geographic location")
    clicks_by_location: Dict[str, int] = Field(default_factory=dict, description="Clicks by geographic location")

    # Device/client data
    opens_by_device: Dict[str, int] = Field(default_factory=dict, description="Opens by device type")
    opens_by_email_client: Dict[str, int] = Field(default_factory=dict, description="Opens by email client")

    # Top performers
    top_openers: List[Dict[str, Any]] = Field(default_factory=list, description="Recipients who opened most")
    top_clickers: List[Dict[str, Any]] = Field(default_factory=list, description="Recipients who clicked most")

    # Error analysis
    bounce_reasons: Dict[str, int] = Field(default_factory=dict, description="Bounce reasons breakdown")
    error_messages: Dict[str, int] = Field(default_factory=dict, description="Error messages breakdown")


# ============================================================================
# EMAIL TRACKING SCHEMAS
# ============================================================================

class EmailTrackingBase(BaseModel):
    """Base email tracking schema."""
    event_type: EmailEventTypeEnum
    event_data: Optional[Dict[str, Any]] = Field(None, description="Additional event metadata")


class TrackEmailEventRequest(EmailTrackingBase):
    """Request to track an email event."""
    user_agent: Optional[str] = Field(None, max_length=500)
    ip_address: Optional[str] = Field(None, max_length=45)


class EmailTrackingResponse(BaseModel):
    """Schema for email tracking event responses."""
    id: int
    campaign_recipient_id: int
    event_type: EmailEventTypeEnum
    event_data: Dict[str, Any]
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TrackingEventsListResponse(BaseModel):
    """List of tracking events for a recipient."""
    recipient_id: int
    email_address: str
    events: List[EmailTrackingResponse]
    total_events: int


# ============================================================================
# FILTER AND QUERY SCHEMAS
# ============================================================================

class CampaignFilters(BaseModel):
    """Filters for campaign list endpoint."""
    status: Optional[CampaignStatusEnum] = None
    template_id: Optional[int] = None
    created_by: Optional[int] = None
    search: Optional[str] = Field(None, description="Search in campaign name")
    date_from: Optional[datetime] = Field(None, description="Filter campaigns created after this date")
    date_to: Optional[datetime] = Field(None, description="Filter campaigns created before this date")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order: asc or desc")

    @validator("sort_by")
    def validate_sort_by(cls, v):
        """Validate sort field."""
        allowed_fields = ["created_at", "updated_at", "name", "started_at", "completed_at"]
        if v not in allowed_fields:
            raise ValueError(f"sort_by must be one of: {', '.join(allowed_fields)}")
        return v

    @validator("sort_order")
    def validate_sort_order(cls, v):
        """Validate sort order."""
        if v not in ["asc", "desc"]:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v


class RecipientFilters(BaseModel):
    """Filters for recipient list endpoint."""
    status: Optional[RecipientStatusEnum] = None
    has_opened: Optional[bool] = None
    has_clicked: Optional[bool] = None
    has_replied: Optional[bool] = None
    has_bounced: Optional[bool] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)


# ============================================================================
# SUCCESS RESPONSE SCHEMAS
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class BulkOperationResponse(BaseModel):
    """Response for bulk operations."""
    success: bool
    total_processed: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    message: str


class DeleteCampaignResponse(BaseModel):
    """Response for campaign deletion."""
    success: bool = True
    message: str
    campaign_id: str
    deleted_at: datetime
