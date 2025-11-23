"""
WebSocket Event Schemas

Pydantic models for all WebSocket event types across the FlipTech Pro application.
Provides type safety, validation, and serialization for real-time updates.
"""

from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# Base Event Schema
class BaseEvent(BaseModel):
    """Base schema for all WebSocket events."""

    type: str = Field(..., description="Event type identifier")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Event timestamp in ISO format"
    )
    room: Optional[str] = Field(None, description="Optional room identifier for targeted messages")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "example:event",
                "timestamp": "2024-01-15T10:30:00Z",
                "room": "campaign:123"
            }
        }


# Campaign Events
class CampaignLaunchedEvent(BaseEvent):
    """Event when a campaign is launched."""

    type: Literal["campaign:launched"] = "campaign:launched"
    campaign_id: int
    campaign_name: str
    total_recipients: int
    scheduled_at: Optional[str] = None


class CampaignPausedEvent(BaseEvent):
    """Event when a campaign is paused."""

    type: Literal["campaign:paused"] = "campaign:paused"
    campaign_id: int
    campaign_name: str
    emails_sent: int
    emails_remaining: int


class CampaignResumedEvent(BaseEvent):
    """Event when a campaign is resumed."""

    type: Literal["campaign:resumed"] = "campaign:resumed"
    campaign_id: int
    campaign_name: str
    emails_remaining: int


class CampaignCompletedEvent(BaseEvent):
    """Event when a campaign completes."""

    type: Literal["campaign:completed"] = "campaign:completed"
    campaign_id: int
    campaign_name: str
    total_sent: int
    total_opened: int
    total_clicked: int
    total_replied: int
    open_rate: float
    click_rate: float
    reply_rate: float


class CampaignEmailSentEvent(BaseEvent):
    """Event when a campaign email is sent."""

    type: Literal["campaign:email_sent"] = "campaign:email_sent"
    campaign_id: int
    recipient_id: int
    lead_id: int
    to_email: str
    subject: str


class CampaignEmailFailedEvent(BaseEvent):
    """Event when a campaign email fails."""

    type: Literal["campaign:email_failed"] = "campaign:email_failed"
    campaign_id: int
    recipient_id: int
    lead_id: int
    to_email: str
    error: str
    retry_count: int


class CampaignStatsUpdatedEvent(BaseEvent):
    """Event when campaign statistics are updated."""

    type: Literal["campaign:stats_updated"] = "campaign:stats_updated"
    campaign_id: int
    emails_sent: int
    emails_opened: int
    emails_clicked: int
    emails_replied: int
    emails_bounced: int
    open_rate: float
    click_rate: float
    reply_rate: float
    bounce_rate: float


# Email Events
class EmailSentEvent(BaseEvent):
    """Event when an email is sent."""

    type: Literal["email:sent"] = "email:sent"
    email_id: Optional[int] = None
    to_email: str
    subject: str
    message_id: str
    provider: str


class EmailDeliveredEvent(BaseEvent):
    """Event when an email is delivered."""

    type: Literal["email:delivered"] = "email:delivered"
    email_id: Optional[int] = None
    to_email: str
    message_id: str


class EmailOpenedEvent(BaseEvent):
    """Event when an email is opened."""

    type: Literal["email:opened"] = "email:opened"
    email_id: Optional[int] = None
    campaign_id: Optional[int] = None
    lead_id: Optional[int] = None
    to_email: str
    opened_at: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class EmailClickedEvent(BaseEvent):
    """Event when an email link is clicked."""

    type: Literal["email:clicked"] = "email:clicked"
    email_id: Optional[int] = None
    campaign_id: Optional[int] = None
    lead_id: Optional[int] = None
    to_email: str
    url: str
    clicked_at: str
    user_agent: Optional[str] = None


class EmailBouncedEvent(BaseEvent):
    """Event when an email bounces."""

    type: Literal["email:bounced"] = "email:bounced"
    email_id: Optional[int] = None
    to_email: str
    bounce_type: str  # hard, soft
    bounce_reason: str


class EmailUnsubscribedEvent(BaseEvent):
    """Event when a user unsubscribes."""

    type: Literal["email:unsubscribed"] = "email:unsubscribed"
    email_id: Optional[int] = None
    campaign_id: Optional[int] = None
    lead_id: Optional[int] = None
    to_email: str
    unsubscribed_at: str


# Scraper Events
class ScraperStartedEvent(BaseEvent):
    """Event when scraping starts."""

    type: Literal["scraper:started"] = "scraper:started"
    scraper_id: str
    source: str  # craigslist, google_maps, linkedin, etc.
    location: Optional[str] = None
    category: Optional[str] = None
    max_results: int


class ScraperProgressEvent(BaseEvent):
    """Event for scraper progress updates."""

    type: Literal["scraper:progress"] = "scraper:progress"
    scraper_id: str
    source: str
    current: int
    total: int
    percent: float
    leads_found: int
    message: Optional[str] = None


class ScraperLeadFoundEvent(BaseEvent):
    """Event when scraper finds a lead."""

    type: Literal["scraper:lead_found"] = "scraper:lead_found"
    scraper_id: str
    source: str
    lead_id: int
    lead_name: Optional[str] = None
    lead_email: Optional[str] = None


class ScraperCompletedEvent(BaseEvent):
    """Event when scraping completes."""

    type: Literal["scraper:completed"] = "scraper:completed"
    scraper_id: str
    source: str
    total_leads: int
    leads_created: int
    leads_updated: int
    duration_seconds: float
    success: bool


class ScraperFailedEvent(BaseEvent):
    """Event when scraping fails."""

    type: Literal["scraper:failed"] = "scraper:failed"
    scraper_id: str
    source: str
    error: str
    partial_results: int


class ScraperGoogleMapsProgressEvent(BaseEvent):
    """Event for Google Maps scraper progress."""

    type: Literal["scraper:google_maps_progress"] = "scraper:google_maps_progress"
    scraper_id: str
    search_query: str
    current_page: int
    businesses_found: int
    businesses_processed: int


class ScraperLinkedInProgressEvent(BaseEvent):
    """Event for LinkedIn scraper progress."""

    type: Literal["scraper:linkedin_progress"] = "scraper:linkedin_progress"
    scraper_id: str
    search_query: str
    profiles_found: int
    profiles_processed: int


class ScraperJobBoardProgressEvent(BaseEvent):
    """Event for job board scraper progress."""

    type: Literal["scraper:job_board_progress"] = "scraper:job_board_progress"
    scraper_id: str
    board: str  # indeed, monster, ziprecruiter
    search_query: str
    jobs_found: int
    jobs_processed: int


# AI Events
class AIProcessingEvent(BaseEvent):
    """Event when AI processing starts."""

    type: Literal["ai:processing"] = "ai:processing"
    task_id: str
    task_type: str  # response, analysis, generation
    resource_id: Optional[int] = None  # lead_id, conversation_id, etc.


class AIResponseReadyEvent(BaseEvent):
    """Event when AI response is ready."""

    type: Literal["ai:response_ready"] = "ai:response_ready"
    task_id: str
    conversation_id: int
    response: str
    confidence: float
    tokens_used: int


class AIAnalysisCompleteEvent(BaseEvent):
    """Event when AI analysis completes."""

    type: Literal["ai:analysis_complete"] = "ai:analysis_complete"
    task_id: str
    lead_id: int
    quality_score: float
    fit_score: float
    insights: List[str]
    recommended_actions: List[str]


class AIModelTrainedEvent(BaseEvent):
    """Event when ML model training completes."""

    type: Literal["ai:model_trained"] = "ai:model_trained"
    model_type: str
    accuracy: float
    training_samples: int
    model_version: str


class AIEmailGeneratedEvent(BaseEvent):
    """Event when AI generates email content."""

    type: Literal["ai:email_generated"] = "ai:email_generated"
    task_id: str
    lead_id: int
    subject: str
    preview: str  # First 100 chars of body


class AILeadAnalyzedEvent(BaseEvent):
    """Event when AI analyzes a lead."""

    type: Literal["ai:lead_analyzed"] = "ai:lead_analyzed"
    lead_id: int
    quality_score: float
    tags: List[str]
    priority: str


class AIConversationProcessedEvent(BaseEvent):
    """Event when AI processes a conversation."""

    type: Literal["ai:conversation_processed"] = "ai:conversation_processed"
    conversation_id: int
    sentiment: str
    intent: str
    key_topics: List[str]
    urgency: str


# Demo Events
class DemoGeneratingEvent(BaseEvent):
    """Event when demo generation starts."""

    type: Literal["demo:generating"] = "demo:generating"
    demo_id: str
    lead_id: int
    template: str


class DemoRecordingEvent(BaseEvent):
    """Event when demo recording is in progress."""

    type: Literal["demo:recording"] = "demo:recording"
    demo_id: str
    recording_type: str  # screen, video
    duration_seconds: int


class DemoComposingEvent(BaseEvent):
    """Event when demo video is being composed."""

    type: Literal["demo:composing"] = "demo:composing"
    demo_id: str
    progress_percent: float
    current_step: str


class DemoUploadingEvent(BaseEvent):
    """Event when demo is being uploaded."""

    type: Literal["demo:uploading"] = "demo:uploading"
    demo_id: str
    file_size_mb: float
    upload_percent: float


class DemoCompletedEvent(BaseEvent):
    """Event when demo is completed."""

    type: Literal["demo:completed"] = "demo:completed"
    demo_id: str
    lead_id: int
    demo_url: str
    video_url: Optional[str] = None
    duration_seconds: float


class DemoFailedEvent(BaseEvent):
    """Event when demo generation fails."""

    type: Literal["demo:failed"] = "demo:failed"
    demo_id: str
    lead_id: int
    error: str
    step_failed: str


# Lead Events
class LeadCreatedEvent(BaseEvent):
    """Event when a lead is created."""

    type: Literal["lead:created"] = "lead:created"
    lead_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    source: str
    location: Optional[str] = None


class LeadUpdatedEvent(BaseEvent):
    """Event when a lead is updated."""

    type: Literal["lead:updated"] = "lead:updated"
    lead_id: int
    updates: Dict[str, Any]


class LeadDeletedEvent(BaseEvent):
    """Event when a lead is deleted."""

    type: Literal["lead:deleted"] = "lead:deleted"
    lead_id: int


# Conversation Events
class ConversationNewReplyEvent(BaseEvent):
    """Event when a new reply arrives."""

    type: Literal["conversation:new_reply"] = "conversation:new_reply"
    conversation_id: int
    message_id: int
    sender: str
    preview: str


class ConversationAIReadyEvent(BaseEvent):
    """Event when AI suggestion is ready."""

    type: Literal["conversation:ai_ready"] = "conversation:ai_ready"
    conversation_id: int
    suggestion_id: int
    confidence: float


class ConversationSentEvent(BaseEvent):
    """Event when a reply is sent."""

    type: Literal["conversation:sent"] = "conversation:sent"
    conversation_id: int
    message_id: int


class ConversationErrorEvent(BaseEvent):
    """Event when conversation error occurs."""

    type: Literal["conversation:error"] = "conversation:error"
    conversation_id: int
    error: str


# System Events
class SystemNotificationEvent(BaseEvent):
    """Generic system notification event."""

    type: Literal["notification:system"] = "notification:system"
    level: Literal["info", "warning", "error", "success"]
    title: str
    message: str
    action_url: Optional[str] = None


class ConnectionEvent(BaseEvent):
    """WebSocket connection event."""

    type: Literal["connection"] = "connection"
    status: Literal["connected", "disconnected"]
    client_id: str
    message: str


class HeartbeatEvent(BaseModel):
    """Heartbeat/ping event."""

    type: Literal["heartbeat"] = "heartbeat"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# Union type for all events (useful for type checking)
WebSocketEvent = (
    CampaignLaunchedEvent
    | CampaignPausedEvent
    | CampaignResumedEvent
    | CampaignCompletedEvent
    | CampaignEmailSentEvent
    | CampaignEmailFailedEvent
    | CampaignStatsUpdatedEvent
    | EmailSentEvent
    | EmailDeliveredEvent
    | EmailOpenedEvent
    | EmailClickedEvent
    | EmailBouncedEvent
    | EmailUnsubscribedEvent
    | ScraperStartedEvent
    | ScraperProgressEvent
    | ScraperLeadFoundEvent
    | ScraperCompletedEvent
    | ScraperFailedEvent
    | ScraperGoogleMapsProgressEvent
    | ScraperLinkedInProgressEvent
    | ScraperJobBoardProgressEvent
    | AIProcessingEvent
    | AIResponseReadyEvent
    | AIAnalysisCompleteEvent
    | AIModelTrainedEvent
    | AIEmailGeneratedEvent
    | AILeadAnalyzedEvent
    | AIConversationProcessedEvent
    | DemoGeneratingEvent
    | DemoRecordingEvent
    | DemoComposingEvent
    | DemoUploadingEvent
    | DemoCompletedEvent
    | DemoFailedEvent
    | LeadCreatedEvent
    | LeadUpdatedEvent
    | LeadDeletedEvent
    | ConversationNewReplyEvent
    | ConversationAIReadyEvent
    | ConversationSentEvent
    | ConversationErrorEvent
    | SystemNotificationEvent
    | ConnectionEvent
    | HeartbeatEvent
)
