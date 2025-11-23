"""
Webhook queue service for reliable webhook delivery.

This service manages a persistent queue of webhooks with retry logic,
ensuring reliable delivery even when external services are temporarily unavailable.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.webhook_queue import (
    WebhookQueueItem,
    WebhookLog,
    WebhookRetryHistory,
    WebhookStatus
)
from app.services.n8n_webhook_trigger import N8nWebhookTrigger
from app.core.webhook_config import webhook_config

logger = logging.getLogger(__name__)


class WebhookQueue:
    """
    Reliable webhook delivery with retry and queue management.

    This service provides persistent webhook queuing with automatic
    retry, prioritization, and comprehensive logging.
    """

    def __init__(self, db: Session):
        """
        Initialize webhook queue service.

        Args:
            db: Database session
        """
        self.db = db
        self.config = webhook_config
        self.webhook_trigger = N8nWebhookTrigger()
        self._processing = False
        self._process_task: Optional[asyncio.Task] = None

    async def enqueue(
        self,
        webhook_url: str,
        payload: Dict[str, Any],
        event_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        priority: int = 0,
        max_retries: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Add webhook to queue.

        Args:
            webhook_url: URL to send webhook to
            payload: Webhook payload
            event_type: Type of event
            entity_type: Entity type (lead, demo_site, video)
            entity_id: Entity ID
            priority: Priority level (0=normal, higher=more important)
            max_retries: Maximum retry attempts
            headers: Custom headers
            metadata: Additional metadata

        Returns:
            Webhook queue item ID

        Example:
            >>> queue = WebhookQueue(db)
            >>> webhook_id = await queue.enqueue(
            ...     webhook_url="https://n8n.example.com/webhook/lead-scraped",
            ...     payload={"lead_id": 123, "name": "Acme Inc"},
            ...     event_type="lead_scraped",
            ...     entity_type="lead",
            ...     entity_id=123,
            ...     priority=0
            ... )
        """
        if max_retries is None:
            max_retries = self.config.retry.max_retries

        # Create queue item
        queue_item = WebhookQueueItem(
            webhook_url=webhook_url,
            payload=payload,
            headers=headers,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            status=WebhookStatus.PENDING.value,
            priority=priority,
            max_retries=max_retries,
            retry_count=0,
            metadata=metadata,
            created_at=datetime.utcnow()
        )

        self.db.add(queue_item)
        self.db.commit()
        self.db.refresh(queue_item)

        logger.info(
            f"Webhook enqueued: id={queue_item.id}, event_type={event_type}, "
            f"entity={entity_type}:{entity_id}, priority={priority}"
        )

        return queue_item.id

    async def process_queue(self):
        """
        Background task to process webhook queue.

        This method runs continuously, processing pending webhooks
        from the queue with retry logic.
        """
        if not self.config.queue.enabled:
            logger.info("Webhook queue processing is disabled")
            return

        logger.info("Starting webhook queue processor")
        self._processing = True

        while self._processing:
            try:
                # Get pending webhooks
                pending_webhooks = self._get_pending_webhooks()

                if pending_webhooks:
                    logger.info(f"Processing {len(pending_webhooks)} pending webhooks")
                    await self._process_webhooks(pending_webhooks)
                else:
                    logger.debug("No pending webhooks to process")

                # Wait before next iteration
                await asyncio.sleep(self.config.queue.processing_interval)

            except Exception as e:
                logger.error(f"Error in webhook queue processor: {str(e)}", exc_info=True)
                await asyncio.sleep(self.config.queue.processing_interval)

        logger.info("Webhook queue processor stopped")

    def _get_pending_webhooks(self) -> List[WebhookQueueItem]:
        """
        Get pending webhooks from queue.

        Returns:
            List of webhook queue items ready for processing
        """
        now = datetime.utcnow()

        # Query for pending webhooks
        query = self.db.query(WebhookQueueItem).filter(
            and_(
                WebhookQueueItem.status.in_([
                    WebhookStatus.PENDING.value,
                    WebhookStatus.FAILED.value
                ]),
                WebhookQueueItem.retry_count < WebhookQueueItem.max_retries,
                or_(
                    WebhookQueueItem.next_retry_at.is_(None),
                    WebhookQueueItem.next_retry_at <= now
                )
            )
        )

        # Apply priority ordering if enabled
        if self.config.queue.priority_enabled:
            query = query.order_by(
                WebhookQueueItem.priority.desc(),
                WebhookQueueItem.created_at.asc()
            )
        else:
            query = query.order_by(WebhookQueueItem.created_at.asc())

        # Limit batch size
        webhooks = query.limit(self.config.queue.batch_size).all()

        return webhooks

    async def _process_webhooks(self, webhooks: List[WebhookQueueItem]):
        """
        Process a batch of webhooks.

        Args:
            webhooks: List of webhook queue items to process
        """
        tasks = []
        for webhook in webhooks:
            task = self._process_single_webhook(webhook)
            tasks.append(task)

        # Process all webhooks concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_single_webhook(self, webhook: WebhookQueueItem):
        """
        Process a single webhook from the queue.

        Args:
            webhook: Webhook queue item to process
        """
        try:
            # Update status to sending
            webhook.status = WebhookStatus.SENDING.value
            self.db.commit()

            # Log attempt
            start_time = datetime.utcnow()

            # Send webhook
            success = await self.webhook_trigger.send_webhook(
                webhook_url=webhook.webhook_url,
                data=webhook.payload,
                headers=webhook.headers,
                retry_count=0,  # Queue handles retries
                entity_type=webhook.entity_type,
                entity_id=webhook.entity_id,
                priority=webhook.priority
            )

            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Record retry attempt
            retry_history = WebhookRetryHistory(
                webhook_queue_id=webhook.id,
                attempt_number=webhook.retry_count + 1,
                status="sent" if success else "failed",
                response_time_ms=duration_ms,
                attempted_at=datetime.utcnow()
            )
            self.db.add(retry_history)

            if success:
                # Mark as sent
                webhook.status = WebhookStatus.SENT.value
                webhook.sent_at = datetime.utcnow()
                logger.info(f"Webhook sent successfully: id={webhook.id}, event_type={webhook.event_type}")

            else:
                # Update retry count
                webhook.retry_count += 1

                # Check if should retry
                if webhook.retry_count < webhook.max_retries:
                    # Calculate next retry time
                    webhook.next_retry_at = webhook.calculate_next_retry(
                        self.config.retry.retry_delays
                    )
                    webhook.status = WebhookStatus.FAILED.value
                    logger.warning(
                        f"Webhook failed, will retry: id={webhook.id}, "
                        f"attempt={webhook.retry_count}/{webhook.max_retries}, "
                        f"next_retry={webhook.next_retry_at}"
                    )
                else:
                    # Max retries reached
                    webhook.status = WebhookStatus.FAILED.value
                    webhook.failed_at = datetime.utcnow()
                    webhook.last_error = "Maximum retry attempts reached"
                    logger.error(
                        f"Webhook failed permanently after {webhook.max_retries} attempts: "
                        f"id={webhook.id}, event_type={webhook.event_type}"
                    )

            self.db.commit()

            # Create webhook log
            await self._log_webhook(webhook, success, duration_ms)

        except Exception as e:
            logger.error(f"Error processing webhook {webhook.id}: {str(e)}", exc_info=True)

            # Update webhook with error
            webhook.retry_count += 1
            webhook.last_error = str(e)
            webhook.error_details = {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

            if webhook.retry_count < webhook.max_retries:
                webhook.next_retry_at = webhook.calculate_next_retry(
                    self.config.retry.retry_delays
                )
                webhook.status = WebhookStatus.FAILED.value
            else:
                webhook.status = WebhookStatus.FAILED.value
                webhook.failed_at = datetime.utcnow()

            self.db.commit()

    async def _log_webhook(
        self,
        webhook: WebhookQueueItem,
        success: bool,
        duration_ms: int
    ):
        """
        Log webhook attempt.

        Args:
            webhook: Webhook queue item
            success: Whether webhook was successful
            duration_ms: Duration in milliseconds
        """
        try:
            log_entry = WebhookLog(
                direction="outgoing",
                event_type=webhook.event_type,
                webhook_url=webhook.webhook_url,
                method="POST",
                headers=webhook.headers,
                payload=webhook.payload,
                response_status=200 if success else 500,
                duration_ms=duration_ms,
                error_message=webhook.last_error if not success else None,
                entity_type=webhook.entity_type,
                entity_id=webhook.entity_id,
                webhook_queue_id=webhook.id,
                signature=webhook.signature,
                metadata=webhook.metadata,
                created_at=datetime.utcnow()
            )

            self.db.add(log_entry)
            self.db.commit()

        except Exception as e:
            logger.error(f"Error logging webhook: {str(e)}", exc_info=True)

    async def retry_failed(self, webhook_id: int) -> bool:
        """
        Manually retry a failed webhook.

        Args:
            webhook_id: Webhook queue item ID

        Returns:
            True if webhook was found and reset for retry

        Example:
            >>> queue = WebhookQueue(db)
            >>> success = await queue.retry_failed(123)
        """
        webhook = self.db.query(WebhookQueueItem).filter(
            WebhookQueueItem.id == webhook_id
        ).first()

        if not webhook:
            logger.warning(f"Webhook not found: id={webhook_id}")
            return False

        # Reset webhook for retry
        webhook.status = WebhookStatus.PENDING.value
        webhook.next_retry_at = None
        webhook.last_error = None
        webhook.retry_count = 0

        self.db.commit()

        logger.info(f"Webhook reset for retry: id={webhook_id}")
        return True

    async def cancel_webhook(self, webhook_id: int) -> bool:
        """
        Cancel a pending webhook.

        Args:
            webhook_id: Webhook queue item ID

        Returns:
            True if webhook was cancelled

        Example:
            >>> queue = WebhookQueue(db)
            >>> success = await queue.cancel_webhook(123)
        """
        webhook = self.db.query(WebhookQueueItem).filter(
            WebhookQueueItem.id == webhook_id
        ).first()

        if not webhook:
            return False

        webhook.status = WebhookStatus.CANCELLED.value
        self.db.commit()

        logger.info(f"Webhook cancelled: id={webhook_id}")
        return True

    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            Dictionary with queue statistics

        Example:
            >>> queue = WebhookQueue(db)
            >>> stats = await queue.get_queue_stats()
            >>> print(stats['pending'])
        """
        pending_count = self.db.query(WebhookQueueItem).filter(
            WebhookQueueItem.status == WebhookStatus.PENDING.value
        ).count()

        sending_count = self.db.query(WebhookQueueItem).filter(
            WebhookQueueItem.status == WebhookStatus.SENDING.value
        ).count()

        sent_count = self.db.query(WebhookQueueItem).filter(
            WebhookQueueItem.status == WebhookStatus.SENT.value
        ).count()

        failed_count = self.db.query(WebhookQueueItem).filter(
            WebhookQueueItem.status == WebhookStatus.FAILED.value
        ).count()

        cancelled_count = self.db.query(WebhookQueueItem).filter(
            WebhookQueueItem.status == WebhookStatus.CANCELLED.value
        ).count()

        return {
            'pending': pending_count,
            'sending': sending_count,
            'sent': sent_count,
            'failed': failed_count,
            'cancelled': cancelled_count,
            'total': pending_count + sending_count + sent_count + failed_count + cancelled_count
        }

    async def cleanup_old_webhooks(self, days: Optional[int] = None):
        """
        Clean up old completed webhooks.

        Args:
            days: Number of days to keep (defaults to config)

        Example:
            >>> queue = WebhookQueue(db)
            >>> await queue.cleanup_old_webhooks(30)
        """
        if days is None:
            days = self.config.queue.cleanup_after_days

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Delete old sent webhooks
        deleted_sent = self.db.query(WebhookQueueItem).filter(
            and_(
                WebhookQueueItem.status == WebhookStatus.SENT.value,
                WebhookQueueItem.sent_at < cutoff_date
            )
        ).delete()

        # Delete old failed webhooks
        deleted_failed = self.db.query(WebhookQueueItem).filter(
            and_(
                WebhookQueueItem.status == WebhookStatus.FAILED.value,
                WebhookQueueItem.failed_at < cutoff_date
            )
        ).delete()

        # Delete old webhook logs
        deleted_logs = self.db.query(WebhookLog).filter(
            WebhookLog.created_at < cutoff_date
        ).delete()

        self.db.commit()

        logger.info(
            f"Cleaned up old webhooks: sent={deleted_sent}, "
            f"failed={deleted_failed}, logs={deleted_logs}"
        )

        return {
            'deleted_sent': deleted_sent,
            'deleted_failed': deleted_failed,
            'deleted_logs': deleted_logs
        }

    def start_processing(self):
        """Start background queue processing."""
        if self._process_task is None or self._process_task.done():
            self._process_task = asyncio.create_task(self.process_queue())
            logger.info("Webhook queue processing started")

    async def stop_processing(self):
        """Stop background queue processing."""
        self._processing = False
        if self._process_task and not self._process_task.done():
            await self._process_task
            logger.info("Webhook queue processing stopped")

    async def close(self):
        """Clean up resources."""
        await self.stop_processing()
        await self.webhook_trigger.close()
