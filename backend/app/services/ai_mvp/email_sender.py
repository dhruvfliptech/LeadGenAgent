"""
Email Sender - Send emails via Postmark API.

Uses Postmark for professional email deliverability:
- 99.99% uptime
- Industry-best inbox placement
- Detailed delivery tracking
- Bounce/spam handling

Based on research from Claudes_Updates/05_MVP_QUICK_START_GUIDE.md
"""

from typing import Optional, Dict, Any
from datetime import datetime
import structlog
from postmarker.core import PostmarkClient
from postmarker.exceptions import PostmarkerException

logger = structlog.get_logger(__name__)


class EmailSenderConfig:
    """Configuration for Email Sender."""

    def __init__(
        self,
        postmark_server_token: str,
        from_email: str,
        from_name: Optional[str] = None
    ):
        self.postmark_server_token = postmark_server_token
        self.from_email = from_email
        self.from_name = from_name or "Sales Team"


class EmailSender:
    """
    Send transactional emails via Postmark.

    Features:
    - Professional email delivery
    - Open/click tracking
    - Bounce/spam handling
    - Template support (future)
    """

    def __init__(self, config: EmailSenderConfig):
        """Initialize email sender."""
        self.config = config
        self.client = PostmarkClient(server_token=config.postmark_server_token)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        track_opens: bool = True,
        track_links: bool = True,
        tag: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send email via Postmark.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML email body
            text_body: Plain text version (auto-generated if None)
            track_opens: Enable open tracking
            track_links: Enable link click tracking
            tag: Email tag for categorization
            metadata: Custom metadata (key-value pairs)

        Returns:
            Send response with message_id, status, etc.

        Raises:
            PostmarkerException: If send fails
        """
        from_address = f"{self.config.from_name} <{self.config.from_email}>"

        logger.info(
            "email.sending",
            to=to_email,
            subject=subject,
            tag=tag
        )

        try:
            response = self.client.emails.send(
                From=from_address,
                To=to_email,
                Subject=subject,
                HtmlBody=html_body,
                TextBody=text_body,
                TrackOpens=track_opens,
                TrackLinks="HtmlOnly" if track_links else "None",
                MessageStream="outbound",  # Use outbound stream for cold emails
                Tag=tag,
                Metadata=metadata or {}
            )

            logger.info(
                "email.sent",
                to=to_email,
                message_id=response["MessageID"],
                submitted_at=response["SubmittedAt"]
            )

            return {
                "success": True,
                "message_id": response["MessageID"],
                "status": "sent",
                "submitted_at": response["SubmittedAt"],
                "to": response["To"],
                "error_code": response.get("ErrorCode", 0)
            }

        except PostmarkerException as e:
            logger.error(
                "email.failed",
                to=to_email,
                error=str(e),
                error_code=getattr(e, "error_code", None)
            )

            return {
                "success": False,
                "message_id": None,
                "status": "failed",
                "error": str(e),
                "error_code": getattr(e, "error_code", None),
                "submitted_at": None
            }

    async def send_bulk_emails(
        self,
        emails: list[Dict[str, Any]],
        batch_size: int = 500
    ) -> Dict[str, Any]:
        """
        Send multiple emails in batch.

        Args:
            emails: List of email dicts with keys: to_email, subject, html_body, etc.
            batch_size: Max emails per batch (Postmark limit: 500)

        Returns:
            Summary with success/failure counts
        """
        total = len(emails)
        success_count = 0
        failed_count = 0
        results = []

        logger.info("email.bulk_sending", total=total)

        # Process in batches
        for i in range(0, total, batch_size):
            batch = emails[i:i + batch_size]

            # Prepare batch messages
            messages = []
            for email in batch:
                from_address = f"{self.config.from_name} <{self.config.from_email}>"
                messages.append({
                    "From": from_address,
                    "To": email["to_email"],
                    "Subject": email["subject"],
                    "HtmlBody": email["html_body"],
                    "TextBody": email.get("text_body"),
                    "TrackOpens": email.get("track_opens", True),
                    "TrackLinks": "HtmlOnly" if email.get("track_links", True) else "None",
                    "MessageStream": "outbound",
                    "Tag": email.get("tag"),
                    "Metadata": email.get("metadata", {})
                })

            try:
                # Send batch
                batch_response = self.client.emails.send_batch(*messages)

                # Process responses
                for response in batch_response:
                    if response.get("ErrorCode") == 0:
                        success_count += 1
                    else:
                        failed_count += 1

                    results.append({
                        "to": response.get("To"),
                        "message_id": response.get("MessageID"),
                        "error_code": response.get("ErrorCode"),
                        "message": response.get("Message")
                    })

            except PostmarkerException as e:
                logger.error(
                    "email.bulk_batch_failed",
                    batch_num=i // batch_size,
                    error=str(e)
                )
                failed_count += len(batch)

        logger.info(
            "email.bulk_complete",
            total=total,
            success=success_count,
            failed=failed_count
        )

        return {
            "total": total,
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": (success_count / total * 100) if total > 0 else 0,
            "results": results
        }

    def get_delivery_stats(self, message_id: str) -> Dict[str, Any]:
        """
        Get delivery statistics for a sent email.

        Args:
            message_id: Postmark message ID

        Returns:
            Stats with opens, clicks, bounces, etc.
        """
        try:
            # Get message details
            message = self.client.messages.get(message_id)

            return {
                "message_id": message_id,
                "status": message.get("Status"),
                "to": message.get("To"),
                "subject": message.get("Subject"),
                "sent_at": message.get("ReceivedAt"),
                "opens": message.get("OpenCount", 0),
                "clicks": message.get("ClickCount", 0),
                "bounced": message.get("Bounced", False),
                "spam_complaint": message.get("SpamComplaint", False)
            }

        except PostmarkerException as e:
            logger.error(
                "email.stats_failed",
                message_id=message_id,
                error=str(e)
            )
            return {
                "message_id": message_id,
                "error": str(e)
            }

    def check_server_health(self) -> Dict[str, Any]:
        """
        Check Postmark server status.

        Returns:
            Server info with stats
        """
        try:
            server = self.client.server.get()

            return {
                "healthy": True,
                "server_id": server.get("ID"),
                "name": server.get("Name"),
                "color": server.get("Color"),
                "smtp_api_activated": server.get("SmtpApiActivated"),
                "delivery_type": server.get("DeliveryType")
            }

        except PostmarkerException as e:
            logger.error("email.health_check_failed", error=str(e))
            return {
                "healthy": False,
                "error": str(e)
            }
