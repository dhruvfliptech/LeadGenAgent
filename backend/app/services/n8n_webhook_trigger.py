"""
N8n webhook trigger service.

This service handles triggering n8n workflows via webhooks from backend events.
It provides methods for different event types and handles webhook delivery,
retries, and error handling.
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import time

from app.core.webhook_config import webhook_config, get_webhook_url
from app.core.url_validator import URLValidator, URLSecurityError
from app.utils.webhook_security import WebhookSecurity

logger = logging.getLogger(__name__)


class N8nWebhookTriggerError(Exception):
    """Base exception for webhook trigger errors."""
    pass


class N8nWebhookTimeoutError(N8nWebhookTriggerError):
    """Webhook request timeout error."""
    pass


class N8nWebhookTrigger:
    """
    Trigger n8n workflows via webhooks from backend events.

    This service provides methods to trigger various n8n workflows
    in response to backend events like lead scraping, demo deployment,
    video generation, etc.
    """

    def __init__(self):
        """Initialize webhook trigger service."""
        self.config = webhook_config
        self.security = WebhookSecurity()
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP client session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.retry.timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close HTTP client session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def trigger_lead_scraped(
        self,
        lead_id: int,
        lead_data: Dict[str, Any]
    ) -> bool:
        """
        Trigger when new lead is scraped.

        Args:
            lead_id: Lead database ID
            lead_data: Lead information

        Returns:
            True if webhook was sent successfully

        Example:
            >>> trigger = N8nWebhookTrigger()
            >>> await trigger.trigger_lead_scraped(123, {
            ...     "business_name": "Acme Inc",
            ...     "category": "web design",
            ...     "score": 0.85
            ... })
        """
        if not self.config.is_enabled():
            logger.debug("n8n integration is disabled, skipping webhook")
            return False

        webhook_url = get_webhook_url('lead_scraped')
        payload = {
            "event": "lead_scraped",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "lead_id": lead_id,
                **lead_data
            }
        }

        return await self.send_webhook(
            webhook_url=webhook_url,
            data=payload,
            entity_type="lead",
            entity_id=lead_id
        )

    async def trigger_lead_qualified(
        self,
        lead_id: int,
        qualification_data: Dict[str, Any]
    ) -> bool:
        """
        Trigger when lead passes qualification.

        Args:
            lead_id: Lead database ID
            qualification_data: Qualification results

        Returns:
            True if webhook was sent successfully
        """
        if not self.config.is_enabled():
            return False

        webhook_url = get_webhook_url('lead_qualified')
        payload = {
            "event": "lead_qualified",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "lead_id": lead_id,
                **qualification_data
            }
        }

        return await self.send_webhook(
            webhook_url=webhook_url,
            data=payload,
            entity_type="lead",
            entity_id=lead_id
        )

    async def trigger_demo_completed(
        self,
        demo_site_id: int,
        demo_data: Dict[str, Any]
    ) -> bool:
        """
        Trigger when demo site deployment completes.

        Args:
            demo_site_id: Demo site database ID
            demo_data: Demo site information

        Returns:
            True if webhook was sent successfully

        Example:
            >>> await trigger.trigger_demo_completed(456, {
            ...     "url": "https://demo-site-123.vercel.app",
            ...     "lead_id": 123,
            ...     "status": "ready"
            ... })
        """
        if not self.config.is_enabled():
            return False

        webhook_url = get_webhook_url('demo_completed')
        payload = {
            "event": "demo_completed",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "demo_site_id": demo_site_id,
                **demo_data
            }
        }

        return await self.send_webhook(
            webhook_url=webhook_url,
            data=payload,
            entity_type="demo_site",
            entity_id=demo_site_id,
            priority=1  # Higher priority for completed demos
        )

    async def trigger_demo_failed(
        self,
        demo_site_id: int,
        error_data: Dict[str, Any]
    ) -> bool:
        """
        Trigger when demo site deployment fails.

        Args:
            demo_site_id: Demo site database ID
            error_data: Error information

        Returns:
            True if webhook was sent successfully
        """
        if not self.config.is_enabled():
            return False

        webhook_url = get_webhook_url('demo_failed')
        payload = {
            "event": "demo_failed",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "demo_site_id": demo_site_id,
                **error_data
            }
        }

        return await self.send_webhook(
            webhook_url=webhook_url,
            data=payload,
            entity_type="demo_site",
            entity_id=demo_site_id,
            priority=2  # High priority for failures
        )

    async def trigger_video_completed(
        self,
        video_id: int,
        video_data: Dict[str, Any]
    ) -> bool:
        """
        Trigger when video generation completes.

        Args:
            video_id: Video database ID
            video_data: Video information

        Returns:
            True if webhook was sent successfully

        Example:
            >>> await trigger.trigger_video_completed(789, {
            ...     "url": "https://storage.example.com/video-123.mp4",
            ...     "duration": 45.5,
            ...     "lead_id": 123
            ... })
        """
        if not self.config.is_enabled():
            return False

        webhook_url = get_webhook_url('video_completed')
        payload = {
            "event": "video_completed",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "video_id": video_id,
                **video_data
            }
        }

        return await self.send_webhook(
            webhook_url=webhook_url,
            data=payload,
            entity_type="video",
            entity_id=video_id,
            priority=1
        )

    async def trigger_video_failed(
        self,
        video_id: int,
        error_data: Dict[str, Any]
    ) -> bool:
        """
        Trigger when video generation fails.

        Args:
            video_id: Video database ID
            error_data: Error information

        Returns:
            True if webhook was sent successfully
        """
        if not self.config.is_enabled():
            return False

        webhook_url = get_webhook_url('video_failed')
        payload = {
            "event": "video_failed",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "video_id": video_id,
                **error_data
            }
        }

        return await self.send_webhook(
            webhook_url=webhook_url,
            data=payload,
            entity_type="video",
            entity_id=video_id,
            priority=2
        )

    async def trigger_email_sent(
        self,
        lead_id: int,
        email_data: Dict[str, Any]
    ) -> bool:
        """
        Trigger when email is sent to lead.

        Args:
            lead_id: Lead database ID
            email_data: Email information

        Returns:
            True if webhook was sent successfully

        Example:
            >>> await trigger.trigger_email_sent(123, {
            ...     "subject": "Check out your custom demo",
            ...     "to": "contact@example.com",
            ...     "sent_at": "2025-11-04T12:00:00Z"
            ... })
        """
        if not self.config.is_enabled():
            return False

        webhook_url = get_webhook_url('email_sent')
        payload = {
            "event": "email_sent",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "lead_id": lead_id,
                **email_data
            }
        }

        return await self.send_webhook(
            webhook_url=webhook_url,
            data=payload,
            entity_type="lead",
            entity_id=lead_id
        )

    async def trigger_email_failed(
        self,
        lead_id: int,
        error_data: Dict[str, Any]
    ) -> bool:
        """
        Trigger when email sending fails.

        Args:
            lead_id: Lead database ID
            error_data: Error information

        Returns:
            True if webhook was sent successfully
        """
        if not self.config.is_enabled():
            return False

        webhook_url = get_webhook_url('email_failed')
        payload = {
            "event": "email_failed",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "lead_id": lead_id,
                **error_data
            }
        }

        return await self.send_webhook(
            webhook_url=webhook_url,
            data=payload,
            entity_type="lead",
            entity_id=lead_id,
            priority=2
        )

    async def trigger_lead_responded(
        self,
        lead_id: int,
        response_data: Dict[str, Any]
    ) -> bool:
        """
        Trigger when lead responds to outreach.

        Args:
            lead_id: Lead database ID
            response_data: Response information

        Returns:
            True if webhook was sent successfully

        Example:
            >>> await trigger.trigger_lead_responded(123, {
            ...     "response_type": "email",
            ...     "message": "I'm interested in learning more",
            ...     "sentiment": "positive"
            ... })
        """
        if not self.config.is_enabled():
            return False

        webhook_url = get_webhook_url('lead_responded')
        payload = {
            "event": "lead_responded",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "lead_id": lead_id,
                **response_data
            }
        }

        return await self.send_webhook(
            webhook_url=webhook_url,
            data=payload,
            entity_type="lead",
            entity_id=lead_id,
            priority=2  # High priority for responses
        )

    async def trigger_approval_requested(
        self,
        approval_type: str,
        entity_id: int,
        approval_data: Dict[str, Any]
    ) -> bool:
        """
        Trigger when approval is requested.

        Args:
            approval_type: Type of approval (demo, video, email)
            entity_id: Entity database ID
            approval_data: Approval request information

        Returns:
            True if webhook was sent successfully
        """
        if not self.config.is_enabled():
            return False

        webhook_url = get_webhook_url('approval_requested')
        payload = {
            "event": "approval_requested",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "approval_type": approval_type,
                "entity_id": entity_id,
                **approval_data
            }
        }

        return await self.send_webhook(
            webhook_url=webhook_url,
            data=payload,
            entity_type=approval_type,
            entity_id=entity_id,
            priority=2  # High priority for approvals
        )

    async def trigger_workflow_error(
        self,
        workflow_name: str,
        error_data: Dict[str, Any]
    ) -> bool:
        """
        Trigger when a workflow encounters an error.

        Args:
            workflow_name: Name of the workflow
            error_data: Error information

        Returns:
            True if webhook was sent successfully
        """
        if not self.config.is_enabled():
            return False

        webhook_url = get_webhook_url('workflow_error')
        payload = {
            "event": "workflow_error",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "workflow_name": workflow_name,
                **error_data
            }
        }

        return await self.send_webhook(
            webhook_url=webhook_url,
            data=payload,
            priority=3  # Critical priority for errors
        )

    async def send_webhook(
        self,
        webhook_url: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        priority: int = 0
    ) -> bool:
        """
        Send webhook with retry logic.

        SECURITY: Validates webhook URL to prevent SSRF attacks
        OWASP: https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html

        Args:
            webhook_url: URL to send webhook to
            data: Webhook payload
            headers: Additional headers
            retry_count: Maximum retries (defaults to config)
            entity_type: Entity type for tracking
            entity_id: Entity ID for tracking
            priority: Priority level (0=normal, 1=high, 2=urgent, 3=critical)

        Returns:
            True if webhook was sent successfully

        Raises:
            N8nWebhookTriggerError: If webhook delivery fails after retries
        """
        # Validate webhook URL to prevent SSRF
        from app.core.security_config import get_webhook_allowed_domains
        validator = URLValidator(
            allowed_domains=get_webhook_allowed_domains(),
            allow_private_ips=False,
            strict_mode=True
        )
        try:
            validated_url = validator.validate_webhook_url(webhook_url)
        except URLSecurityError as e:
            logger.error(f"Blocked unsafe webhook URL: {webhook_url} - {e}")
            raise N8nWebhookTriggerError(f"Invalid webhook URL: {str(e)}")

        if retry_count is None:
            retry_count = self.config.retry.max_retries

        # Prepare headers
        request_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Craigslist-Lead-Gen-Webhook/1.0'
        }

        if headers:
            request_headers.update(headers)

        # Add signature if security is enabled
        if self.config.security.require_signature and self.config.security.webhook_secret:
            signed_payload = self.security.create_signed_payload(
                data,
                self.config.security.webhook_secret
            )
            request_headers.update(signed_payload['headers'])

        # Get session
        session = await self.get_session()

        # Attempt delivery with retries
        last_error = None
        for attempt in range(retry_count + 1):
            try:
                start_time = time.time()

                # Send request using validated URL
                async with session.post(
                    validated_url,  # Use the validated URL
                    json=data,
                    headers=request_headers
                ) as response:
                    duration_ms = int((time.time() - start_time) * 1000)

                    # Read response
                    response_text = await response.text()

                    # Check status
                    if response.status >= 200 and response.status < 300:
                        logger.info(
                            f"Webhook sent successfully: url={webhook_url}, "
                            f"event={data.get('event')}, status={response.status}, "
                            f"duration_ms={duration_ms}"
                        )
                        return True
                    else:
                        error_msg = f"Webhook failed with status {response.status}: {response_text}"
                        logger.warning(error_msg)
                        last_error = error_msg

            except asyncio.TimeoutError:
                error_msg = f"Webhook request timeout after {self.config.retry.timeout_seconds}s"
                logger.warning(f"{error_msg}: url={webhook_url}, attempt={attempt + 1}")
                last_error = error_msg

            except aiohttp.ClientError as e:
                error_msg = f"Webhook request failed: {str(e)}"
                logger.warning(f"{error_msg}: url={webhook_url}, attempt={attempt + 1}")
                last_error = error_msg

            except Exception as e:
                error_msg = f"Unexpected error sending webhook: {str(e)}"
                logger.error(f"{error_msg}: url={webhook_url}, attempt={attempt + 1}")
                last_error = error_msg

            # Wait before retry (if not last attempt)
            if attempt < retry_count:
                retry_delay = self.config.retry.retry_delays[
                    min(attempt, len(self.config.retry.retry_delays) - 1)
                ]
                logger.info(f"Retrying webhook in {retry_delay}s (attempt {attempt + 2}/{retry_count + 1})")
                await asyncio.sleep(retry_delay)

        # All retries failed
        logger.error(
            f"Webhook delivery failed after {retry_count + 1} attempts: "
            f"url={webhook_url}, last_error={last_error}"
        )
        return False

    async def batch_send_webhooks(
        self,
        webhooks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send multiple webhooks concurrently.

        Args:
            webhooks: List of webhook configurations

        Returns:
            Dictionary with results

        Example:
            >>> webhooks = [
            ...     {"url": "...", "data": {...}},
            ...     {"url": "...", "data": {...}}
            ... ]
            >>> results = await trigger.batch_send_webhooks(webhooks)
        """
        tasks = []
        for webhook in webhooks:
            task = self.send_webhook(
                webhook_url=webhook['url'],
                data=webhook['data'],
                headers=webhook.get('headers'),
                entity_type=webhook.get('entity_type'),
                entity_id=webhook.get('entity_id'),
                priority=webhook.get('priority', 0)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r is True)
        failure_count = len(results) - success_count

        return {
            'total': len(webhooks),
            'success': success_count,
            'failed': failure_count,
            'results': results
        }


# Singleton instance
_webhook_trigger: Optional[N8nWebhookTrigger] = None


def get_webhook_trigger() -> N8nWebhookTrigger:
    """
    Get singleton webhook trigger instance.

    Returns:
        N8nWebhookTrigger instance

    Example:
        >>> from app.services.n8n_webhook_trigger import get_webhook_trigger
        >>> trigger = get_webhook_trigger()
        >>> await trigger.trigger_lead_scraped(123, {...})
    """
    global _webhook_trigger
    if _webhook_trigger is None:
        _webhook_trigger = N8nWebhookTrigger()
    return _webhook_trigger


async def cleanup_webhook_trigger():
    """Clean up webhook trigger resources."""
    global _webhook_trigger
    if _webhook_trigger is not None:
        await _webhook_trigger.close()
        _webhook_trigger = None
