"""
Webhook Handler Service

Handles incoming webhooks from N8N with queueing, validation,
and async processing.
"""

import logging
import hashlib
import hmac
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.n8n_workflows import (
    WebhookQueue,
    QueueStatus,
    N8NWorkflow
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class WebhookHandler:
    """
    Webhook Handler

    Processes incoming webhooks with validation, queueing,
    and retry logic.
    """

    def __init__(self, db: Session):
        """Initialize webhook handler"""
        self.db = db

    def validate_signature(
        self,
        payload: Dict[str, Any],
        signature: str,
        secret: Optional[str] = None
    ) -> bool:
        """
        Validate webhook signature

        Args:
            payload: Webhook payload
            signature: Signature from header
            secret: Webhook secret (defaults to settings)

        Returns:
            True if signature is valid
        """
        if not secret:
            secret = getattr(settings, 'N8N_WEBHOOK_SECRET', None)

        if not secret:
            logger.warning("Webhook secret not configured, skipping validation")
            return True

        try:
            import json
            payload_str = json.dumps(payload, sort_keys=True)
            expected_signature = hmac.new(
                secret.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(expected_signature, signature)

        except Exception as e:
            logger.error(f"Signature validation error: {str(e)}")
            return False

    def queue_webhook(
        self,
        workflow_id: Optional[int],
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        source: str = "n8n",
        priority: int = 0,
        webhook_url: Optional[str] = None
    ) -> WebhookQueue:
        """
        Queue webhook for async processing

        Args:
            workflow_id: Associated workflow ID
            payload: Webhook payload
            headers: Request headers
            source: Webhook source
            priority: Processing priority (higher = more important)
            webhook_url: Original webhook URL

        Returns:
            WebhookQueue entry
        """
        try:
            webhook_entry = WebhookQueue(
                workflow_id=workflow_id,
                webhook_payload=payload,
                webhook_headers=headers or {},
                source=source,
                webhook_url=webhook_url,
                status=QueueStatus.QUEUED,
                priority=priority
            )

            self.db.add(webhook_entry)
            self.db.commit()
            self.db.refresh(webhook_entry)

            logger.info(f"Queued webhook {webhook_entry.id} for processing")
            return webhook_entry

        except Exception as e:
            logger.error(f"Failed to queue webhook: {str(e)}")
            self.db.rollback()
            raise

    def get_pending_webhooks(self, limit: int = 10) -> list[WebhookQueue]:
        """
        Get pending webhooks for processing

        Args:
            limit: Maximum number to retrieve

        Returns:
            List of pending webhooks
        """
        try:
            webhooks = (
                self.db.query(WebhookQueue)
                .filter(WebhookQueue.status == QueueStatus.QUEUED)
                .order_by(WebhookQueue.priority.desc(), WebhookQueue.created_at.asc())
                .limit(limit)
                .all()
            )
            return webhooks

        except Exception as e:
            logger.error(f"Failed to get pending webhooks: {str(e)}")
            return []

    def mark_processing(self, webhook_id: int) -> bool:
        """Mark webhook as processing"""
        try:
            webhook = self.db.query(WebhookQueue).filter(
                WebhookQueue.id == webhook_id
            ).first()

            if webhook:
                webhook.status = QueueStatus.PROCESSING
                self.db.commit()
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to mark webhook as processing: {str(e)}")
            self.db.rollback()
            return False

    def mark_completed(
        self,
        webhook_id: int,
        processing_duration: Optional[float] = None
    ) -> bool:
        """Mark webhook as completed"""
        try:
            webhook = self.db.query(WebhookQueue).filter(
                WebhookQueue.id == webhook_id
            ).first()

            if webhook:
                webhook.status = QueueStatus.COMPLETED
                webhook.processed_at = datetime.utcnow()
                webhook.processing_duration_seconds = processing_duration
                self.db.commit()
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to mark webhook as completed: {str(e)}")
            self.db.rollback()
            return False

    def mark_failed(
        self,
        webhook_id: int,
        error_message: str,
        error_trace: Optional[str] = None
    ) -> bool:
        """Mark webhook as failed and schedule retry if applicable"""
        try:
            webhook = self.db.query(WebhookQueue).filter(
                WebhookQueue.id == webhook_id
            ).first()

            if webhook:
                webhook.status = QueueStatus.FAILED
                webhook.error_message = error_message
                webhook.error_trace = error_trace
                webhook.last_error_at = datetime.utcnow()
                webhook.retry_count += 1

                # Schedule retry if not exceeded max retries
                if webhook.retry_count < webhook.max_retries:
                    webhook.next_retry_at = webhook.calculate_next_retry()
                    webhook.status = QueueStatus.QUEUED
                    logger.info(
                        f"Webhook {webhook_id} will retry at {webhook.next_retry_at}"
                    )

                self.db.commit()
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to mark webhook as failed: {str(e)}")
            self.db.rollback()
            return False

    def get_retryable_webhooks(self, limit: int = 10) -> list[WebhookQueue]:
        """Get webhooks that should be retried"""
        try:
            now = datetime.utcnow()
            webhooks = (
                self.db.query(WebhookQueue)
                .filter(
                    WebhookQueue.status == QueueStatus.QUEUED,
                    WebhookQueue.retry_count > 0,
                    WebhookQueue.next_retry_at <= now
                )
                .order_by(WebhookQueue.priority.desc(), WebhookQueue.next_retry_at.asc())
                .limit(limit)
                .all()
            )
            return webhooks

        except Exception as e:
            logger.error(f"Failed to get retryable webhooks: {str(e)}")
            return []

    def find_workflow_by_webhook(self, webhook_path: str) -> Optional[N8NWorkflow]:
        """
        Find workflow by webhook URL path

        Args:
            webhook_path: Webhook path or ID

        Returns:
            N8NWorkflow if found
        """
        try:
            # Try by workflow ID first
            workflow = self.db.query(N8NWorkflow).filter(
                N8NWorkflow.n8n_workflow_id == webhook_path
            ).first()

            if workflow:
                return workflow

            # Try by webhook URL containing the path
            workflow = self.db.query(N8NWorkflow).filter(
                N8NWorkflow.webhook_url.contains(webhook_path)
            ).first()

            return workflow

        except Exception as e:
            logger.error(f"Failed to find workflow by webhook: {str(e)}")
            return None
