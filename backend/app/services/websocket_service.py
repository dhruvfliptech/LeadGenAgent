"""
WebSocket Service Layer

High-level service for publishing WebSocket events throughout the application.
Provides type-safe event publishing with Pydantic schemas and Redis Pub/Sub integration.
"""

import logging
from typing import Dict, Any, Optional, Type
from datetime import datetime

from app.core.redis_pubsub import redis_pubsub_manager, RedisPubSubManager
from app.schemas.websocket_events import (
    BaseEvent,
    CampaignLaunchedEvent,
    CampaignPausedEvent,
    CampaignResumedEvent,
    CampaignCompletedEvent,
    CampaignEmailSentEvent,
    CampaignEmailFailedEvent,
    CampaignStatsUpdatedEvent,
    EmailSentEvent,
    EmailDeliveredEvent,
    EmailOpenedEvent,
    EmailClickedEvent,
    EmailBouncedEvent,
    EmailUnsubscribedEvent,
    ScraperStartedEvent,
    ScraperProgressEvent,
    ScraperLeadFoundEvent,
    ScraperCompletedEvent,
    ScraperFailedEvent,
    ScraperGoogleMapsProgressEvent,
    ScraperLinkedInProgressEvent,
    ScraperJobBoardProgressEvent,
    AIProcessingEvent,
    AIResponseReadyEvent,
    AIAnalysisCompleteEvent,
    AIModelTrainedEvent,
    AIEmailGeneratedEvent,
    AILeadAnalyzedEvent,
    AIConversationProcessedEvent,
    DemoGeneratingEvent,
    DemoRecordingEvent,
    DemoComposingEvent,
    DemoUploadingEvent,
    DemoCompletedEvent,
    DemoFailedEvent,
    LeadCreatedEvent,
    LeadUpdatedEvent,
    LeadDeletedEvent,
    ConversationNewReplyEvent,
    ConversationAIReadyEvent,
    ConversationSentEvent,
    ConversationErrorEvent,
    SystemNotificationEvent,
)

logger = logging.getLogger(__name__)


class WebSocketService:
    """
    Service for publishing WebSocket events with type safety and Redis integration.

    This service provides a clean interface for publishing events from anywhere
    in the application, with automatic serialization and Redis Pub/Sub routing.
    """

    def __init__(self, pubsub_manager: Optional[RedisPubSubManager] = None):
        """
        Initialize WebSocket service.

        Args:
            pubsub_manager: Optional Redis Pub/Sub manager (uses global instance by default)
        """
        self.pubsub_manager = pubsub_manager or redis_pubsub_manager

    async def publish_event(
        self,
        event: BaseEvent,
        room: Optional[str] = None,
    ) -> bool:
        """
        Publish a typed event.

        Args:
            event: Pydantic event model
            room: Optional room identifier for targeted messages

        Returns:
            bool: True if published successfully
        """
        try:
            # Serialize event
            event_dict = event.model_dump()

            # Add room if specified
            if room and "room" not in event_dict:
                event_dict["room"] = room

            # Publish via Redis Pub/Sub
            return await self.pubsub_manager.publish_event(
                event_type=event.type,
                data=event_dict,
                room=room,
            )

        except Exception as e:
            logger.error(f"Failed to publish event {event.type}: {e}")
            return False

    # Campaign Events
    async def campaign_launched(
        self,
        campaign_id: int,
        campaign_name: str,
        total_recipients: int,
        scheduled_at: Optional[str] = None,
    ) -> bool:
        """Publish campaign launched event."""
        event = CampaignLaunchedEvent(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            total_recipients=total_recipients,
            scheduled_at=scheduled_at,
        )
        return await self.publish_event(event, room=f"campaign:{campaign_id}")

    async def campaign_paused(
        self,
        campaign_id: int,
        campaign_name: str,
        emails_sent: int,
        emails_remaining: int,
    ) -> bool:
        """Publish campaign paused event."""
        event = CampaignPausedEvent(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            emails_sent=emails_sent,
            emails_remaining=emails_remaining,
        )
        return await self.publish_event(event, room=f"campaign:{campaign_id}")

    async def campaign_resumed(
        self,
        campaign_id: int,
        campaign_name: str,
        emails_remaining: int,
    ) -> bool:
        """Publish campaign resumed event."""
        event = CampaignResumedEvent(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            emails_remaining=emails_remaining,
        )
        return await self.publish_event(event, room=f"campaign:{campaign_id}")

    async def campaign_completed(
        self,
        campaign_id: int,
        campaign_name: str,
        total_sent: int,
        total_opened: int,
        total_clicked: int,
        total_replied: int,
        open_rate: float,
        click_rate: float,
        reply_rate: float,
    ) -> bool:
        """Publish campaign completed event."""
        event = CampaignCompletedEvent(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            total_sent=total_sent,
            total_opened=total_opened,
            total_clicked=total_clicked,
            total_replied=total_replied,
            open_rate=open_rate,
            click_rate=click_rate,
            reply_rate=reply_rate,
        )
        return await self.publish_event(event, room=f"campaign:{campaign_id}")

    async def campaign_email_sent(
        self,
        campaign_id: int,
        recipient_id: int,
        lead_id: int,
        to_email: str,
        subject: str,
    ) -> bool:
        """Publish campaign email sent event."""
        event = CampaignEmailSentEvent(
            campaign_id=campaign_id,
            recipient_id=recipient_id,
            lead_id=lead_id,
            to_email=to_email,
            subject=subject,
        )
        return await self.publish_event(event, room=f"campaign:{campaign_id}")

    async def campaign_email_failed(
        self,
        campaign_id: int,
        recipient_id: int,
        lead_id: int,
        to_email: str,
        error: str,
        retry_count: int,
    ) -> bool:
        """Publish campaign email failed event."""
        event = CampaignEmailFailedEvent(
            campaign_id=campaign_id,
            recipient_id=recipient_id,
            lead_id=lead_id,
            to_email=to_email,
            error=error,
            retry_count=retry_count,
        )
        return await self.publish_event(event, room=f"campaign:{campaign_id}")

    async def campaign_stats_updated(
        self,
        campaign_id: int,
        emails_sent: int,
        emails_opened: int,
        emails_clicked: int,
        emails_replied: int,
        emails_bounced: int,
        open_rate: float,
        click_rate: float,
        reply_rate: float,
        bounce_rate: float,
    ) -> bool:
        """Publish campaign stats updated event."""
        event = CampaignStatsUpdatedEvent(
            campaign_id=campaign_id,
            emails_sent=emails_sent,
            emails_opened=emails_opened,
            emails_clicked=emails_clicked,
            emails_replied=emails_replied,
            emails_bounced=emails_bounced,
            open_rate=open_rate,
            click_rate=click_rate,
            reply_rate=reply_rate,
            bounce_rate=bounce_rate,
        )
        return await self.publish_event(event, room=f"campaign:{campaign_id}")

    # Email Events
    async def email_sent(
        self,
        to_email: str,
        subject: str,
        message_id: str,
        provider: str,
        email_id: Optional[int] = None,
    ) -> bool:
        """Publish email sent event."""
        event = EmailSentEvent(
            email_id=email_id,
            to_email=to_email,
            subject=subject,
            message_id=message_id,
            provider=provider,
        )
        return await self.publish_event(event)

    async def email_opened(
        self,
        to_email: str,
        opened_at: str,
        email_id: Optional[int] = None,
        campaign_id: Optional[int] = None,
        lead_id: Optional[int] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> bool:
        """Publish email opened event."""
        event = EmailOpenedEvent(
            email_id=email_id,
            campaign_id=campaign_id,
            lead_id=lead_id,
            to_email=to_email,
            opened_at=opened_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        room = f"campaign:{campaign_id}" if campaign_id else None
        return await self.publish_event(event, room=room)

    async def email_clicked(
        self,
        to_email: str,
        url: str,
        clicked_at: str,
        email_id: Optional[int] = None,
        campaign_id: Optional[int] = None,
        lead_id: Optional[int] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """Publish email clicked event."""
        event = EmailClickedEvent(
            email_id=email_id,
            campaign_id=campaign_id,
            lead_id=lead_id,
            to_email=to_email,
            url=url,
            clicked_at=clicked_at,
            user_agent=user_agent,
        )
        room = f"campaign:{campaign_id}" if campaign_id else None
        return await self.publish_event(event, room=room)

    # Scraper Events
    async def scraper_started(
        self,
        scraper_id: str,
        source: str,
        max_results: int,
        location: Optional[str] = None,
        category: Optional[str] = None,
    ) -> bool:
        """Publish scraper started event."""
        event = ScraperStartedEvent(
            scraper_id=scraper_id,
            source=source,
            location=location,
            category=category,
            max_results=max_results,
        )
        return await self.publish_event(event, room=f"scraper:{scraper_id}")

    async def scraper_progress(
        self,
        scraper_id: str,
        source: str,
        current: int,
        total: int,
        leads_found: int,
        message: Optional[str] = None,
    ) -> bool:
        """Publish scraper progress event."""
        percent = (current / total * 100) if total > 0 else 0
        event = ScraperProgressEvent(
            scraper_id=scraper_id,
            source=source,
            current=current,
            total=total,
            percent=round(percent, 2),
            leads_found=leads_found,
            message=message,
        )
        return await self.publish_event(event, room=f"scraper:{scraper_id}")

    async def scraper_lead_found(
        self,
        scraper_id: str,
        source: str,
        lead_id: int,
        lead_name: Optional[str] = None,
        lead_email: Optional[str] = None,
    ) -> bool:
        """Publish scraper lead found event."""
        event = ScraperLeadFoundEvent(
            scraper_id=scraper_id,
            source=source,
            lead_id=lead_id,
            lead_name=lead_name,
            lead_email=lead_email,
        )
        return await self.publish_event(event, room=f"scraper:{scraper_id}")

    async def scraper_completed(
        self,
        scraper_id: str,
        source: str,
        total_leads: int,
        leads_created: int,
        leads_updated: int,
        duration_seconds: float,
        success: bool = True,
    ) -> bool:
        """Publish scraper completed event."""
        event = ScraperCompletedEvent(
            scraper_id=scraper_id,
            source=source,
            total_leads=total_leads,
            leads_created=leads_created,
            leads_updated=leads_updated,
            duration_seconds=duration_seconds,
            success=success,
        )
        return await self.publish_event(event, room=f"scraper:{scraper_id}")

    async def scraper_failed(
        self,
        scraper_id: str,
        source: str,
        error: str,
        partial_results: int = 0,
    ) -> bool:
        """Publish scraper failed event."""
        event = ScraperFailedEvent(
            scraper_id=scraper_id,
            source=source,
            error=error,
            partial_results=partial_results,
        )
        return await self.publish_event(event, room=f"scraper:{scraper_id}")

    # AI Events
    async def ai_processing(
        self,
        task_id: str,
        task_type: str,
        resource_id: Optional[int] = None,
    ) -> bool:
        """Publish AI processing event."""
        event = AIProcessingEvent(
            task_id=task_id,
            task_type=task_type,
            resource_id=resource_id,
        )
        return await self.publish_event(event)

    async def ai_response_ready(
        self,
        task_id: str,
        conversation_id: int,
        response: str,
        confidence: float,
        tokens_used: int,
    ) -> bool:
        """Publish AI response ready event."""
        event = AIResponseReadyEvent(
            task_id=task_id,
            conversation_id=conversation_id,
            response=response,
            confidence=confidence,
            tokens_used=tokens_used,
        )
        return await self.publish_event(event, room=f"conversation:{conversation_id}")

    async def ai_lead_analyzed(
        self,
        lead_id: int,
        quality_score: float,
        tags: list,
        priority: str,
    ) -> bool:
        """Publish AI lead analyzed event."""
        event = AILeadAnalyzedEvent(
            lead_id=lead_id,
            quality_score=quality_score,
            tags=tags,
            priority=priority,
        )
        return await self.publish_event(event, room=f"lead:{lead_id}")

    # Demo Events
    async def demo_generating(
        self,
        demo_id: str,
        lead_id: int,
        template: str,
    ) -> bool:
        """Publish demo generating event."""
        event = DemoGeneratingEvent(
            demo_id=demo_id,
            lead_id=lead_id,
            template=template,
        )
        return await self.publish_event(event, room=f"demo:{demo_id}")

    async def demo_completed(
        self,
        demo_id: str,
        lead_id: int,
        demo_url: str,
        duration_seconds: float,
        video_url: Optional[str] = None,
    ) -> bool:
        """Publish demo completed event."""
        event = DemoCompletedEvent(
            demo_id=demo_id,
            lead_id=lead_id,
            demo_url=demo_url,
            video_url=video_url,
            duration_seconds=duration_seconds,
        )
        return await self.publish_event(event, room=f"demo:{demo_id}")

    async def demo_failed(
        self,
        demo_id: str,
        lead_id: int,
        error: str,
        step_failed: str,
    ) -> bool:
        """Publish demo failed event."""
        event = DemoFailedEvent(
            demo_id=demo_id,
            lead_id=lead_id,
            error=error,
            step_failed=step_failed,
        )
        return await self.publish_event(event, room=f"demo:{demo_id}")

    # Lead Events
    async def lead_created(
        self,
        lead_id: int,
        source: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        location: Optional[str] = None,
    ) -> bool:
        """Publish lead created event."""
        event = LeadCreatedEvent(
            lead_id=lead_id,
            name=name,
            email=email,
            source=source,
            location=location,
        )
        return await self.publish_event(event)

    async def lead_updated(
        self,
        lead_id: int,
        updates: Dict[str, Any],
    ) -> bool:
        """Publish lead updated event."""
        event = LeadUpdatedEvent(
            lead_id=lead_id,
            updates=updates,
        )
        return await self.publish_event(event, room=f"lead:{lead_id}")

    # System Notifications
    async def system_notification(
        self,
        level: str,
        title: str,
        message: str,
        action_url: Optional[str] = None,
    ) -> bool:
        """Publish system notification event."""
        event = SystemNotificationEvent(
            level=level,
            title=title,
            message=message,
            action_url=action_url,
        )
        return await self.publish_event(event)


# Global service instance
websocket_service = WebSocketService()
