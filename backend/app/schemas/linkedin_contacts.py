"""
LinkedIn Contacts Pydantic Schemas

Defines request/response schemas for LinkedIn contact import and messaging.
Includes validation, CSV parsing schemas, and OAuth flow models.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, HttpUrl, validator, root_validator


# ============================================================================
# LinkedIn Contact Schemas
# ============================================================================

class LinkedInContactBase(BaseModel):
    """Base schema for LinkedIn contact."""
    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    linkedin_url: Optional[str] = Field(None, max_length=500)
    company: Optional[str] = Field(None, max_length=500)
    position: Optional[str] = Field(None, max_length=500)
    headline: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    @validator('linkedin_url')
    def validate_linkedin_url(cls, v):
        """Validate LinkedIn URL format."""
        if v and not any(domain in v.lower() for domain in ['linkedin.com', 'linkedin.in']):
            raise ValueError('Must be a valid LinkedIn URL')
        return v


class LinkedInContactCreate(LinkedInContactBase):
    """Schema for creating a new LinkedIn contact."""
    profile_picture_url: Optional[str] = Field(None, max_length=1000)
    connected_on: Optional[datetime] = None
    mutual_connections_count: Optional[int] = Field(default=0, ge=0)
    profile_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    imported_from: str = Field(default='manual', pattern='^(csv|manual|api)$')
    import_batch_id: Optional[str] = Field(None, max_length=100)


class LinkedInContactUpdate(BaseModel):
    """Schema for updating a LinkedIn contact."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    linkedin_url: Optional[str] = Field(None, max_length=500)
    company: Optional[str] = Field(None, max_length=500)
    position: Optional[str] = Field(None, max_length=500)
    headline: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    can_message: Optional[bool] = None
    status: Optional[str] = Field(None, pattern='^(active|archived|blocked|bounced)$')
    unsubscribed: Optional[bool] = None


class LinkedInContactResponse(LinkedInContactBase):
    """Schema for LinkedIn contact response."""
    id: int
    full_name: str
    profile_picture_url: Optional[str]
    connected_on: Optional[datetime]
    mutual_connections_count: int
    imported_from: str
    import_batch_id: Optional[str]
    last_messaged_at: Optional[datetime]
    total_messages_sent: int
    last_message_status: Optional[str]
    can_message: bool
    can_send_message: bool
    lead_id: Optional[int]
    campaign_ids: List[int]
    response_received: bool
    last_response_at: Optional[datetime]
    engagement_score: int
    status: str
    is_premium: bool
    unsubscribed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LinkedInContactListResponse(BaseModel):
    """Schema for paginated list of LinkedIn contacts."""
    contacts: List[LinkedInContactResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# CSV Import Schemas
# ============================================================================

class CSVFieldMapping(BaseModel):
    """Schema for CSV field mapping configuration."""
    first_name: str = Field(default='First Name', description='CSV column for first name')
    last_name: str = Field(default='Last Name', description='CSV column for last name')
    email: str = Field(default='Email Address', description='CSV column for email')
    company: str = Field(default='Company', description='CSV column for company')
    position: str = Field(default='Position', description='CSV column for position')
    connected_on: str = Field(default='Connected On', description='CSV column for connection date')
    linkedin_url: str = Field(default='URL', description='CSV column for LinkedIn URL')


class CSVImportRequest(BaseModel):
    """Schema for CSV import request."""
    filename: str = Field(..., description='Name of uploaded CSV file')
    field_mapping: Optional[CSVFieldMapping] = Field(default_factory=CSVFieldMapping)
    tags: List[str] = Field(default_factory=list, description='Tags to apply to imported contacts')
    skip_duplicates: bool = Field(default=True, description='Skip contacts that already exist')
    deduplicate_by: str = Field(default='linkedin_url', pattern='^(linkedin_url|email|name)$')
    import_batch_id: Optional[str] = Field(None, description='Custom batch ID for this import')


class CSVImportPreview(BaseModel):
    """Schema for CSV import preview before actual import."""
    total_rows: int
    sample_contacts: List[Dict[str, Any]]
    field_mapping: CSVFieldMapping
    detected_columns: List[str]
    validation_errors: List[str] = Field(default_factory=list)


class CSVImportResponse(BaseModel):
    """Schema for CSV import response."""
    import_batch_id: str
    total_rows: int
    imported: int
    skipped: int
    failed: int
    errors: List[str] = Field(default_factory=list)
    contacts: List[LinkedInContactResponse] = Field(default_factory=list)


# ============================================================================
# LinkedIn Message Schemas
# ============================================================================

class LinkedInMessageBase(BaseModel):
    """Base schema for LinkedIn message."""
    subject: Optional[str] = Field(None, max_length=500)
    message_content: str = Field(..., min_length=1)
    message_type: str = Field(default='direct', pattern='^(direct|connection_request|inmail)$')


class LinkedInMessageCreate(LinkedInMessageBase):
    """Schema for creating a new LinkedIn message."""
    contact_id: int = Field(..., gt=0)
    campaign_id: Optional[int] = Field(None, gt=0)
    template_id: Optional[int] = Field(None, gt=0)
    personalized_fields: Dict[str, str] = Field(default_factory=dict)
    scheduled_for: Optional[datetime] = None
    priority: int = Field(default=0, ge=0, le=10)

    @validator('message_content')
    def validate_message_length(cls, v, values):
        """Validate message length based on type."""
        message_type = values.get('message_type', 'direct')
        if message_type == 'connection_request' and len(v) > 300:
            raise ValueError('Connection request messages must be 300 characters or less')
        if message_type == 'direct' and len(v) > 8000:
            raise ValueError('Direct messages must be 8000 characters or less')
        return v


class LinkedInBulkMessageCreate(BaseModel):
    """Schema for bulk message sending."""
    contact_ids: List[int] = Field(..., min_items=1, max_items=1000)
    subject: Optional[str] = Field(None, max_length=500)
    message_content: str = Field(..., min_length=1)
    message_type: str = Field(default='direct', pattern='^(direct|connection_request|inmail)$')
    campaign_id: Optional[int] = Field(None, gt=0)
    template_id: Optional[int] = Field(None, gt=0)
    personalize: bool = Field(default=True, description='Use contact data for personalization')
    scheduled_for: Optional[datetime] = None
    stagger_minutes: int = Field(default=5, ge=1, le=60, description='Minutes between messages')


class LinkedInMessageUpdate(BaseModel):
    """Schema for updating a LinkedIn message."""
    status: Optional[str] = Field(None, pattern='^(pending|sending|sent|delivered|read|failed|bounced)$')
    error_message: Optional[str] = None
    linkedin_message_id: Optional[str] = None
    conversation_id: Optional[str] = None


class LinkedInMessageResponse(LinkedInMessageBase):
    """Schema for LinkedIn message response."""
    id: int
    contact_id: int
    linkedin_message_id: Optional[str]
    conversation_id: Optional[str]
    campaign_id: Optional[int]
    template_id: Optional[int]
    status: str
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    failed_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    replied: bool
    reply_at: Optional[datetime]
    reply_content: Optional[str]
    clicked_link: bool
    click_count: int
    scheduled_for: Optional[datetime]
    priority: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LinkedInMessageListResponse(BaseModel):
    """Schema for paginated list of LinkedIn messages."""
    messages: List[LinkedInMessageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class LinkedInBulkMessageResponse(BaseModel):
    """Schema for bulk message response."""
    total_requested: int
    queued: int
    failed: int
    estimated_completion: Optional[datetime]
    message_ids: List[int]
    errors: List[str] = Field(default_factory=list)


# ============================================================================
# OAuth and Connection Schemas
# ============================================================================

class LinkedInOAuthInitiate(BaseModel):
    """Schema for initiating OAuth flow."""
    redirect_uri: Optional[str] = None
    state: Optional[str] = None
    scope: List[str] = Field(
        default=['r_liteprofile', 'w_member_social', 'r_emailaddress'],
        description='OAuth scopes to request'
    )


class LinkedInOAuthCallback(BaseModel):
    """Schema for OAuth callback."""
    code: str = Field(..., description='Authorization code from LinkedIn')
    state: Optional[str] = Field(None, description='State parameter for CSRF protection')


class LinkedInConnectionResponse(BaseModel):
    """Schema for LinkedIn connection response."""
    id: int
    account_name: Optional[str]
    linkedin_user_id: str
    profile_email: Optional[str]
    profile_name: Optional[str]
    profile_picture_url: Optional[str]
    profile_url: Optional[str]
    is_active: bool
    is_valid: bool
    is_token_expired: bool
    can_send_messages: bool
    daily_messages_sent: int
    messages_remaining_today: int
    rate_limit_exceeded: bool
    total_messages_sent: int
    total_connections_imported: int
    last_used_at: Optional[datetime]
    connected_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LinkedInConnectionUpdate(BaseModel):
    """Schema for updating LinkedIn connection."""
    account_name: Optional[str] = None
    is_active: Optional[bool] = None


# ============================================================================
# Analytics and Statistics Schemas
# ============================================================================

class LinkedInContactStats(BaseModel):
    """Schema for contact statistics."""
    total_contacts: int
    active_contacts: int
    archived_contacts: int
    blocked_contacts: int
    messageable_contacts: int
    contacts_with_email: int
    contacts_by_company: Dict[str, int]
    contacts_by_industry: Dict[str, int]
    recent_imports: List[Dict[str, Any]]


class LinkedInMessageStats(BaseModel):
    """Schema for message statistics."""
    total_messages: int
    sent_today: int
    pending_messages: int
    failed_messages: int
    delivery_rate: float
    read_rate: float
    response_rate: float
    messages_by_status: Dict[str, int]
    messages_by_campaign: Dict[str, int]
    average_response_time_hours: Optional[float]


class LinkedInDashboardStats(BaseModel):
    """Schema for LinkedIn dashboard statistics."""
    contacts: LinkedInContactStats
    messages: LinkedInMessageStats
    connection_status: LinkedInConnectionResponse
    recent_activity: List[Dict[str, Any]]


# ============================================================================
# Filter and Search Schemas
# ============================================================================

class LinkedInContactFilters(BaseModel):
    """Schema for filtering contacts."""
    search: Optional[str] = Field(None, description='Search by name, company, or position')
    company: Optional[str] = None
    position: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = Field(None, pattern='^(active|archived|blocked|bounced)$')
    can_message: Optional[bool] = None
    has_email: Optional[bool] = None
    campaign_id: Optional[int] = None
    tags: Optional[List[str]] = None
    import_batch_id: Optional[str] = None
    connected_after: Optional[datetime] = None
    connected_before: Optional[datetime] = None
    min_engagement_score: Optional[int] = Field(None, ge=0, le=100)


class LinkedInMessageFilters(BaseModel):
    """Schema for filtering messages."""
    contact_id: Optional[int] = None
    campaign_id: Optional[int] = None
    status: Optional[str] = None
    message_type: Optional[str] = None
    sent_after: Optional[datetime] = None
    sent_before: Optional[datetime] = None
    replied: Optional[bool] = None
    failed: Optional[bool] = None


# ============================================================================
# Template and Personalization Schemas
# ============================================================================

class LinkedInMessageTemplate(BaseModel):
    """Schema for message template."""
    name: str = Field(..., min_length=1, max_length=255)
    subject: Optional[str] = Field(None, max_length=500)
    content: str = Field(..., min_length=1)
    message_type: str = Field(default='direct', pattern='^(direct|connection_request|inmail)$')
    personalization_fields: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    is_active: bool = Field(default=True)


class LinkedInMessageTemplateResponse(LinkedInMessageTemplate):
    """Schema for message template response."""
    id: int
    usage_count: int
    success_rate: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Export Schemas
# ============================================================================

class LinkedInExportRequest(BaseModel):
    """Schema for exporting contacts."""
    format: str = Field(default='csv', pattern='^(csv|json|xlsx)$')
    filters: Optional[LinkedInContactFilters] = None
    include_messages: bool = Field(default=False)
    include_fields: Optional[List[str]] = None


class LinkedInExportResponse(BaseModel):
    """Schema for export response."""
    export_id: str
    format: str
    total_records: int
    download_url: str
    expires_at: datetime
