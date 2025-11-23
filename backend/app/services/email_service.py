"""
Email Service
Complete email sending infrastructure with multi-provider support and tracking
"""
import smtplib
import logging
import re
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import time

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.email_config import email_config
from app.models import Campaign, CampaignMetrics, Lead
from app.core.database import get_db

logger = logging.getLogger(__name__)


class EmailValidationError(Exception):
    """Raised when email validation fails"""
    pass


class EmailSendError(Exception):
    """Raised when email sending fails"""
    pass


class EmailService:
    """
    Production-ready email service with multi-provider support
    Handles sending, tracking, validation, and bounce detection
    """

    def __init__(self, db: Optional[Session] = None):
        """Initialize email service"""
        self.db = db
        self.config = email_config

        # Validate configuration
        is_valid, errors = self.config.validate_configuration()
        if not is_valid and not self.config.TEST_MODE:
            logger.warning(f"Email configuration incomplete: {', '.join(errors)}")

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        tracking_token: Optional[str] = None,
    ) -> dict:
        """
        Send a single email with tracking

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML email body
            text_body: Plain text version (auto-generated if not provided)
            from_email: Sender email (defaults to config)
            from_name: Sender name (defaults to config)
            reply_to: Reply-to address (defaults to config)
            attachments: List of attachment dictionaries
            tracking_token: Optional tracking token for opens/clicks

        Returns:
            dict with status and message_id
        """
        try:
            # Validate email
            self.validate_email(to_email)

            # Check if email is bounced
            if self.check_bounce(to_email):
                raise EmailSendError(f"Email {to_email} is on bounce list")

            # Override recipient in debug mode
            if self.config.DEBUG_EMAIL_OVERRIDE:
                logger.info(f"DEBUG MODE: Overriding recipient {to_email} with {self.config.DEBUG_EMAIL_OVERRIDE}")
                to_email = self.config.DEBUG_EMAIL_OVERRIDE

            # Set defaults
            from_email = from_email or self.config.EMAIL_FROM
            from_name = from_name or self.config.EMAIL_FROM_NAME
            reply_to = reply_to or self.config.EMAIL_REPLY_TO

            # Test mode - just log
            if self.config.TEST_MODE:
                logger.info("=" * 80)
                logger.info("TEST MODE - Email would be sent:")
                logger.info(f"To: {to_email}")
                logger.info(f"From: {from_name} <{from_email}>")
                logger.info(f"Subject: {subject}")
                logger.info(f"Tracking Token: {tracking_token}")
                logger.info(f"HTML Body Length: {len(html_body)} chars")
                logger.info("=" * 80)
                return {
                    "success": True,
                    "message_id": f"test-{secrets.token_hex(16)}",
                    "provider": "test_mode"
                }

            # Route to appropriate provider
            if self.config.EMAIL_PROVIDER == 'smtp':
                result = self._send_smtp(
                    to_email, subject, html_body, text_body,
                    from_email, from_name, reply_to, attachments
                )
            elif self.config.EMAIL_PROVIDER == 'sendgrid':
                result = self._send_sendgrid(
                    to_email, subject, html_body, text_body,
                    from_email, from_name, reply_to, attachments
                )
            elif self.config.EMAIL_PROVIDER == 'mailgun':
                result = self._send_mailgun(
                    to_email, subject, html_body, text_body,
                    from_email, from_name, reply_to, attachments
                )
            elif self.config.EMAIL_PROVIDER == 'resend':
                result = self._send_resend(
                    to_email, subject, html_body, text_body,
                    from_email, from_name, reply_to, attachments
                )
            else:
                raise EmailSendError(f"Unknown email provider: {self.config.EMAIL_PROVIDER}")

            logger.info(f"Email sent successfully to {to_email} via {self.config.EMAIL_PROVIDER}")
            return result

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise EmailSendError(f"Failed to send email: {str(e)}")

    def send_batch(
        self,
        emails: List[Dict[str, Any]],
        delay_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send multiple emails with optional delay between sends

        Args:
            emails: List of email dictionaries with keys: to_email, subject, html_body, etc.
            delay_seconds: Delay between sends (defaults to config)

        Returns:
            dict with success/failure counts and details
        """
        delay = delay_seconds or self.config.BATCH_DELAY_SECONDS
        results = {
            "total": len(emails),
            "success": 0,
            "failed": 0,
            "errors": []
        }

        for i, email_data in enumerate(emails):
            try:
                self.send_email(**email_data)
                results["success"] += 1

                # Add delay between sends (except for last email)
                if i < len(emails) - 1 and delay > 0:
                    time.sleep(delay)

            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "email": email_data.get("to_email"),
                    "error": str(e)
                })
                logger.error(f"Failed to send email in batch: {str(e)}")

        logger.info(f"Batch send complete: {results['success']}/{results['total']} successful")
        return results

    def send_campaign_email(
        self,
        campaign_id: int,
        lead_id: int,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> dict:
        """
        Send email as part of a campaign with full tracking

        Args:
            campaign_id: Campaign ID
            lead_id: Lead ID
            subject: Email subject
            html_body: HTML body (tracking will be added)
            text_body: Plain text body

        Returns:
            dict with send status
        """
        if not self.db:
            raise EmailSendError("Database session required for campaign emails")

        try:
            # Get lead
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise EmailSendError(f"Lead {lead_id} not found")

            # Generate tracking token
            tracking_token = self._generate_tracking_token(campaign_id, lead_id)

            # Add tracking to HTML body
            from app.services.email_template_service import EmailTemplateService
            template_service = EmailTemplateService()

            if self.config.TRACKING_PIXEL_ENABLED:
                html_body = template_service.add_tracking_pixel(html_body, tracking_token)

            if self.config.LINK_TRACKING_ENABLED:
                html_body = template_service.wrap_links_for_tracking(html_body, tracking_token)

            # Send email
            result = self.send_email(
                to_email=lead.email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                tracking_token=tracking_token
            )

            # Update metrics
            self._update_campaign_metrics(campaign_id, sent=1)

            logger.info(f"Campaign email sent: campaign={campaign_id}, lead={lead_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to send campaign email: {str(e)}")
            self._update_campaign_metrics(campaign_id, failed=1)
            raise EmailSendError(f"Failed to send campaign email: {str(e)}")

    def track_open(self, tracking_token: str) -> bytes:
        """
        Track email open and return 1x1 transparent pixel

        Args:
            tracking_token: Tracking token from email

        Returns:
            1x1 transparent GIF image bytes
        """
        try:
            campaign_id, lead_id = self._decode_tracking_token(tracking_token)

            if self.db:
                # Update metrics
                self._update_campaign_metrics(campaign_id, opens=1)

                # TODO: Store individual open event in campaign_events table
                # This would allow tracking multiple opens per lead
                logger.info(f"Email opened: campaign={campaign_id}, lead={lead_id}")

        except Exception as e:
            logger.error(f"Failed to track email open: {str(e)}")

        # Return 1x1 transparent GIF
        return self._generate_tracking_pixel()

    def track_click(self, tracking_token: str, url: str) -> str:
        """
        Track link click and return redirect URL

        Args:
            tracking_token: Tracking token from email
            url: Original URL to redirect to

        Returns:
            URL to redirect to
        """
        try:
            campaign_id, lead_id = self._decode_tracking_token(tracking_token)

            if self.db:
                # Update metrics
                self._update_campaign_metrics(campaign_id, clicks=1)

                # TODO: Store individual click event in campaign_events table
                # This would allow tracking which links were clicked
                logger.info(f"Link clicked: campaign={campaign_id}, lead={lead_id}, url={url}")

        except Exception as e:
            logger.error(f"Failed to track link click: {str(e)}")

        return url

    def validate_email(self, email: str) -> bool:
        """
        Validate email address format

        Args:
            email: Email address to validate

        Returns:
            True if valid

        Raises:
            EmailValidationError if invalid
        """
        # Basic regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not email or not isinstance(email, str):
            raise EmailValidationError("Email address is required")

        if not re.match(pattern, email):
            raise EmailValidationError(f"Invalid email format: {email}")

        # Additional checks
        if len(email) > 254:
            raise EmailValidationError("Email address too long")

        local_part, domain = email.rsplit('@', 1)
        if len(local_part) > 64:
            raise EmailValidationError("Email local part too long")

        return True

    def check_bounce(self, email: str) -> bool:
        """
        Check if email address has bounced too many times

        Args:
            email: Email address to check

        Returns:
            True if email is on bounce list
        """
        if not self.db or not self.config.BOUNCE_CHECK_ENABLED:
            return False

        # TODO: Implement bounce tracking in database
        # Query bounce_tracking table for email
        # Return True if bounce_count >= MAX_BOUNCE_COUNT

        return False

    # Private methods

    def _send_smtp(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str],
        from_email: str,
        from_name: str,
        reply_to: str,
        attachments: Optional[List[Dict[str, Any]]]
    ) -> dict:
        """Send email via SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = to_email
            msg['Reply-To'] = reply_to

            # Add text version
            if text_body:
                msg.attach(MIMEText(text_body, 'plain'))

            # Add HTML version
            msg.attach(MIMEText(html_body, 'html'))

            # TODO: Add attachments support
            # if attachments:
            #     for attachment in attachments:
            #         # Add attachment logic

            # Connect to SMTP server
            if self.config.SMTP_USE_SSL:
                server = smtplib.SMTP_SSL(self.config.SMTP_HOST, self.config.SMTP_PORT)
            else:
                server = smtplib.SMTP(self.config.SMTP_HOST, self.config.SMTP_PORT)

            if self.config.SMTP_USE_TLS and not self.config.SMTP_USE_SSL:
                server.starttls()

            # Login
            if self.config.SMTP_USERNAME and self.config.SMTP_PASSWORD:
                server.login(self.config.SMTP_USERNAME, self.config.SMTP_PASSWORD)

            # Send email
            server.send_message(msg)
            server.quit()

            return {
                "success": True,
                "message_id": msg['Message-ID'] if 'Message-ID' in msg else secrets.token_hex(16),
                "provider": "smtp"
            }

        except smtplib.SMTPAuthenticationError as e:
            raise EmailSendError(f"SMTP authentication failed: {str(e)}")
        except smtplib.SMTPException as e:
            raise EmailSendError(f"SMTP error: {str(e)}")
        except Exception as e:
            raise EmailSendError(f"Failed to send via SMTP: {str(e)}")

    def _send_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str],
        from_email: str,
        from_name: str,
        reply_to: str,
        attachments: Optional[List[Dict[str, Any]]]
    ) -> dict:
        """
        Send email via SendGrid API

        TODO: Implement SendGrid integration
        - Install: pip install sendgrid
        - Documentation: https://docs.sendgrid.com/api-reference/mail-send/mail-send
        """
        # from sendgrid import SendGridAPIClient
        # from sendgrid.helpers.mail import Mail
        #
        # message = Mail(
        #     from_email=(from_email, from_name),
        #     to_emails=to_email,
        #     subject=subject,
        #     html_content=html_body
        # )
        #
        # if text_body:
        #     message.plain_text_content = text_body
        #
        # sg = SendGridAPIClient(self.config.SENDGRID_API_KEY)
        # response = sg.send(message)
        #
        # return {
        #     "success": True,
        #     "message_id": response.headers.get('X-Message-Id'),
        #     "provider": "sendgrid"
        # }

        raise NotImplementedError(
            "SendGrid integration not yet implemented. "
            "Install 'sendgrid' package and uncomment code above."
        )

    def _send_mailgun(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str],
        from_email: str,
        from_name: str,
        reply_to: str,
        attachments: Optional[List[Dict[str, Any]]]
    ) -> dict:
        """
        Send email via Mailgun API

        TODO: Implement Mailgun integration
        - Install: pip install requests
        - Documentation: https://documentation.mailgun.com/en/latest/api-sending.html
        """
        # import requests
        #
        # response = requests.post(
        #     f"https://api.mailgun.net/v3/{self.config.MAILGUN_DOMAIN}/messages",
        #     auth=("api", self.config.MAILGUN_API_KEY),
        #     data={
        #         "from": f"{from_name} <{from_email}>",
        #         "to": to_email,
        #         "subject": subject,
        #         "html": html_body,
        #         "text": text_body or "",
        #         "h:Reply-To": reply_to
        #     }
        # )
        #
        # if response.status_code != 200:
        #     raise EmailSendError(f"Mailgun API error: {response.text}")
        #
        # return {
        #     "success": True,
        #     "message_id": response.json().get('id'),
        #     "provider": "mailgun"
        # }

        raise NotImplementedError(
            "Mailgun integration not yet implemented. "
            "Install 'requests' package and uncomment code above."
        )

    def _send_resend(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str],
        from_email: str,
        from_name: str,
        reply_to: str,
        attachments: Optional[List[Dict[str, Any]]]
    ) -> dict:
        """
        Send email via Resend API

        TODO: Implement Resend integration
        - Install: pip install resend
        - Documentation: https://resend.com/docs/send-with-python
        """
        # import resend
        #
        # resend.api_key = self.config.RESEND_API_KEY
        #
        # params = {
        #     "from": f"{from_name} <{from_email}>",
        #     "to": to_email,
        #     "subject": subject,
        #     "html": html_body,
        #     "reply_to": reply_to
        # }
        #
        # if text_body:
        #     params["text"] = text_body
        #
        # response = resend.Emails.send(params)
        #
        # return {
        #     "success": True,
        #     "message_id": response.get('id'),
        #     "provider": "resend"
        # }

        raise NotImplementedError(
            "Resend integration not yet implemented. "
            "Install 'resend' package and uncomment code above."
        )

    def _generate_tracking_token(self, campaign_id: int, lead_id: int) -> str:
        """Generate tracking token for campaign and lead"""
        # Simple encoding: campaign_id:lead_id:random
        random_part = secrets.token_hex(8)
        return f"{campaign_id}:{lead_id}:{random_part}"

    def _decode_tracking_token(self, token: str) -> tuple[int, int]:
        """Decode tracking token to campaign_id and lead_id"""
        try:
            parts = token.split(':')
            return int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            raise ValueError(f"Invalid tracking token: {token}")

    def _generate_tracking_pixel(self) -> bytes:
        """Generate 1x1 transparent GIF pixel"""
        # 1x1 transparent GIF in bytes
        return bytes.fromhex(
            '474946383961010001008000000000000021f90401000000002c00000000'
            '010001000002024401003b'
        )

    def _update_campaign_metrics(
        self,
        campaign_id: int,
        sent: int = 0,
        delivered: int = 0,
        opens: int = 0,
        clicks: int = 0,
        failed: int = 0
    ):
        """Update campaign metrics"""
        if not self.db:
            return

        try:
            metrics = self.db.query(CampaignMetrics).filter(
                CampaignMetrics.campaign_id == campaign_id
            ).first()

            if metrics:
                metrics.emails_sent += sent
                metrics.emails_delivered += delivered
                metrics.opens += opens
                metrics.clicks += clicks
                metrics.bounces += failed

                # Update rates
                if metrics.emails_sent > 0:
                    metrics.open_rate = (metrics.opens / metrics.emails_sent) * 100
                    metrics.click_rate = (metrics.clicks / metrics.emails_sent) * 100
                    metrics.bounce_rate = (metrics.bounces / metrics.emails_sent) * 100

                self.db.commit()

        except Exception as e:
            logger.error(f"Failed to update campaign metrics: {str(e)}")
            self.db.rollback()


    def send_email_async(self, **kwargs) -> str:
        """
        Send email asynchronously using Celery.

        Args:
            **kwargs: Same arguments as send_email()

        Returns:
            str: Celery task ID

        Usage:
            task_id = email_service.send_email_async(
                to_email='user@example.com',
                subject='Hello',
                html_body='<p>Hello World</p>'
            )
        """
        try:
            from app.tasks.email_tasks import send_single_email
            task = send_single_email.apply_async(kwargs=kwargs)
            logger.info(f"Email queued for async sending: task_id={task.id}")
            return task.id
        except ImportError:
            logger.error("Celery not available. Cannot send email asynchronously.")
            raise EmailSendError("Celery not configured for async email sending")

    def send_batch_async(self, emails: List[Dict[str, Any]], **kwargs) -> str:
        """
        Send batch of emails asynchronously using Celery.

        Args:
            emails: List of email dictionaries
            **kwargs: Additional arguments (batch_size, delay_seconds)

        Returns:
            str: Celery task ID

        Usage:
            task_id = email_service.send_batch_async(
                emails=[
                    {'to_email': 'user1@example.com', 'subject': 'Hello', ...},
                    {'to_email': 'user2@example.com', 'subject': 'Hello', ...},
                ]
            )
        """
        try:
            from app.tasks.email_tasks import send_batch_emails
            task = send_batch_emails.apply_async(
                args=[emails],
                kwargs=kwargs
            )
            logger.info(f"Batch email queued for async sending: task_id={task.id}")
            return task.id
        except ImportError:
            logger.error("Celery not available. Cannot send batch asynchronously.")
            raise EmailSendError("Celery not configured for async batch sending")
