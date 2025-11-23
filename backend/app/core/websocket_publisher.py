"""
Synchronous WebSocket Event Publisher for Celery Tasks

This module provides a synchronous wrapper around the WebSocket service
for use in Celery tasks (which are synchronous). It handles async/sync bridging
and Redis connection management.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from functools import wraps

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class SyncWebSocketPublisher:
    """
    Synchronous WebSocket event publisher for use in Celery tasks.

    This class publishes events to Redis Pub/Sub channels, which are then
    consumed by the WebSocket server and pushed to connected clients.
    """

    def __init__(self):
        """Initialize synchronous Redis client."""
        self.redis_client: Optional[redis.Redis] = None
        self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis client."""
        if not settings.REDIS_URL:
            logger.warning("REDIS_URL not configured, WebSocket publishing disabled")
            return

        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Sync WebSocket publisher connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """
        Publish a message to a Redis channel.

        Args:
            channel: Redis channel name
            message: Message dictionary (will be JSON serialized)

        Returns:
            bool: True if published successfully
        """
        if not self.redis_client:
            logger.warning("Redis client not available, cannot publish message")
            return False

        try:
            import json
            from datetime import datetime

            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.utcnow().isoformat()

            # Serialize and publish
            message_json = json.dumps(message)
            self.redis_client.publish(channel, message_json)

            logger.debug(f"Published to {channel}: {message.get('type', 'unknown')}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish to {channel}: {e}")
            return False

    # Campaign Events
    def campaign_launched(
        self,
        campaign_id: int,
        campaign_name: str,
        total_recipients: int,
        scheduled_at: Optional[str] = None,
    ) -> bool:
        """Publish campaign launched event."""
        return self.publish("fliptechpro:campaigns", {
            "type": "campaign:launched",
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "total_recipients": total_recipients,
            "scheduled_at": scheduled_at,
            "room": f"campaign:{campaign_id}",
        })

    def campaign_paused(
        self,
        campaign_id: int,
        campaign_name: str,
        emails_sent: int,
        emails_remaining: int,
    ) -> bool:
        """Publish campaign paused event."""
        return self.publish("fliptechpro:campaigns", {
            "type": "campaign:paused",
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "emails_sent": emails_sent,
            "emails_remaining": emails_remaining,
            "room": f"campaign:{campaign_id}",
        })

    def campaign_resumed(
        self,
        campaign_id: int,
        campaign_name: str,
        emails_remaining: int,
    ) -> bool:
        """Publish campaign resumed event."""
        return self.publish("fliptechpro:campaigns", {
            "type": "campaign:resumed",
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "emails_remaining": emails_remaining,
            "room": f"campaign:{campaign_id}",
        })

    def campaign_completed(
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
        return self.publish("fliptechpro:campaigns", {
            "type": "campaign:completed",
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "total_sent": total_sent,
            "total_opened": total_opened,
            "total_clicked": total_clicked,
            "total_replied": total_replied,
            "open_rate": open_rate,
            "click_rate": click_rate,
            "reply_rate": reply_rate,
            "room": f"campaign:{campaign_id}",
        })

    def campaign_stats_updated(
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
        return self.publish("fliptechpro:campaigns", {
            "type": "campaign:stats_updated",
            "campaign_id": campaign_id,
            "emails_sent": emails_sent,
            "emails_opened": emails_opened,
            "emails_clicked": emails_clicked,
            "emails_replied": emails_replied,
            "emails_bounced": emails_bounced,
            "open_rate": open_rate,
            "click_rate": click_rate,
            "reply_rate": reply_rate,
            "bounce_rate": bounce_rate,
            "room": f"campaign:{campaign_id}",
        })

    # Email Events
    def email_sent(
        self,
        to_email: str,
        subject: str,
        message_id: str,
        provider: str,
        campaign_id: Optional[int] = None,
    ) -> bool:
        """Publish email sent event."""
        message = {
            "type": "email:sent",
            "to_email": to_email,
            "subject": subject,
            "message_id": message_id,
            "provider": provider,
        }
        if campaign_id:
            message["campaign_id"] = campaign_id
            message["room"] = f"campaign:{campaign_id}"
        return self.publish("fliptechpro:emails", message)

    def email_opened(
        self,
        to_email: str,
        opened_at: str,
        campaign_id: Optional[int] = None,
        lead_id: Optional[int] = None,
    ) -> bool:
        """Publish email opened event."""
        message = {
            "type": "email:opened",
            "to_email": to_email,
            "opened_at": opened_at,
        }
        if campaign_id:
            message["campaign_id"] = campaign_id
            message["room"] = f"campaign:{campaign_id}"
        if lead_id:
            message["lead_id"] = lead_id
        return self.publish("fliptechpro:emails", message)

    # Scraper Events
    def scraper_started(
        self,
        scraper_id: str,
        source: str,
        max_results: int,
        location: Optional[str] = None,
        category: Optional[str] = None,
    ) -> bool:
        """Publish scraper started event."""
        return self.publish("fliptechpro:scrapers", {
            "type": "scraper:started",
            "scraper_id": scraper_id,
            "source": source,
            "location": location,
            "category": category,
            "max_results": max_results,
            "room": f"scraper:{scraper_id}",
        })

    def scraper_progress(
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
        return self.publish("fliptechpro:scrapers", {
            "type": "scraper:progress",
            "scraper_id": scraper_id,
            "source": source,
            "current": current,
            "total": total,
            "percent": round(percent, 2),
            "leads_found": leads_found,
            "message": message,
            "room": f"scraper:{scraper_id}",
        })

    def scraper_lead_found(
        self,
        scraper_id: str,
        source: str,
        lead_id: int,
        lead_name: Optional[str] = None,
        lead_email: Optional[str] = None,
    ) -> bool:
        """Publish scraper lead found event."""
        return self.publish("fliptechpro:scrapers", {
            "type": "scraper:lead_found",
            "scraper_id": scraper_id,
            "source": source,
            "lead_id": lead_id,
            "lead_name": lead_name,
            "lead_email": lead_email,
            "room": f"scraper:{scraper_id}",
        })

    def scraper_completed(
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
        return self.publish("fliptechpro:scrapers", {
            "type": "scraper:completed",
            "scraper_id": scraper_id,
            "source": source,
            "total_leads": total_leads,
            "leads_created": leads_created,
            "leads_updated": leads_updated,
            "duration_seconds": duration_seconds,
            "success": success,
            "room": f"scraper:{scraper_id}",
        })

    def scraper_failed(
        self,
        scraper_id: str,
        source: str,
        error: str,
        partial_results: int = 0,
    ) -> bool:
        """Publish scraper failed event."""
        return self.publish("fliptechpro:scrapers", {
            "type": "scraper:failed",
            "scraper_id": scraper_id,
            "source": source,
            "error": error,
            "partial_results": partial_results,
            "room": f"scraper:{scraper_id}",
        })

    # AI Events
    def ai_processing(
        self,
        task_id: str,
        task_type: str,
        resource_id: Optional[int] = None,
    ) -> bool:
        """Publish AI processing event."""
        return self.publish("fliptechpro:ai", {
            "type": "ai:processing",
            "task_id": task_id,
            "task_type": task_type,
            "resource_id": resource_id,
        })

    def ai_response_ready(
        self,
        task_id: str,
        conversation_id: int,
        response: str,
        confidence: float,
        tokens_used: int,
    ) -> bool:
        """Publish AI response ready event."""
        return self.publish("fliptechpro:ai", {
            "type": "ai:response_ready",
            "task_id": task_id,
            "conversation_id": conversation_id,
            "response": response,
            "confidence": confidence,
            "tokens_used": tokens_used,
            "room": f"conversation:{conversation_id}",
        })

    # Demo Events
    def demo_generating(
        self,
        demo_id: str,
        lead_id: int,
        template: str,
    ) -> bool:
        """Publish demo generating event."""
        return self.publish("fliptechpro:demos", {
            "type": "demo:generating",
            "demo_id": demo_id,
            "lead_id": lead_id,
            "template": template,
            "room": f"demo:{demo_id}",
        })

    def demo_composing(
        self,
        demo_id: str,
        progress_percent: float,
        current_step: str,
    ) -> bool:
        """Publish demo composing event."""
        return self.publish("fliptechpro:demos", {
            "type": "demo:composing",
            "demo_id": demo_id,
            "progress_percent": progress_percent,
            "current_step": current_step,
            "room": f"demo:{demo_id}",
        })

    def demo_completed(
        self,
        demo_id: str,
        lead_id: int,
        demo_url: str,
        duration_seconds: float,
        video_url: Optional[str] = None,
    ) -> bool:
        """Publish demo completed event."""
        return self.publish("fliptechpro:demos", {
            "type": "demo:completed",
            "demo_id": demo_id,
            "lead_id": lead_id,
            "demo_url": demo_url,
            "video_url": video_url,
            "duration_seconds": duration_seconds,
            "room": f"demo:{demo_id}",
        })

    def demo_failed(
        self,
        demo_id: str,
        lead_id: int,
        error: str,
        step_failed: str,
    ) -> bool:
        """Publish demo failed event."""
        return self.publish("fliptechpro:demos", {
            "type": "demo:failed",
            "demo_id": demo_id,
            "lead_id": lead_id,
            "error": error,
            "step_failed": step_failed,
            "room": f"demo:{demo_id}",
        })

    # Lead Events
    def lead_created(
        self,
        lead_id: int,
        source: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        location: Optional[str] = None,
    ) -> bool:
        """Publish lead created event."""
        return self.publish("fliptechpro:leads", {
            "type": "lead:created",
            "lead_id": lead_id,
            "name": name,
            "email": email,
            "source": source,
            "location": location,
        })

    # System Notifications
    def system_notification(
        self,
        level: str,
        title: str,
        message: str,
        action_url: Optional[str] = None,
    ) -> bool:
        """Publish system notification event."""
        return self.publish("fliptechpro:notifications", {
            "type": "notification:system",
            "level": level,
            "title": title,
            "message": message,
            "action_url": action_url,
        })


# Global instance for use in Celery tasks
ws_publisher = SyncWebSocketPublisher()
