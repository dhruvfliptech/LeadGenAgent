"""
Conversation API Schemas.

Pydantic models for request/response validation in conversation endpoints.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ConversationStatusEnum(str, Enum):
    """Conversation status enum for API."""
    ACTIVE = "active"
    NEEDS_REPLY = "needs_reply"
    WAITING = "waiting"
    ARCHIVED = "archived"


class MessageDirectionEnum(str, Enum):
    """Message direction enum for API."""
    OUTBOUND = "outbound"
    INBOUND = "inbound"


class AISuggestionStatusEnum(str, Enum):
    """AI suggestion status enum for API."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"


# Base schemas

class LeadInfo(BaseModel):
    """Minimal lead info for conversation responses."""
    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    title: str

    class Config:
        from_attributes = True


class SenderRecipientInfo(BaseModel):
    """Email sender/recipient info."""
    email: str
    name: Optional[str] = None


class AIMetadata(BaseModel):
    """AI model metadata."""
    provider: Optional[str] = None
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None


# Message schemas

class MessageBase(BaseModel):
    """Base message schema."""
    subject: str
    body_text: Optional[str] = None
    body_html: Optional[str] = None


class MessageResponse(MessageBase):
    """Message response schema."""
    id: int
    conversation_id: int
    direction: MessageDirectionEnum
    sender: SenderRecipientInfo
    recipient: SenderRecipientInfo
    sent_at: datetime
    read_at: Optional[datetime] = None
    is_read: bool
    created_at: datetime
    attachments: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True


# AI Suggestion schemas

class AISuggestionResponse(BaseModel):
    """AI suggestion response schema."""
    id: int
    conversation_id: int
    reply_to_message_id: int
    suggested_subject: Optional[str] = None
    suggested_body: str
    edited_body: Optional[str] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    sentiment_analysis: Dict[str, Any] = {}
    context_used: List[str] = []
    ai_reasoning: Optional[str] = None
    ai_metadata: AIMetadata
    status: AISuggestionStatusEnum
    created_at: datetime
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_notes: Optional[str] = None

    class Config:
        from_attributes = True


# Conversation schemas

class ConversationListItem(BaseModel):
    """Conversation list item for overview page."""
    id: int
    lead: LeadInfo
    subject: str
    status: ConversationStatusEnum
    message_count: int
    last_message_at: datetime
    last_inbound_at: Optional[datetime] = None
    last_outbound_at: Optional[datetime] = None
    has_pending_suggestion: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Paginated conversation list response."""
    conversations: List[ConversationListItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class ConversationThreadResponse(BaseModel):
    """Full conversation thread with messages."""
    id: int
    lead: LeadInfo
    subject: str
    status: ConversationStatusEnum
    message_count: int
    last_message_at: datetime
    last_inbound_at: Optional[datetime] = None
    last_outbound_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    messages: List[MessageResponse]
    pending_suggestions: List[AISuggestionResponse] = []

    class Config:
        from_attributes = True


# Request schemas

class ApproveReplyRequest(BaseModel):
    """Request to approve and send AI suggestion."""
    suggestion_id: int
    edited_body: Optional[str] = None  # If user edited before approving
    edited_subject: Optional[str] = None


class RejectReplyRequest(BaseModel):
    """Request to reject AI suggestion."""
    suggestion_id: int
    reason: Optional[str] = None


class SendReplyRequest(BaseModel):
    """Request to send custom reply (not AI-generated)."""
    subject: str
    body: str
    body_html: Optional[str] = None


class RegenerateReplyRequest(BaseModel):
    """Request to regenerate AI suggestion with custom parameters."""
    message_id: int  # The inbound message to reply to
    tone: Optional[str] = Field(None, description="Desired tone: professional, casual, formal, friendly")
    length: Optional[str] = Field(None, description="Desired length: short, medium, long")
    custom_prompt: Optional[str] = Field(None, description="Custom instructions for AI")


class ArchiveConversationRequest(BaseModel):
    """Request to archive conversation."""
    reason: Optional[str] = None


# Stats schemas

class ConversationStatsResponse(BaseModel):
    """Conversation analytics and statistics."""
    total_conversations: int
    active_conversations: int
    needs_reply: int
    waiting_for_response: int
    archived_conversations: int

    # This week
    emails_sent_week: int
    emails_received_week: int
    response_rate_week: float = Field(..., ge=0.0, le=100.0)
    avg_response_time_hours: Optional[float] = None

    # AI metrics
    ai_suggestions_generated_week: int
    ai_suggestions_approved_week: int
    ai_approval_rate_week: float = Field(..., ge=0.0, le=100.0)
    avg_confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Delivery metrics
    emails_opened_week: int
    emails_clicked_week: int
    open_rate_week: float = Field(..., ge=0.0, le=100.0)
    click_rate_week: float = Field(..., ge=0.0, le=100.0)


# Filter schemas

class ConversationFilters(BaseModel):
    """Filters for conversation list endpoint."""
    status: Optional[ConversationStatusEnum] = None
    lead_id: Optional[int] = None
    has_pending_suggestion: Optional[bool] = None
    search: Optional[str] = Field(None, description="Search in subject or lead name")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("last_message_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order: asc or desc")

    @validator("sort_by")
    def validate_sort_by(cls, v):
        allowed_fields = ["last_message_at", "created_at", "message_count"]
        if v not in allowed_fields:
            raise ValueError(f"sort_by must be one of: {', '.join(allowed_fields)}")
        return v

    @validator("sort_order")
    def validate_sort_order(cls, v):
        if v not in ["asc", "desc"]:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v


# WebSocket event schemas

class ConversationEvent(BaseModel):
    """WebSocket event for conversation updates."""
    type: str  # conversation:new_reply, conversation:ai_ready, conversation:sent, etc.
    conversation_id: int
    data: Dict[str, Any]
    timestamp: datetime


# Success response schemas

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
