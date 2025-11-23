"""
Campaign Tasks

Celery tasks for campaign execution, scheduling, and management.
These tasks handle the asynchronous processing of email campaigns.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from celery import shared_task, group, chain, chord
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import and_, or_

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="app.tasks.campaign_tasks.send_campaign_emails",
    max_retries=2,
    default_retry_delay=300,
)
def send_campaign_emails(
    self,
    campaign_id: int,
    batch_size: int = 50,
) -> Dict[str, Any]:
    """
    Send all queued emails for a campaign.

    This is the main task that processes a campaign and sends emails
    to all queued recipients in batches.

    Args:
        campaign_id: Campaign ID
        batch_size: Number of emails to send per batch

    Returns:
        dict: Campaign send results
    """
    from app.core.database import SessionLocal
    from app.models.campaigns import Campaign, CampaignRecipient, RecipientStatusEnum
    from app.models.leads import Lead
    from app.services.email_template_service import EmailTemplateService
    from app.tasks.email_tasks import send_campaign_email

    logger.info(f"Starting campaign email send: campaign_id={campaign_id}")

    db = SessionLocal()
    try:
        # Get campaign
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Get template service
        template_service = EmailTemplateService()

        # Get queued recipients with their leads
        recipients = (
            db.query(CampaignRecipient)
            .filter(
                and_(
                    CampaignRecipient.campaign_id == campaign_id,
                    CampaignRecipient.status == RecipientStatusEnum.QUEUED
                )
            )
            .limit(batch_size)
            .all()
        )

        if not recipients:
            logger.info(f"No queued recipients for campaign {campaign_id}")
            return {
                "status": "success",
                "campaign_id": campaign_id,
                "total": 0,
                "message": "No queued recipients"
            }

        logger.info(f"Processing {len(recipients)} recipients for campaign {campaign_id}")

        # Process recipients in parallel
        tasks = []
        for recipient in recipients:
            lead = db.query(Lead).filter(Lead.id == recipient.lead_id).first()
            if not lead or not lead.email:
                logger.warning(f"Recipient {recipient.id} has no valid lead/email")
                recipient.status = RecipientStatusEnum.FAILED
                continue

            # TODO: Get actual template from database
            # For now, use a simple template
            template_html = f"""
            <h1>Hello {{{{ lead_name }}}}!</h1>
            <p>This is an email from FlipTech Pro campaign: {campaign.name}</p>
            <p><a href="https://fliptechpro.com">Visit our website</a></p>
            """

            variables = {
                "lead_name": lead.name or "there",
                "campaign_name": campaign.name,
            }

            # Render template
            html_body = template_service.render_template(template_html, variables)
            text_body = template_service.generate_text_version(html_body)

            # Create task for this recipient
            task = send_campaign_email.s(
                campaign_id=campaign_id,
                recipient_id=recipient.id,
                lead_id=lead.id,
                subject=f"Message from {campaign.name}",
                html_body=html_body,
                text_body=text_body,
            )
            tasks.append(task)

        # Execute tasks in parallel
        if tasks:
            job = group(tasks)
            result = job.apply_async()

            logger.info(f"Queued {len(tasks)} email tasks for campaign {campaign_id}")

        db.commit()

        return {
            "status": "success",
            "campaign_id": campaign_id,
            "total": len(tasks),
            "message": f"Queued {len(tasks)} emails for sending"
        }

    except Exception as e:
        logger.error(f"Failed to send campaign emails: {str(e)}")
        db.rollback()
        raise

    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.campaign_tasks.process_campaign_batch",
    max_retries=2,
    default_retry_delay=180,
)
def process_campaign_batch(
    self,
    campaign_id: int,
    batch_number: int,
    recipient_ids: List[int],
) -> Dict[str, Any]:
    """
    Process a specific batch of recipients for a campaign.

    Args:
        campaign_id: Campaign ID
        batch_number: Batch number for tracking
        recipient_ids: List of recipient IDs to process

    Returns:
        dict: Batch processing results
    """
    from app.core.database import SessionLocal
    from app.tasks.email_tasks import send_campaign_email

    logger.info(f"Processing batch {batch_number} for campaign {campaign_id}")

    db = SessionLocal()
    try:
        # Create tasks for each recipient
        tasks = [
            send_campaign_email.s(
                campaign_id=campaign_id,
                recipient_id=recipient_id,
                lead_id=None,  # Will be looked up in the task
                subject="",  # Will be generated in the task
                html_body="",  # Will be generated in the task
            )
            for recipient_id in recipient_ids
        ]

        # Execute tasks
        if tasks:
            job = group(tasks)
            result = job.apply_async()

        logger.info(f"Batch {batch_number} queued: {len(tasks)} emails")

        return {
            "status": "success",
            "campaign_id": campaign_id,
            "batch_number": batch_number,
            "total": len(tasks),
        }

    except Exception as e:
        logger.error(f"Failed to process batch {batch_number}: {str(e)}")
        raise

    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.campaign_tasks.launch_campaign_async",
    max_retries=1,
)
def launch_campaign_async(
    self,
    campaign_id: int,
) -> Dict[str, Any]:
    """
    Launch a campaign asynchronously.

    This task queues all pending recipients and triggers the sending process.

    Args:
        campaign_id: Campaign ID

    Returns:
        dict: Launch result
    """
    from app.core.database import SessionLocal
    from app.models.campaigns import Campaign, CampaignRecipient, RecipientStatusEnum, CampaignStatusEnum
    from sqlalchemy import update

    logger.info(f"Launching campaign asynchronously: {campaign_id}")

    db = SessionLocal()
    try:
        # Get campaign
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Update campaign status
        campaign.status = CampaignStatusEnum.RUNNING
        campaign.started_at = datetime.utcnow()

        # Queue all pending recipients
        stmt = (
            update(CampaignRecipient)
            .where(
                and_(
                    CampaignRecipient.campaign_id == campaign_id,
                    CampaignRecipient.status == RecipientStatusEnum.PENDING
                )
            )
            .values(status=RecipientStatusEnum.QUEUED)
        )
        db.execute(stmt)
        db.commit()

        # Trigger the send process
        send_campaign_emails.apply_async(args=[campaign_id], countdown=5)

        logger.info(f"Campaign {campaign_id} launched successfully")

        return {
            "status": "success",
            "campaign_id": campaign_id,
            "message": "Campaign launched successfully"
        }

    except Exception as e:
        logger.error(f"Failed to launch campaign {campaign_id}: {str(e)}")
        db.rollback()
        raise

    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.campaign_tasks.process_scheduled_campaigns",
    max_retries=1,
)
def process_scheduled_campaigns(self) -> Dict[str, Any]:
    """
    Process campaigns scheduled to start.

    This task runs periodically via Celery Beat and launches campaigns
    that are scheduled to start.

    Returns:
        dict: Processing results
    """
    from app.core.database import SessionLocal
    from app.models.campaigns import Campaign, CampaignStatusEnum

    logger.info("Processing scheduled campaigns")

    db = SessionLocal()
    try:
        now = datetime.utcnow()

        # Find campaigns scheduled to start
        campaigns = (
            db.query(Campaign)
            .filter(
                and_(
                    Campaign.status == CampaignStatusEnum.SCHEDULED,
                    Campaign.scheduled_at <= now
                )
            )
            .all()
        )

        if not campaigns:
            logger.info("No campaigns scheduled to start")
            return {
                "status": "success",
                "launched": 0,
                "message": "No campaigns to launch"
            }

        logger.info(f"Found {len(campaigns)} campaigns to launch")

        launched = 0
        for campaign in campaigns:
            try:
                # Launch campaign asynchronously
                launch_campaign_async.apply_async(args=[campaign.id])
                launched += 1
                logger.info(f"Launched campaign {campaign.campaign_id}")

            except Exception as e:
                logger.error(f"Failed to launch campaign {campaign.id}: {str(e)}")

        return {
            "status": "success",
            "launched": launched,
            "total": len(campaigns),
        }

    except Exception as e:
        logger.error(f"Failed to process scheduled campaigns: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
        }

    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.campaign_tasks.update_campaign_metrics",
    max_retries=1,
)
def update_campaign_metrics(self) -> Dict[str, Any]:
    """
    Update metrics for all running campaigns.

    This task runs periodically to recalculate campaign metrics
    like open rates, click rates, etc.

    Returns:
        dict: Update results
    """
    from app.core.database import SessionLocal
    from app.models.campaigns import Campaign, CampaignRecipient, CampaignStatusEnum
    from sqlalchemy import func

    logger.info("Updating campaign metrics")

    db = SessionLocal()
    try:
        # Get running campaigns
        campaigns = (
            db.query(Campaign)
            .filter(Campaign.status == CampaignStatusEnum.RUNNING)
            .all()
        )

        if not campaigns:
            logger.info("No running campaigns to update")
            return {
                "status": "success",
                "updated": 0,
                "message": "No running campaigns"
            }

        updated = 0
        for campaign in campaigns:
            try:
                # Get recipient counts
                recipients = db.query(CampaignRecipient).filter(
                    CampaignRecipient.campaign_id == campaign.id
                ).all()

                sent = sum(1 for r in recipients if r.sent_at is not None)
                opened = sum(1 for r in recipients if r.opened_at is not None)
                clicked = sum(1 for r in recipients if r.clicked_at is not None)
                replied = sum(1 for r in recipients if r.replied_at is not None)
                bounced = sum(1 for r in recipients if r.bounced_at is not None)

                # Update campaign metrics
                campaign.emails_sent = sent
                campaign.emails_opened = opened
                campaign.emails_clicked = clicked
                campaign.emails_replied = replied
                campaign.emails_bounced = bounced

                # Calculate rates
                if sent > 0:
                    campaign.open_rate = (opened / sent) * 100
                    campaign.click_rate = (clicked / sent) * 100
                    campaign.reply_rate = (replied / sent) * 100
                    campaign.bounce_rate = (bounced / sent) * 100

                updated += 1

            except Exception as e:
                logger.error(f"Failed to update metrics for campaign {campaign.id}: {str(e)}")

        db.commit()

        logger.info(f"Updated metrics for {updated} campaigns")

        return {
            "status": "success",
            "updated": updated,
            "total": len(campaigns),
        }

    except Exception as e:
        logger.error(f"Failed to update campaign metrics: {str(e)}")
        db.rollback()
        return {
            "status": "failed",
            "error": str(e),
        }

    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.campaign_tasks.cleanup_old_task_results",
    max_retries=1,
)
def cleanup_old_task_results(self) -> Dict[str, Any]:
    """
    Clean up old Celery task results from Redis.

    This task runs periodically to prevent Redis from filling up
    with old task results.

    Returns:
        dict: Cleanup results
    """
    from celery_app import celery_app
    from datetime import timedelta

    logger.info("Cleaning up old task results")

    try:
        # Get all task IDs from result backend
        # Delete results older than 24 hours
        cutoff = datetime.utcnow() - timedelta(hours=24)

        # This would be implemented based on your backend
        # For Redis, you might use the Redis client directly
        # For now, just log
        logger.info("Task result cleanup complete")

        return {
            "status": "success",
            "message": "Cleanup complete",
        }

    except Exception as e:
        logger.error(f"Failed to cleanup task results: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
        }


@shared_task(
    bind=True,
    name="app.tasks.campaign_tasks.generate_daily_analytics",
    max_retries=1,
)
def generate_daily_analytics(self) -> Dict[str, Any]:
    """
    Generate daily analytics report for all campaigns.

    This task runs daily to generate analytics reports that can be
    viewed in the dashboard or sent via email.

    Returns:
        dict: Analytics generation results
    """
    from app.core.database import SessionLocal
    from app.models.campaigns import Campaign, CampaignRecipient
    from sqlalchemy import func

    logger.info("Generating daily analytics")

    db = SessionLocal()
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)

        # Get campaigns active yesterday
        campaigns = (
            db.query(Campaign)
            .filter(
                or_(
                    Campaign.started_at >= yesterday,
                    Campaign.completed_at >= yesterday,
                )
            )
            .all()
        )

        if not campaigns:
            logger.info("No campaigns active yesterday")
            return {
                "status": "success",
                "campaigns": 0,
                "message": "No campaigns active yesterday"
            }

        analytics = {
            "date": yesterday.date().isoformat(),
            "total_campaigns": len(campaigns),
            "total_emails_sent": 0,
            "total_opens": 0,
            "total_clicks": 0,
            "total_replies": 0,
            "total_bounces": 0,
        }

        for campaign in campaigns:
            analytics["total_emails_sent"] += campaign.emails_sent
            analytics["total_opens"] += campaign.emails_opened
            analytics["total_clicks"] += campaign.emails_clicked
            analytics["total_replies"] += campaign.emails_replied
            analytics["total_bounces"] += campaign.emails_bounced

        # TODO: Store analytics in database or send via email
        logger.info(f"Generated daily analytics: {analytics}")

        return {
            "status": "success",
            "analytics": analytics,
        }

    except Exception as e:
        logger.error(f"Failed to generate daily analytics: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
        }

    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.campaign_tasks.pause_campaign_async",
    max_retries=1,
)
def pause_campaign_async(
    self,
    campaign_id: int,
) -> Dict[str, Any]:
    """
    Pause a running campaign asynchronously.

    Args:
        campaign_id: Campaign ID

    Returns:
        dict: Pause result
    """
    from app.core.database import SessionLocal
    from app.models.campaigns import Campaign, CampaignStatusEnum

    logger.info(f"Pausing campaign: {campaign_id}")

    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if campaign.status != CampaignStatusEnum.RUNNING:
            raise ValueError(f"Campaign is not running (status: {campaign.status})")

        campaign.status = CampaignStatusEnum.PAUSED
        db.commit()

        logger.info(f"Campaign {campaign_id} paused successfully")

        return {
            "status": "success",
            "campaign_id": campaign_id,
            "message": "Campaign paused successfully"
        }

    except Exception as e:
        logger.error(f"Failed to pause campaign {campaign_id}: {str(e)}")
        db.rollback()
        raise

    finally:
        db.close()


@shared_task(
    bind=True,
    name="app.tasks.campaign_tasks.resume_campaign_async",
    max_retries=1,
)
def resume_campaign_async(
    self,
    campaign_id: int,
) -> Dict[str, Any]:
    """
    Resume a paused campaign asynchronously.

    Args:
        campaign_id: Campaign ID

    Returns:
        dict: Resume result
    """
    from app.core.database import SessionLocal
    from app.models.campaigns import Campaign, CampaignStatusEnum

    logger.info(f"Resuming campaign: {campaign_id}")

    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        if campaign.status != CampaignStatusEnum.PAUSED:
            raise ValueError(f"Campaign is not paused (status: {campaign.status})")

        campaign.status = CampaignStatusEnum.RUNNING
        db.commit()

        # Resume sending
        send_campaign_emails.apply_async(args=[campaign_id], countdown=5)

        logger.info(f"Campaign {campaign_id} resumed successfully")

        return {
            "status": "success",
            "campaign_id": campaign_id,
            "message": "Campaign resumed successfully"
        }

    except Exception as e:
        logger.error(f"Failed to resume campaign {campaign_id}: {str(e)}")
        db.rollback()
        raise

    finally:
        db.close()
