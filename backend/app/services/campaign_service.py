"""
Campaign Service Layer.

Business logic for campaign management, email sending, and tracking.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, update, delete, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.campaigns import Campaign, CampaignRecipient, EmailTracking
from app.models.leads import Lead
from app.schemas.campaigns import (
    CampaignCreate,
    CampaignUpdate,
    CampaignStatusEnum,
    RecipientStatusEnum,
    EmailEventTypeEnum,
    CampaignFilters,
    RecipientFilters,
)

logger = logging.getLogger(__name__)


class CampaignService:
    """Service class for campaign operations."""

    def __init__(self, db: AsyncSession):
        """Initialize campaign service with database session."""
        self.db = db

    # ============================================================================
    # CAMPAIGN CRUD OPERATIONS
    # ============================================================================

    async def create_campaign(
        self,
        campaign_data: CampaignCreate,
        created_by: Optional[int] = None
    ) -> Campaign:
        """
        Create a new campaign.

        Args:
            campaign_data: Campaign creation data
            created_by: User ID who created the campaign

        Returns:
            Created campaign object

        Raises:
            ValueError: If validation fails
        """
        try:
            # Generate unique campaign ID
            campaign_id = f"camp_{uuid.uuid4().hex[:12]}"

            # Create campaign object
            campaign = Campaign(
                campaign_id=campaign_id,
                name=campaign_data.name,
                template_id=campaign_data.template_id,
                status=CampaignStatusEnum.DRAFT,
                scheduled_at=campaign_data.scheduled_at,
                created_by=created_by,
            )

            self.db.add(campaign)
            await self.db.commit()
            await self.db.refresh(campaign)

            logger.info(f"Created campaign: {campaign_id} - {campaign_data.name}")
            return campaign

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create campaign: {e}")
            raise

    async def get_campaign(self, campaign_id: int) -> Optional[Campaign]:
        """
        Get campaign by ID.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign object or None if not found
        """
        try:
            stmt = select(Campaign).where(Campaign.id == campaign_id)
            result = await self.db.execute(stmt)
            campaign = result.scalar_one_or_none()

            if campaign:
                logger.info(f"Retrieved campaign: {campaign.campaign_id}")
            else:
                logger.warning(f"Campaign not found: {campaign_id}")

            return campaign

        except Exception as e:
            logger.error(f"Failed to get campaign {campaign_id}: {e}")
            raise

    async def get_campaign_by_campaign_id(self, campaign_id: str) -> Optional[Campaign]:
        """
        Get campaign by campaign_id string.

        Args:
            campaign_id: Campaign ID string (e.g., 'camp_abc123')

        Returns:
            Campaign object or None if not found
        """
        try:
            stmt = select(Campaign).where(Campaign.campaign_id == campaign_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Failed to get campaign {campaign_id}: {e}")
            raise

    async def list_campaigns(self, filters: CampaignFilters) -> Tuple[List[Campaign], int]:
        """
        List campaigns with pagination and filtering.

        Args:
            filters: Campaign filters

        Returns:
            Tuple of (campaigns list, total count)
        """
        try:
            # Build base query
            stmt = select(Campaign)

            # Apply filters
            conditions = []

            if filters.status:
                conditions.append(Campaign.status == filters.status)

            if filters.template_id:
                conditions.append(Campaign.template_id == filters.template_id)

            if filters.created_by:
                conditions.append(Campaign.created_by == filters.created_by)

            if filters.search:
                conditions.append(Campaign.name.ilike(f"%{filters.search}%"))

            if filters.date_from:
                conditions.append(Campaign.created_at >= filters.date_from)

            if filters.date_to:
                conditions.append(Campaign.created_at <= filters.date_to)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            # Get total count
            count_stmt = select(func.count()).select_from(stmt.alias())
            total_result = await self.db.execute(count_stmt)
            total = total_result.scalar()

            # Apply sorting
            sort_column = getattr(Campaign, filters.sort_by)
            if filters.sort_order == "desc":
                stmt = stmt.order_by(desc(sort_column))
            else:
                stmt = stmt.order_by(asc(sort_column))

            # Apply pagination
            offset = (filters.page - 1) * filters.page_size
            stmt = stmt.offset(offset).limit(filters.page_size)

            # Execute query
            result = await self.db.execute(stmt)
            campaigns = result.scalars().all()

            logger.info(f"Listed {len(campaigns)} campaigns (total: {total})")
            return list(campaigns), total

        except Exception as e:
            logger.error(f"Failed to list campaigns: {e}")
            raise

    async def update_campaign(
        self,
        campaign_id: int,
        campaign_data: CampaignUpdate
    ) -> Optional[Campaign]:
        """
        Update campaign details.

        Args:
            campaign_id: Campaign ID
            campaign_data: Updated campaign data

        Returns:
            Updated campaign object or None if not found

        Raises:
            ValueError: If campaign is already running/completed
        """
        try:
            campaign = await self.get_campaign(campaign_id)
            if not campaign:
                return None

            # Prevent updates to running/completed campaigns
            if campaign.status in [CampaignStatusEnum.RUNNING, CampaignStatusEnum.COMPLETED]:
                raise ValueError(f"Cannot update campaign in '{campaign.status}' status")

            # Update fields
            update_data = campaign_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(campaign, field, value)

            await self.db.commit()
            await self.db.refresh(campaign)

            logger.info(f"Updated campaign: {campaign.campaign_id}")
            return campaign

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update campaign {campaign_id}: {e}")
            raise

    async def delete_campaign(self, campaign_id: int) -> bool:
        """
        Delete campaign (soft delete by marking as failed/archived).

        Args:
            campaign_id: Campaign ID

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If campaign is currently running
        """
        try:
            campaign = await self.get_campaign(campaign_id)
            if not campaign:
                return False

            # Prevent deletion of running campaigns
            if campaign.status == CampaignStatusEnum.RUNNING:
                raise ValueError("Cannot delete a running campaign. Pause it first.")

            # Soft delete by marking as failed
            campaign.status = CampaignStatusEnum.FAILED
            campaign.completed_at = datetime.utcnow()

            await self.db.commit()

            logger.info(f"Deleted campaign: {campaign.campaign_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete campaign {campaign_id}: {e}")
            raise

    # ============================================================================
    # RECIPIENT MANAGEMENT
    # ============================================================================

    async def add_recipients(
        self,
        campaign_id: int,
        lead_ids: List[int]
    ) -> Tuple[int, List[str]]:
        """
        Add recipients to campaign from lead IDs.

        Args:
            campaign_id: Campaign ID
            lead_ids: List of lead IDs to add

        Returns:
            Tuple of (successful_count, error_messages)

        Raises:
            ValueError: If campaign not found or invalid state
        """
        try:
            campaign = await self.get_campaign(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign not found: {campaign_id}")

            # Prevent adding recipients to running/completed campaigns
            if campaign.status in [CampaignStatusEnum.RUNNING, CampaignStatusEnum.COMPLETED]:
                raise ValueError(f"Cannot add recipients to campaign in '{campaign.status}' status")

            # Fetch leads
            stmt = select(Lead).where(Lead.id.in_(lead_ids))
            result = await self.db.execute(stmt)
            leads = result.scalars().all()

            # Track results
            successful = 0
            errors = []

            for lead in leads:
                try:
                    # Validate lead has email
                    if not lead.email:
                        errors.append(f"Lead {lead.id} has no email address")
                        continue

                    # Check if already added
                    existing_stmt = select(CampaignRecipient).where(
                        and_(
                            CampaignRecipient.campaign_id == campaign_id,
                            CampaignRecipient.lead_id == lead.id
                        )
                    )
                    existing_result = await self.db.execute(existing_stmt)
                    if existing_result.scalar_one_or_none():
                        errors.append(f"Lead {lead.id} already added to campaign")
                        continue

                    # Create recipient
                    recipient = CampaignRecipient(
                        campaign_id=campaign_id,
                        lead_id=lead.id,
                        email_address=lead.email,
                        status=RecipientStatusEnum.PENDING,
                    )
                    self.db.add(recipient)
                    successful += 1

                except Exception as e:
                    errors.append(f"Lead {lead.id}: {str(e)}")
                    logger.error(f"Failed to add lead {lead.id} to campaign: {e}")

            # Update campaign recipient count
            campaign.total_recipients = campaign.total_recipients + successful

            await self.db.commit()

            logger.info(f"Added {successful} recipients to campaign {campaign.campaign_id}")
            return successful, errors

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to add recipients to campaign {campaign_id}: {e}")
            raise

    async def get_recipients(
        self,
        campaign_id: int,
        filters: RecipientFilters
    ) -> Tuple[List[CampaignRecipient], int]:
        """
        Get campaign recipients with filtering and pagination.

        Args:
            campaign_id: Campaign ID
            filters: Recipient filters

        Returns:
            Tuple of (recipients list, total count)
        """
        try:
            # Build base query with eager loading to avoid N+1 queries
            stmt = (
                select(CampaignRecipient)
                .options(
                    selectinload(CampaignRecipient.campaign),  # Eager load campaign
                    selectinload(CampaignRecipient.tracking_events)  # Eager load tracking events
                )
                .where(CampaignRecipient.campaign_id == campaign_id)
            )

            # Apply filters
            conditions = []

            if filters.status:
                conditions.append(CampaignRecipient.status == filters.status)

            if filters.has_opened is not None:
                if filters.has_opened:
                    conditions.append(CampaignRecipient.opened_at.isnot(None))
                else:
                    conditions.append(CampaignRecipient.opened_at.is_(None))

            if filters.has_clicked is not None:
                if filters.has_clicked:
                    conditions.append(CampaignRecipient.clicked_at.isnot(None))
                else:
                    conditions.append(CampaignRecipient.clicked_at.is_(None))

            if filters.has_replied is not None:
                if filters.has_replied:
                    conditions.append(CampaignRecipient.replied_at.isnot(None))
                else:
                    conditions.append(CampaignRecipient.replied_at.is_(None))

            if filters.has_bounced is not None:
                if filters.has_bounced:
                    conditions.append(CampaignRecipient.bounced_at.isnot(None))
                else:
                    conditions.append(CampaignRecipient.bounced_at.is_(None))

            if conditions:
                stmt = stmt.where(and_(*conditions))

            # Get total count
            count_stmt = select(func.count()).select_from(stmt.alias())
            total_result = await self.db.execute(count_stmt)
            total = total_result.scalar()

            # Apply pagination
            offset = (filters.page - 1) * filters.page_size
            stmt = stmt.offset(offset).limit(filters.page_size)

            # Execute query
            result = await self.db.execute(stmt)
            recipients = result.scalars().all()

            logger.info(f"Retrieved {len(recipients)} recipients (total: {total})")
            return list(recipients), total

        except Exception as e:
            logger.error(f"Failed to get recipients for campaign {campaign_id}: {e}")
            raise

    async def remove_recipient(self, campaign_id: int, recipient_id: int) -> bool:
        """
        Remove a recipient from campaign.

        Args:
            campaign_id: Campaign ID
            recipient_id: Recipient ID

        Returns:
            True if removed, False if not found

        Raises:
            ValueError: If campaign is running
        """
        try:
            campaign = await self.get_campaign(campaign_id)
            if not campaign:
                return False

            # Prevent removal from running campaigns
            if campaign.status == CampaignStatusEnum.RUNNING:
                raise ValueError("Cannot remove recipients from running campaign")

            # Find and delete recipient
            stmt = delete(CampaignRecipient).where(
                and_(
                    CampaignRecipient.campaign_id == campaign_id,
                    CampaignRecipient.id == recipient_id
                )
            )
            result = await self.db.execute(stmt)

            if result.rowcount > 0:
                # Update campaign recipient count
                campaign.total_recipients = campaign.total_recipients - 1
                await self.db.commit()

                logger.info(f"Removed recipient {recipient_id} from campaign {campaign.campaign_id}")
                return True
            else:
                return False

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to remove recipient {recipient_id}: {e}")
            raise

    # ============================================================================
    # CAMPAIGN CONTROL
    # ============================================================================

    async def send_campaign_emails_sync(
        self,
        campaign_id: int,
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Send campaign emails synchronously (for testing/small campaigns).

        WARNING: This is a blocking operation. For production use, move to Celery.

        Args:
            campaign_id: Campaign ID
            batch_size: Number of emails to send in each batch

        Returns:
            Dictionary with send results

        Note:
            TODO: Move to Celery task for production use
            This should be called from a background worker, not directly from API
        """
        try:
            from app.services.email_service import EmailService
            from app.services.email_template_service import EmailTemplateService

            campaign = await self.get_campaign(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign not found: {campaign_id}")

            # Get template service
            template_service = EmailTemplateService()

            # Get queued recipients
            stmt = select(CampaignRecipient).where(
                and_(
                    CampaignRecipient.campaign_id == campaign_id,
                    CampaignRecipient.status == RecipientStatusEnum.QUEUED
                )
            ).options(selectinload(CampaignRecipient.lead)).limit(batch_size)

            result = await self.db.execute(stmt)
            recipients = result.scalars().all()

            if not recipients:
                logger.info(f"No queued recipients for campaign {campaign_id}")
                return {
                    "total": 0,
                    "sent": 0,
                    "failed": 0,
                    "errors": []
                }

            # Convert async session to sync for EmailService
            # EmailService uses sync database operations
            from app.db.database import SessionLocal
            sync_db = SessionLocal()

            try:
                email_service = EmailService(db=sync_db)

                results = {
                    "total": len(recipients),
                    "sent": 0,
                    "failed": 0,
                    "errors": []
                }

                for recipient in recipients:
                    try:
                        # Get lead
                        lead = recipient.lead
                        if not lead or not lead.email:
                            logger.warning(f"Recipient {recipient.id} has no valid email")
                            recipient.status = RecipientStatusEnum.FAILED
                            results["failed"] += 1
                            continue

                        # Generate tracking token
                        tracking_token = email_service._generate_tracking_token(
                            campaign.id,
                            lead.id
                        )

                        # TODO: Get actual template from database
                        # For now, use a simple template
                        template_html = f"""
                        <h1>Hello {{{{ lead_name }}}}!</h1>
                        <p>This is a test email from FlipTech Pro campaign: {campaign.name}</p>
                        <p><a href="https://fliptechpro.com">Visit our website</a></p>
                        """

                        variables = {
                            "lead_name": lead.name or "there",
                            "campaign_name": campaign.name
                        }

                        # Render template
                        html_body = template_service.render_template(template_html, variables)

                        # Add tracking
                        html_body = template_service.add_tracking_pixel(html_body, tracking_token)
                        html_body = template_service.wrap_links_for_tracking(html_body, tracking_token)
                        html_body = template_service.add_unsubscribe_link(html_body, tracking_token)

                        # Generate text version
                        text_body = template_service.generate_text_version(html_body)

                        # Send email
                        send_result = email_service.send_email(
                            to_email=lead.email,
                            subject=f"Message from {campaign.name}",  # TODO: Get from template
                            html_body=html_body,
                            text_body=text_body,
                            tracking_token=tracking_token
                        )

                        # Update recipient status
                        recipient.status = RecipientStatusEnum.SENT
                        recipient.sent_at = datetime.utcnow()
                        campaign.emails_sent += 1

                        results["sent"] += 1
                        logger.info(f"Sent email to {lead.email} for campaign {campaign_id}")

                    except Exception as e:
                        logger.error(f"Failed to send email to recipient {recipient.id}: {e}")
                        recipient.status = RecipientStatusEnum.FAILED
                        campaign.emails_failed += 1
                        results["failed"] += 1
                        results["errors"].append({
                            "recipient_id": recipient.id,
                            "email": lead.email if lead else "unknown",
                            "error": str(e)
                        })

                # Update campaign metrics
                if results["sent"] > 0:
                    campaign.last_sent_at = datetime.utcnow()

                # Check if campaign is complete
                remaining_stmt = select(func.count()).select_from(CampaignRecipient).where(
                    and_(
                        CampaignRecipient.campaign_id == campaign_id,
                        CampaignRecipient.status == RecipientStatusEnum.QUEUED
                    )
                )
                remaining_result = await self.db.execute(remaining_stmt)
                remaining_count = remaining_result.scalar()

                if remaining_count == 0:
                    campaign.status = CampaignStatusEnum.COMPLETED
                    campaign.completed_at = datetime.utcnow()
                    logger.info(f"Campaign {campaign_id} completed")

                await self.db.commit()
                sync_db.commit()

                logger.info(
                    f"Campaign {campaign_id} batch complete: "
                    f"{results['sent']}/{results['total']} sent, "
                    f"{results['failed']} failed"
                )

                return results

            finally:
                sync_db.close()

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to send campaign emails: {e}")
            raise

    async def launch_campaign(
        self,
        campaign_id: int,
        send_immediately: bool = True
    ) -> Campaign:
        """
        Launch a campaign to start sending emails.

        Args:
            campaign_id: Campaign ID
            send_immediately: If True, start sending now; otherwise use scheduled_at

        Returns:
            Updated campaign object

        Raises:
            ValueError: If campaign invalid or has no recipients

        Note:
            In production, this will trigger Celery background tasks for email sending.
            For now, it updates status and queues recipients.
        """
        try:
            campaign = await self.get_campaign(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign not found: {campaign_id}")

            # Validate campaign state
            if campaign.status not in [CampaignStatusEnum.DRAFT, CampaignStatusEnum.SCHEDULED]:
                raise ValueError(f"Campaign cannot be launched from '{campaign.status}' status")

            # Validate has recipients
            if campaign.total_recipients == 0:
                raise ValueError("Campaign has no recipients")

            # Update campaign status
            if send_immediately:
                campaign.status = CampaignStatusEnum.RUNNING
                campaign.started_at = datetime.utcnow()

                # Queue all pending recipients
                stmt = update(CampaignRecipient).where(
                    and_(
                        CampaignRecipient.campaign_id == campaign_id,
                        CampaignRecipient.status == RecipientStatusEnum.PENDING
                    )
                ).values(status=RecipientStatusEnum.QUEUED)
                await self.db.execute(stmt)

                # Launch campaign asynchronously using Celery
                try:
                    from app.tasks.campaign_tasks import launch_campaign_async
                    launch_campaign_async.apply_async(args=[campaign_id], countdown=5)
                    logger.info(f"Launched campaign asynchronously: {campaign.campaign_id}")
                except ImportError:
                    # Fallback if Celery not available
                    logger.warning("Celery not available. Call send_campaign_emails_sync() manually.")
                    logger.info(f"Note: Call send_campaign_emails_sync({campaign_id}) to start sending")
            else:
                campaign.status = CampaignStatusEnum.SCHEDULED
                if not campaign.scheduled_at:
                    raise ValueError("Campaign must have scheduled_at for delayed launch")

                # Schedule Celery task for future execution
                try:
                    from app.tasks.campaign_tasks import launch_campaign_async
                    launch_campaign_async.apply_async(
                        args=[campaign_id],
                        eta=campaign.scheduled_at
                    )
                    logger.info(f"Scheduled campaign for {campaign.scheduled_at}: {campaign.campaign_id}")
                except ImportError:
                    logger.warning("Celery not available. Campaign will need to be launched manually.")
                    logger.info(f"Scheduled campaign for {campaign.scheduled_at}: {campaign.campaign_id}")

            await self.db.commit()
            await self.db.refresh(campaign)

            return campaign

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to launch campaign {campaign_id}: {e}")
            raise

    async def pause_campaign(self, campaign_id: int) -> Campaign:
        """
        Pause a running campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            Updated campaign object

        Raises:
            ValueError: If campaign not running
        """
        try:
            campaign = await self.get_campaign(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign not found: {campaign_id}")

            if campaign.status != CampaignStatusEnum.RUNNING:
                raise ValueError(f"Campaign is not running (status: {campaign.status})")

            campaign.status = CampaignStatusEnum.PAUSED

            # Pause campaign asynchronously using Celery
            try:
                from app.tasks.campaign_tasks import pause_campaign_async
                pause_campaign_async.apply_async(args=[campaign_id])
            except ImportError:
                logger.warning("Celery not available for async pause")

            await self.db.commit()
            await self.db.refresh(campaign)

            logger.info(f"Paused campaign: {campaign.campaign_id}")
            return campaign

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to pause campaign {campaign_id}: {e}")
            raise

    async def resume_campaign(self, campaign_id: int) -> Campaign:
        """
        Resume a paused campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            Updated campaign object

        Raises:
            ValueError: If campaign not paused
        """
        try:
            campaign = await self.get_campaign(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign not found: {campaign_id}")

            if campaign.status != CampaignStatusEnum.PAUSED:
                raise ValueError(f"Campaign is not paused (status: {campaign.status})")

            campaign.status = CampaignStatusEnum.RUNNING

            # Resume campaign asynchronously using Celery
            try:
                from app.tasks.campaign_tasks import resume_campaign_async
                resume_campaign_async.apply_async(args=[campaign_id])
            except ImportError:
                logger.warning("Celery not available for async resume")

            await self.db.commit()
            await self.db.refresh(campaign)

            logger.info(f"Resumed campaign: {campaign.campaign_id}")
            return campaign

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to resume campaign {campaign_id}: {e}")
            raise

    # ============================================================================
    # STATISTICS AND ANALYTICS
    # ============================================================================

    async def get_campaign_stats(self, campaign_id: int) -> Optional[Dict[str, Any]]:
        """
        Get real-time campaign statistics.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign statistics dictionary or None if not found
        """
        try:
            campaign = await self.get_campaign(campaign_id)
            if not campaign:
                return None

            # Get recipient status counts
            status_counts_stmt = select(
                CampaignRecipient.status,
                func.count(CampaignRecipient.id).label("count")
            ).where(
                CampaignRecipient.campaign_id == campaign_id
            ).group_by(CampaignRecipient.status)

            status_result = await self.db.execute(status_counts_stmt)
            status_counts = {row.status: row.count for row in status_result}

            # Calculate progress
            total_recipients = campaign.total_recipients
            sent = status_counts.get(RecipientStatusEnum.SENT, 0)
            progress_percentage = (sent / total_recipients * 100) if total_recipients > 0 else 0

            # Calculate estimated completion time
            estimated_completion = None
            emails_per_hour = None
            if campaign.started_at and campaign.status == CampaignStatusEnum.RUNNING:
                elapsed = (datetime.utcnow() - campaign.started_at).total_seconds() / 3600
                if elapsed > 0 and sent > 0:
                    emails_per_hour = sent / elapsed
                    remaining = total_recipients - sent
                    hours_remaining = remaining / emails_per_hour
                    estimated_completion = datetime.utcnow() + timedelta(hours=hours_remaining)

            stats = {
                "campaign_id": campaign.campaign_id,
                "campaign_name": campaign.name,
                "status": campaign.status,
                "total_recipients": total_recipients,
                "pending": status_counts.get(RecipientStatusEnum.PENDING, 0),
                "queued": status_counts.get(RecipientStatusEnum.QUEUED, 0),
                "sent": sent,
                "failed": status_counts.get(RecipientStatusEnum.FAILED, 0),
                "bounced": status_counts.get(RecipientStatusEnum.BOUNCED, 0),
                "opened": campaign.emails_opened,
                "clicked": campaign.emails_clicked,
                "replied": campaign.emails_replied,
                "metrics": {
                    "emails_sent": campaign.emails_sent,
                    "emails_opened": campaign.emails_opened,
                    "emails_clicked": campaign.emails_clicked,
                    "emails_replied": campaign.emails_replied,
                    "emails_bounced": campaign.emails_bounced,
                    "open_rate": round(campaign.open_rate, 2),
                    "click_rate": round(campaign.click_rate, 2),
                    "reply_rate": round(campaign.reply_rate, 2),
                    "bounce_rate": round(campaign.bounce_rate, 2),
                },
                "scheduled_at": campaign.scheduled_at,
                "started_at": campaign.started_at,
                "completed_at": campaign.completed_at,
                "estimated_completion": estimated_completion,
                "progress_percentage": round(progress_percentage, 2),
                "emails_per_hour": round(emails_per_hour, 2) if emails_per_hour else None,
            }

            logger.info(f"Retrieved stats for campaign {campaign.campaign_id}")
            return stats

        except Exception as e:
            logger.error(f"Failed to get campaign stats for {campaign_id}: {e}")
            raise

    async def get_campaign_analytics(self, campaign_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed campaign analytics.

        Args:
            campaign_id: Campaign ID

        Returns:
            Detailed analytics dictionary or None if not found
        """
        try:
            campaign = await self.get_campaign(campaign_id)
            if not campaign:
                return None

            # Get basic stats
            stats = await self.get_campaign_stats(campaign_id)

            # Get tracking events for analytics
            tracking_stmt = select(EmailTracking).join(
                CampaignRecipient,
                EmailTracking.campaign_recipient_id == CampaignRecipient.id
            ).where(CampaignRecipient.campaign_id == campaign_id)

            tracking_result = await self.db.execute(tracking_stmt)
            tracking_events = tracking_result.scalars().all()

            # Analyze tracking data
            opens_by_location = {}
            opens_by_device = {}
            bounce_reasons = {}

            for event in tracking_events:
                if event.event_type == EmailEventTypeEnum.OPEN:
                    # Parse device info from user agent (simplified)
                    if event.user_agent:
                        if "Mobile" in event.user_agent:
                            device = "Mobile"
                        elif "Tablet" in event.user_agent:
                            device = "Tablet"
                        else:
                            device = "Desktop"
                        opens_by_device[device] = opens_by_device.get(device, 0) + 1

                    # Track location if available
                    if event.ip_address:
                        # In production, use IP geolocation service
                        location = "Unknown"
                        opens_by_location[location] = opens_by_location.get(location, 0) + 1

                elif event.event_type == EmailEventTypeEnum.BOUNCE:
                    reason = event.event_data.get("reason", "Unknown") if event.event_data else "Unknown"
                    bounce_reasons[reason] = bounce_reasons.get(reason, 0) + 1

            analytics = {
                "campaign": campaign.to_dict(),
                "stats": stats,
                "hourly_sends": [],  # TODO: Implement time series data
                "hourly_opens": [],  # TODO: Implement time series data
                "hourly_clicks": [],  # TODO: Implement time series data
                "opens_by_location": opens_by_location,
                "clicks_by_location": {},  # TODO: Implement
                "opens_by_device": opens_by_device,
                "opens_by_email_client": {},  # TODO: Parse from user agent
                "top_openers": [],  # TODO: Implement
                "top_clickers": [],  # TODO: Implement
                "bounce_reasons": bounce_reasons,
                "error_messages": {},  # TODO: Aggregate from recipients
            }

            logger.info(f"Retrieved analytics for campaign {campaign.campaign_id}")
            return analytics

        except Exception as e:
            logger.error(f"Failed to get campaign analytics for {campaign_id}: {e}")
            raise

    # ============================================================================
    # EMAIL TRACKING
    # ============================================================================

    async def track_email_event(
        self,
        recipient_id: int,
        event_type: EmailEventTypeEnum,
        event_data: Optional[Dict[str, Any]] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> EmailTracking:
        """
        Track an email event (open, click, bounce, etc.).

        Args:
            recipient_id: Campaign recipient ID
            event_type: Type of event
            event_data: Additional event metadata
            user_agent: Client user agent
            ip_address: Client IP address

        Returns:
            Created tracking event

        Raises:
            ValueError: If recipient not found
        """
        try:
            # Verify recipient exists
            recipient_stmt = select(CampaignRecipient).where(
                CampaignRecipient.id == recipient_id
            )
            recipient_result = await self.db.execute(recipient_stmt)
            recipient = recipient_result.scalar_one_or_none()

            if not recipient:
                raise ValueError(f"Recipient not found: {recipient_id}")

            # Create tracking event
            tracking = EmailTracking(
                campaign_recipient_id=recipient_id,
                event_type=event_type,
                event_data=event_data or {},
                user_agent=user_agent,
                ip_address=ip_address,
            )
            self.db.add(tracking)

            # Update recipient timestamps and campaign metrics
            now = datetime.utcnow()
            campaign = await self.get_campaign(recipient.campaign_id)

            if event_type == EmailEventTypeEnum.OPEN:
                if not recipient.opened_at:
                    recipient.opened_at = now
                    campaign.emails_opened += 1

            elif event_type == EmailEventTypeEnum.CLICK:
                if not recipient.clicked_at:
                    recipient.clicked_at = now
                    campaign.emails_clicked += 1

            elif event_type == EmailEventTypeEnum.BOUNCE:
                if not recipient.bounced_at:
                    recipient.bounced_at = now
                    recipient.status = RecipientStatusEnum.BOUNCED
                    campaign.emails_bounced += 1

            elif event_type == EmailEventTypeEnum.REPLY:
                if not recipient.replied_at:
                    recipient.replied_at = now
                    campaign.emails_replied += 1

            await self.db.commit()
            await self.db.refresh(tracking)

            logger.info(f"Tracked {event_type} event for recipient {recipient_id}")
            return tracking

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to track email event: {e}")
            raise

    async def get_recipient_tracking_events(
        self,
        recipient_id: int
    ) -> List[EmailTracking]:
        """
        Get all tracking events for a recipient.

        Args:
            recipient_id: Campaign recipient ID

        Returns:
            List of tracking events
        """
        try:
            stmt = select(EmailTracking).where(
                EmailTracking.campaign_recipient_id == recipient_id
            ).order_by(EmailTracking.created_at.desc())

            result = await self.db.execute(stmt)
            events = result.scalars().all()

            logger.info(f"Retrieved {len(events)} tracking events for recipient {recipient_id}")
            return list(events)

        except Exception as e:
            logger.error(f"Failed to get tracking events for recipient {recipient_id}: {e}")
            raise
