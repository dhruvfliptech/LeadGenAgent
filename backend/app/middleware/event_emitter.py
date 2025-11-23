"""
Event emitter middleware for automatic webhook triggers.

This module sets up SQLAlchemy event listeners to automatically trigger
webhooks when database records are created or updated.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.models.leads import Lead
from app.models.demo_sites import DemoSite
from app.models.composed_videos import ComposedVideo
from app.services.n8n_webhook_trigger import get_webhook_trigger

logger = logging.getLogger(__name__)

# Track if listeners have been set up
_listeners_setup = False


def setup_event_listeners():
    """
    Set up SQLAlchemy event listeners to trigger webhooks.

    This function should be called once during application startup
    to register all event listeners for automatic webhook triggering.

    Example:
        >>> from app.middleware.event_emitter import setup_event_listeners
        >>> setup_event_listeners()
    """
    global _listeners_setup

    if _listeners_setup:
        logger.debug("Event listeners already set up")
        return

    logger.info("Setting up webhook event listeners")

    # Lead events
    event.listen(Lead, 'after_insert', _on_lead_created)
    event.listen(Lead, 'after_update', _on_lead_updated)

    # Demo site events
    event.listen(DemoSite, 'after_insert', _on_demo_created)
    event.listen(DemoSite, 'after_update', _on_demo_updated)

    # Video events
    event.listen(ComposedVideo, 'after_insert', _on_video_created)
    event.listen(ComposedVideo, 'after_update', _on_video_updated)

    _listeners_setup = True
    logger.info("Webhook event listeners configured successfully")


def _on_lead_created(mapper, connection, target: Lead):
    """
    Trigger webhook when lead is created.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: Lead instance
    """
    try:
        logger.debug(f"Lead created event: id={target.id}")

        # Prepare lead data
        lead_data = {
            "lead_id": target.id,
            "title": target.title,
            "category": target.category,
            "location": target.location.name if target.location else None,
            "source": target.source,
            "url": target.url,
            "created_at": target.created_at.isoformat() if target.created_at else None
        }

        # Emit webhook asynchronously
        emit_webhook_event('lead_scraped', target.id, lead_data, entity_type='lead')

    except Exception as e:
        logger.error(f"Error in lead created event handler: {str(e)}", exc_info=True)


def _on_lead_updated(mapper, connection, target: Lead):
    """
    Trigger webhook when lead status changes.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: Lead instance
    """
    try:
        # Get the previous state
        history = connection.execute(
            "SELECT status, has_been_qualified FROM leads WHERE id = %s",
            (target.id,)
        ).fetchone()

        if not history:
            return

        old_status = history[0] if len(history) > 0 else None
        old_qualified = history[1] if len(history) > 1 else False

        # Check if qualification status changed
        if target.has_been_qualified and not old_qualified:
            logger.debug(f"Lead qualified event: id={target.id}")

            qualification_data = {
                "lead_id": target.id,
                "qualification_score": target.qualification_score,
                "qualification_reasoning": target.qualification_reasoning,
                "qualified_at": target.qualified_at.isoformat() if target.qualified_at else None
            }

            emit_webhook_event('lead_qualified', target.id, qualification_data, entity_type='lead')

        # Check if lead responded
        if target.status == 'responded' and old_status != 'responded':
            logger.debug(f"Lead responded event: id={target.id}")

            response_data = {
                "lead_id": target.id,
                "status": target.status,
                "response_sent_at": target.response_sent_at.isoformat() if target.response_sent_at else None
            }

            emit_webhook_event('lead_responded', target.id, response_data, entity_type='lead')

    except Exception as e:
        logger.error(f"Error in lead updated event handler: {str(e)}", exc_info=True)


def _on_demo_created(mapper, connection, target: DemoSite):
    """
    Trigger webhook when demo site is created.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: DemoSite instance
    """
    try:
        logger.debug(f"Demo site created event: id={target.id}")
        # Demo creation doesn't trigger webhook - only completion does

    except Exception as e:
        logger.error(f"Error in demo created event handler: {str(e)}", exc_info=True)


def _on_demo_updated(mapper, connection, target: DemoSite):
    """
    Trigger webhook when demo deployment status changes.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: DemoSite instance
    """
    try:
        # Get the previous status
        history = connection.execute(
            "SELECT status FROM demo_sites WHERE id = %s",
            (target.id,)
        ).fetchone()

        if not history:
            return

        old_status = history[0] if len(history) > 0 else None

        # Check if deployment completed
        if target.status == 'ready' and old_status != 'ready':
            logger.debug(f"Demo completed event: id={target.id}")

            demo_data = {
                "demo_site_id": target.id,
                "lead_id": target.lead_id,
                "url": target.url,
                "preview_url": target.preview_url,
                "project_name": target.project_name,
                "framework": target.framework,
                "deployed_at": target.deployed_at.isoformat() if target.deployed_at else None
            }

            emit_webhook_event('demo_completed', target.id, demo_data, entity_type='demo_site', priority=1)

        # Check if deployment failed
        elif target.status == 'error' and old_status != 'error':
            logger.debug(f"Demo failed event: id={target.id}")

            error_data = {
                "demo_site_id": target.id,
                "lead_id": target.lead_id,
                "error_message": target.error_message,
                "project_name": target.project_name
            }

            emit_webhook_event('demo_failed', target.id, error_data, entity_type='demo_site', priority=2)

    except Exception as e:
        logger.error(f"Error in demo updated event handler: {str(e)}", exc_info=True)


def _on_video_created(mapper, connection, target: ComposedVideo):
    """
    Trigger webhook when video is created.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: ComposedVideo instance
    """
    try:
        logger.debug(f"Video created event: id={target.id}")
        # Video creation doesn't trigger webhook - only completion does

    except Exception as e:
        logger.error(f"Error in video created event handler: {str(e)}", exc_info=True)


def _on_video_updated(mapper, connection, target: ComposedVideo):
    """
    Trigger webhook when video generation status changes.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: ComposedVideo instance
    """
    try:
        # Get the previous status
        history = connection.execute(
            "SELECT status FROM composed_videos WHERE id = %s",
            (target.id,)
        ).fetchone()

        if not history:
            return

        old_status = history[0] if len(history) > 0 else None

        # Check if video completed
        if target.status == 'completed' and old_status != 'completed':
            logger.debug(f"Video completed event: id={target.id}")

            video_data = {
                "video_id": target.id,
                "lead_id": target.lead_id,
                "demo_site_id": target.demo_site_id,
                "output_url": target.output_url,
                "duration": target.duration,
                "completed_at": target.completed_at.isoformat() if target.completed_at else None
            }

            emit_webhook_event('video_completed', target.id, video_data, entity_type='video', priority=1)

        # Check if video failed
        elif target.status == 'failed' and old_status != 'failed':
            logger.debug(f"Video failed event: id={target.id}")

            error_data = {
                "video_id": target.id,
                "lead_id": target.lead_id,
                "error_message": target.error_message
            }

            emit_webhook_event('video_failed', target.id, error_data, entity_type='video', priority=2)

    except Exception as e:
        logger.error(f"Error in video updated event handler: {str(e)}", exc_info=True)


def emit_webhook_event(
    event_type: str,
    entity_id: int,
    data: Dict[str, Any],
    entity_type: Optional[str] = None,
    priority: int = 0
):
    """
    Emit a webhook event asynchronously.

    This function schedules a webhook to be sent without blocking
    the current database transaction.

    Args:
        event_type: Type of event (lead_scraped, demo_completed, etc.)
        entity_id: Entity ID
        data: Event data
        entity_type: Entity type (lead, demo_site, video)
        priority: Priority level

    Example:
        >>> emit_webhook_event(
        ...     'lead_scraped',
        ...     123,
        ...     {"lead_id": 123, "name": "Acme Inc"},
        ...     entity_type='lead'
        ... )
    """
    try:
        # Get the event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No event loop running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Create task to send webhook
        loop.create_task(_send_webhook_async(event_type, entity_id, data, entity_type, priority))

    except Exception as e:
        logger.error(f"Error emitting webhook event: {str(e)}", exc_info=True)


async def _send_webhook_async(
    event_type: str,
    entity_id: int,
    data: Dict[str, Any],
    entity_type: Optional[str],
    priority: int
):
    """
    Send webhook asynchronously.

    Args:
        event_type: Type of event
        entity_id: Entity ID
        data: Event data
        entity_type: Entity type
        priority: Priority level
    """
    try:
        trigger = get_webhook_trigger()

        # Map event type to trigger method
        if event_type == 'lead_scraped':
            await trigger.trigger_lead_scraped(entity_id, data)
        elif event_type == 'lead_qualified':
            await trigger.trigger_lead_qualified(entity_id, data)
        elif event_type == 'demo_completed':
            await trigger.trigger_demo_completed(entity_id, data)
        elif event_type == 'demo_failed':
            await trigger.trigger_demo_failed(entity_id, data)
        elif event_type == 'video_completed':
            await trigger.trigger_video_completed(entity_id, data)
        elif event_type == 'video_failed':
            await trigger.trigger_video_failed(entity_id, data)
        elif event_type == 'lead_responded':
            await trigger.trigger_lead_responded(entity_id, data)
        else:
            logger.warning(f"Unknown webhook event type: {event_type}")

    except Exception as e:
        logger.error(
            f"Error sending webhook: event_type={event_type}, "
            f"entity_id={entity_id}, error={str(e)}",
            exc_info=True
        )


def remove_event_listeners():
    """
    Remove all event listeners.

    This function should be called during application shutdown
    or when testing to clean up event listeners.
    """
    global _listeners_setup

    if not _listeners_setup:
        return

    logger.info("Removing webhook event listeners")

    # Remove all listeners
    event.remove(Lead, 'after_insert', _on_lead_created)
    event.remove(Lead, 'after_update', _on_lead_updated)
    event.remove(DemoSite, 'after_insert', _on_demo_created)
    event.remove(DemoSite, 'after_update', _on_demo_updated)
    event.remove(ComposedVideo, 'after_insert', _on_video_created)
    event.remove(ComposedVideo, 'after_update', _on_video_updated)

    _listeners_setup = False
    logger.info("Webhook event listeners removed")
