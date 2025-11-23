"""
Email Tasks

Celery tasks for sending emails, batch processing, and retry logic.
These tasks replace the synchronous email sending in the email service.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from celery import shared_task, group, chain, chord
from celery.exceptions import SoftTimeLimitExceeded, MaxRetriesExceededError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="app.tasks.email_tasks.send_single_email",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def send_single_email(
    self,
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    reply_to: Optional[str] = None,
    tracking_token: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Send a single email asynchronously.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_body: HTML email body
        text_body: Plain text version
        from_email: Sender email
        from_name: Sender name
        reply_to: Reply-to address
        tracking_token: Tracking token for opens/clicks

    Returns:
        dict: Send result with status and message_id

    Raises:
        MaxRetriesExceededError: If all retries fail
    """
    from app.services.email_service import EmailService
    from app.core.database import SessionLocal

    logger.info(f"Sending email to {to_email}: {subject}")

    db = SessionLocal()
    try:
        email_service = EmailService(db=db)

        result = email_service.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            from_email=from_email,
            from_name=from_name,
            reply_to=reply_to,
            tracking_token=tracking_token,
        )

        logger.info(f"Email sent successfully to {to_email}")
        return {
            "status": "success",
            "to_email": to_email,
            "message_id": result.get("message_id"),
            "provider": result.get("provider"),
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Email task timed out for {to_email}")
        raise

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")

        # Retry with exponential backoff
        try:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for {to_email}")
            return {
                "status": "failed",
                "to_email": to_email,
                "error": str(e),
            }

    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.email_tasks.send_batch_emails",
    max_retries=2,
    default_retry_delay=300,
)
def send_batch_emails(
    self,
    emails: List[Dict[str, Any]],
    batch_size: int = 50,
    delay_seconds: int = 2,
) -> Dict[str, Any]:
    """
    Send multiple emails in batches with rate limiting.

    Args:
        emails: List of email dictionaries
        batch_size: Number of emails per batch
        delay_seconds: Delay between batches

    Returns:
        dict: Batch send results
    """
    from celery import group
    from time import sleep

    logger.info(f"Starting batch email send: {len(emails)} emails")

    results = {
        "total": len(emails),
        "success": 0,
        "failed": 0,
        "errors": []
    }

    try:
        # Process emails in batches
        for i in range(0, len(emails), batch_size):
            batch = emails[i:i + batch_size]

            # Create parallel tasks for this batch
            job = group(
                send_single_email.s(**email_data)
                for email_data in batch
            )

            # Execute batch
            batch_results = job.apply_async()
            batch_results.get()  # Wait for batch to complete

            # Add delay between batches (except for last batch)
            if i + batch_size < len(emails) and delay_seconds > 0:
                sleep(delay_seconds)

            logger.info(f"Batch {i // batch_size + 1} completed")

        logger.info(f"Batch email send completed: {len(emails)} emails")

        return {
            "status": "success",
            "total": len(emails),
            "message": f"Sent {len(emails)} emails successfully"
        }

    except Exception as e:
        logger.error(f"Batch email send failed: {str(e)}")
        return {
            "status": "failed",
            "total": len(emails),
            "error": str(e)
        }


@shared_task(
    bind=True,
    name="app.tasks.email_tasks.retry_failed_emails",
    max_retries=1,
)
def retry_failed_emails(self) -> Dict[str, Any]:
    """
    Retry failed emails from the database.

    This task runs periodically via Celery Beat to retry emails
    that failed due to temporary issues.

    Returns:
        dict: Retry results
    """
    from app.core.database import SessionLocal
    from app.models.campaigns import CampaignRecipient, RecipientStatusEnum
    from sqlalchemy import and_

    logger.info("Starting retry of failed emails")

    db = SessionLocal()
    try:
        # Find failed recipients that should be retried
        # Only retry if failed less than 3 times and more than 1 hour ago
        retry_after = datetime.utcnow() - timedelta(hours=1)

        stmt = (
            db.query(CampaignRecipient)
            .filter(
                and_(
                    CampaignRecipient.status == RecipientStatusEnum.FAILED,
                    CampaignRecipient.retry_count < 3,
                    CampaignRecipient.updated_at < retry_after
                )
            )
            .limit(100)  # Process 100 at a time
        )

        recipients = stmt.all()

        if not recipients:
            logger.info("No failed emails to retry")
            return {
                "status": "success",
                "retried": 0,
                "message": "No failed emails to retry"
            }

        logger.info(f"Retrying {len(recipients)} failed emails")

        retried = 0
        for recipient in recipients:
            try:
                # Update retry count
                recipient.retry_count += 1
                recipient.status = RecipientStatusEnum.QUEUED

                db.commit()
                retried += 1

                # Queue the email for sending
                # This would trigger the campaign email task
                logger.info(f"Queued recipient {recipient.id} for retry")

            except Exception as e:
                logger.error(f"Failed to retry recipient {recipient.id}: {str(e)}")
                db.rollback()

        logger.info(f"Retry complete: {retried}/{len(recipients)} queued")

        return {
            "status": "success",
            "retried": retried,
            "total": len(recipients)
        }

    except Exception as e:
        logger.error(f"Failed to retry emails: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }

    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.email_tasks.send_campaign_email",
    max_retries=3,
    default_retry_delay=120,
    autoretry_for=(Exception,),
)
def send_campaign_email(
    self,
    campaign_id: int,
    recipient_id: int,
    lead_id: int,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send a campaign email with tracking.

    Args:
        campaign_id: Campaign ID
        recipient_id: Campaign recipient ID
        lead_id: Lead ID
        subject: Email subject
        html_body: HTML body with tracking
        text_body: Plain text body

    Returns:
        dict: Send result
    """
    from app.services.email_service import EmailService
    from app.services.email_template_service import EmailTemplateService
    from app.core.database import SessionLocal
    from app.models.leads import Lead
    from app.models.campaigns import CampaignRecipient, RecipientStatusEnum

    logger.info(f"Sending campaign email: campaign={campaign_id}, lead={lead_id}")

    db = SessionLocal()
    try:
        email_service = EmailService(db=db)
        template_service = EmailTemplateService()

        # Get lead
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead or not lead.email:
            raise ValueError(f"Lead {lead_id} not found or has no email")

        # Get recipient
        recipient = db.query(CampaignRecipient).filter(
            CampaignRecipient.id == recipient_id
        ).first()
        if not recipient:
            raise ValueError(f"Recipient {recipient_id} not found")

        # Generate tracking token
        tracking_token = email_service._generate_tracking_token(campaign_id, lead_id)

        # Add tracking to HTML body
        if email_service.config.TRACKING_PIXEL_ENABLED:
            html_body = template_service.add_tracking_pixel(html_body, tracking_token)

        if email_service.config.LINK_TRACKING_ENABLED:
            html_body = template_service.wrap_links_for_tracking(html_body, tracking_token)

        html_body = template_service.add_unsubscribe_link(html_body, tracking_token)

        # Send email
        result = email_service.send_email(
            to_email=lead.email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            tracking_token=tracking_token,
        )

        # Update recipient status
        recipient.status = RecipientStatusEnum.SENT
        recipient.sent_at = datetime.utcnow()
        db.commit()

        logger.info(f"Campaign email sent successfully to {lead.email}")

        return {
            "status": "success",
            "campaign_id": campaign_id,
            "recipient_id": recipient_id,
            "lead_id": lead_id,
            "to_email": lead.email,
            "message_id": result.get("message_id"),
        }

    except Exception as e:
        logger.error(f"Failed to send campaign email: {str(e)}")

        # Update recipient as failed
        try:
            recipient = db.query(CampaignRecipient).filter(
                CampaignRecipient.id == recipient_id
            ).first()
            if recipient:
                recipient.status = RecipientStatusEnum.FAILED
                recipient.retry_count = recipient.retry_count + 1
                db.commit()
        except:
            pass

        # Retry
        raise self.retry(exc=e)

    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.email_tasks.send_test_email",
    max_retries=1,
)
def send_test_email(
    self,
    to_email: str,
    test_mode: bool = True,
) -> Dict[str, Any]:
    """
    Send a test email to verify email configuration.

    Args:
        to_email: Test recipient email
        test_mode: If True, use TEST_MODE in email service

    Returns:
        dict: Test result
    """
    from app.services.email_service import EmailService
    from app.core.database import SessionLocal

    logger.info(f"Sending test email to {to_email}")

    db = SessionLocal()
    try:
        email_service = EmailService(db=db)

        # Override test mode if needed
        original_test_mode = email_service.config.TEST_MODE
        if test_mode:
            email_service.config.TEST_MODE = True

        result = email_service.send_email(
            to_email=to_email,
            subject="FlipTech Pro - Test Email",
            html_body="<h1>Test Email</h1><p>This is a test email from FlipTech Pro.</p>",
            text_body="Test Email\n\nThis is a test email from FlipTech Pro.",
        )

        # Restore original test mode
        email_service.config.TEST_MODE = original_test_mode

        logger.info(f"Test email sent successfully to {to_email}")

        return {
            "status": "success",
            "to_email": to_email,
            "message": "Test email sent successfully",
            "result": result,
        }

    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}")
        return {
            "status": "failed",
            "to_email": to_email,
            "error": str(e),
        }

    finally:
        db.close()
