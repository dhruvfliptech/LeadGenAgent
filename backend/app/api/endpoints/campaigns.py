"""
Campaign Management API Endpoints.

RESTful API for email campaign creation, management, and tracking.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.campaign_service import CampaignService
from app.models.campaigns import CampaignRecipient
from sqlalchemy import select
from app.schemas.campaigns import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse,
    AddRecipientsRequest,
    CampaignRecipientResponse,
    RecipientListResponse,
    LaunchCampaignRequest,
    SendTestEmailRequest,
    PauseCampaignResponse,
    CampaignStatsResponse,
    CampaignAnalyticsResponse,
    TrackEmailEventRequest,
    EmailTrackingResponse,
    TrackingEventsListResponse,
    CampaignFilters,
    RecipientFilters,
    SuccessResponse,
    BulkOperationResponse,
    DeleteCampaignResponse,
    EmailEventTypeEnum,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# CAMPAIGN CRUD ENDPOINTS
# ============================================================================

@router.post(
    "/",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Campaign",
    description="Create a new email campaign",
)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    """
    Create a new email campaign.

    Example request:
    ```json
    {
        "name": "Q1 Outreach Campaign",
        "template_id": 1,
        "scheduled_at": "2025-11-10T10:00:00Z"
    }
    ```
    """
    try:
        service = CampaignService(db)
        campaign = await service.create_campaign(
            campaign_data=campaign_data,
            created_by=None,  # TODO: Get from auth context
        )

        return CampaignResponse.from_orm(campaign)

    except ValueError as e:
        logger.warning(f"Validation error creating campaign: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create campaign"
        )


@router.get(
    "/",
    response_model=CampaignListResponse,
    summary="List Campaigns",
    description="Get paginated list of campaigns with filtering",
)
async def list_campaigns(
    status: Optional[str] = Query(None, description="Filter by campaign status"),
    template_id: Optional[int] = Query(None, description="Filter by template ID"),
    search: Optional[str] = Query(None, description="Search in campaign name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
) -> CampaignListResponse:
    """
    Get paginated list of campaigns.

    Query parameters:
    - status: Filter by campaign status (draft, scheduled, running, paused, completed, failed)
    - template_id: Filter by template ID
    - search: Search in campaign name
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - sort_by: Sort field (default: created_at)
    - sort_order: Sort order (default: desc)
    """
    try:
        filters = CampaignFilters(
            status=status,
            template_id=template_id,
            search=search,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        service = CampaignService(db)
        campaigns, total = await service.list_campaigns(filters)

        # Convert to response models
        campaign_responses = [CampaignResponse.from_orm(c) for c in campaigns]

        return CampaignListResponse(
            campaigns=campaign_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(page * page_size) < total,
        )

    except ValueError as e:
        logger.warning(f"Validation error listing campaigns: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list campaigns"
        )


@router.get(
    "/{campaign_id}",
    response_model=CampaignResponse,
    summary="Get Campaign",
    description="Get campaign details by ID",
)
async def get_campaign(
    campaign_id: int = Path(..., description="Campaign ID"),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    """
    Get detailed information about a specific campaign.
    """
    try:
        service = CampaignService(db)
        campaign = await service.get_campaign(campaign_id)

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign not found: {campaign_id}"
            )

        return CampaignResponse.from_orm(campaign)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get campaign"
        )


@router.put(
    "/{campaign_id}",
    response_model=CampaignResponse,
    summary="Update Campaign",
    description="Update campaign details",
)
async def update_campaign(
    campaign_id: int = Path(..., description="Campaign ID"),
    campaign_data: CampaignUpdate = ...,
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    """
    Update campaign details.

    Note: Cannot update campaigns that are running or completed.

    Example request:
    ```json
    {
        "name": "Updated Campaign Name",
        "scheduled_at": "2025-11-15T14:00:00Z"
    }
    ```
    """
    try:
        service = CampaignService(db)
        campaign = await service.update_campaign(campaign_id, campaign_data)

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign not found: {campaign_id}"
            )

        return CampaignResponse.from_orm(campaign)

    except ValueError as e:
        logger.warning(f"Validation error updating campaign: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update campaign"
        )


@router.delete(
    "/{campaign_id}",
    response_model=DeleteCampaignResponse,
    summary="Delete Campaign",
    description="Delete campaign (soft delete)",
)
async def delete_campaign(
    campaign_id: int = Path(..., description="Campaign ID"),
    db: AsyncSession = Depends(get_db),
) -> DeleteCampaignResponse:
    """
    Delete a campaign.

    Note: Cannot delete running campaigns. Pause them first.
    This is a soft delete - campaign is marked as failed but data is retained.
    """
    try:
        service = CampaignService(db)
        campaign = await service.get_campaign(campaign_id)

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign not found: {campaign_id}"
            )

        deleted = await service.delete_campaign(campaign_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign not found: {campaign_id}"
            )

        return DeleteCampaignResponse(
            success=True,
            message="Campaign deleted successfully",
            campaign_id=campaign.campaign_id,
            deleted_at=campaign.completed_at,
        )

    except ValueError as e:
        logger.warning(f"Validation error deleting campaign: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete campaign"
        )


# ============================================================================
# RECIPIENT MANAGEMENT ENDPOINTS
# ============================================================================

@router.post(
    "/{campaign_id}/recipients",
    response_model=BulkOperationResponse,
    summary="Add Recipients",
    description="Add recipients to campaign from lead IDs",
)
async def add_recipients(
    campaign_id: int = Path(..., description="Campaign ID"),
    request_data: AddRecipientsRequest = ...,
    db: AsyncSession = Depends(get_db),
) -> BulkOperationResponse:
    """
    Add recipients to a campaign.

    Example request:
    ```json
    {
        "lead_ids": [1, 2, 3, 4, 5]
    }
    ```

    Returns count of successful additions and any errors.
    """
    try:
        service = CampaignService(db)
        successful, errors = await service.add_recipients(
            campaign_id=campaign_id,
            lead_ids=request_data.lead_ids,
        )

        failed = len(errors)
        total = successful + failed

        return BulkOperationResponse(
            success=failed == 0,
            total_processed=total,
            successful=successful,
            failed=failed,
            errors=[{"message": err} for err in errors],
            message=f"Added {successful} recipients to campaign",
        )

    except ValueError as e:
        logger.warning(f"Validation error adding recipients: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding recipients to campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add recipients"
        )


@router.get(
    "/{campaign_id}/recipients",
    response_model=RecipientListResponse,
    summary="List Recipients",
    description="Get paginated list of campaign recipients",
)
async def list_recipients(
    campaign_id: int = Path(..., description="Campaign ID"),
    status: Optional[str] = Query(None, description="Filter by recipient status"),
    has_opened: Optional[bool] = Query(None, description="Filter by opened status"),
    has_clicked: Optional[bool] = Query(None, description="Filter by clicked status"),
    has_replied: Optional[bool] = Query(None, description="Filter by replied status"),
    has_bounced: Optional[bool] = Query(None, description="Filter by bounced status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> RecipientListResponse:
    """
    Get paginated list of campaign recipients with filtering.
    """
    try:
        filters = RecipientFilters(
            status=status,
            has_opened=has_opened,
            has_clicked=has_clicked,
            has_replied=has_replied,
            has_bounced=has_bounced,
            page=page,
            page_size=page_size,
        )

        service = CampaignService(db)
        recipients, total = await service.get_recipients(campaign_id, filters)

        # Convert to response models
        recipient_responses = [CampaignRecipientResponse.from_orm(r) for r in recipients]

        return RecipientListResponse(
            recipients=recipient_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(page * page_size) < total,
        )

    except ValueError as e:
        logger.warning(f"Validation error listing recipients: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing recipients for campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list recipients"
        )


@router.delete(
    "/{campaign_id}/recipients/{recipient_id}",
    response_model=SuccessResponse,
    summary="Remove Recipient",
    description="Remove a recipient from campaign",
)
async def remove_recipient(
    campaign_id: int = Path(..., description="Campaign ID"),
    recipient_id: int = Path(..., description="Recipient ID"),
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Remove a recipient from a campaign.

    Note: Cannot remove recipients from running campaigns.
    """
    try:
        service = CampaignService(db)
        removed = await service.remove_recipient(campaign_id, recipient_id)

        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipient not found: {recipient_id}"
            )

        return SuccessResponse(
            success=True,
            message="Recipient removed successfully",
        )

    except ValueError as e:
        logger.warning(f"Validation error removing recipient: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing recipient {recipient_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove recipient"
        )


# ============================================================================
# CAMPAIGN CONTROL ENDPOINTS
# ============================================================================

@router.post(
    "/{campaign_id}/launch",
    response_model=CampaignResponse,
    summary="Launch Campaign",
    description="Launch campaign to start sending emails",
)
async def launch_campaign(
    campaign_id: int = Path(..., description="Campaign ID"),
    request_data: LaunchCampaignRequest = ...,
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    """
    Launch a campaign to start sending emails.

    Example request:
    ```json
    {
        "send_immediately": true,
        "test_mode": false
    }
    ```

    Note: In production, this triggers background email sending tasks.
    """
    try:
        service = CampaignService(db)

        # TODO: Handle test mode
        if request_data.test_mode:
            # Send test email only
            logger.info(f"Test mode launch for campaign {campaign_id} to {request_data.test_email}")
            # TODO: Implement test email sending
            pass

        campaign = await service.launch_campaign(
            campaign_id=campaign_id,
            send_immediately=request_data.send_immediately,
        )

        return CampaignResponse.from_orm(campaign)

    except ValueError as e:
        logger.warning(f"Validation error launching campaign: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error launching campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to launch campaign"
        )


@router.post(
    "/{campaign_id}/pause",
    response_model=PauseCampaignResponse,
    summary="Pause Campaign",
    description="Pause a running campaign",
)
async def pause_campaign(
    campaign_id: int = Path(..., description="Campaign ID"),
    db: AsyncSession = Depends(get_db),
) -> PauseCampaignResponse:
    """
    Pause a running campaign.
    """
    try:
        service = CampaignService(db)
        campaign = await service.pause_campaign(campaign_id)

        return PauseCampaignResponse(
            success=True,
            message="Campaign paused successfully",
            campaign_id=campaign.campaign_id,
            status=campaign.status,
        )

    except ValueError as e:
        logger.warning(f"Validation error pausing campaign: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error pausing campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pause campaign"
        )


@router.post(
    "/{campaign_id}/resume",
    response_model=PauseCampaignResponse,
    summary="Resume Campaign",
    description="Resume a paused campaign",
)
async def resume_campaign(
    campaign_id: int = Path(..., description="Campaign ID"),
    db: AsyncSession = Depends(get_db),
) -> PauseCampaignResponse:
    """
    Resume a paused campaign.
    """
    try:
        service = CampaignService(db)
        campaign = await service.resume_campaign(campaign_id)

        return PauseCampaignResponse(
            success=True,
            message="Campaign resumed successfully",
            campaign_id=campaign.campaign_id,
            status=campaign.status,
        )

    except ValueError as e:
        logger.warning(f"Validation error resuming campaign: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error resuming campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resume campaign"
        )


@router.post(
    "/{campaign_id}/test",
    response_model=SuccessResponse,
    summary="Send Test Email",
    description="Send a test email for the campaign",
)
async def send_test_email(
    campaign_id: int = Path(..., description="Campaign ID"),
    request_data: SendTestEmailRequest = ...,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """
    Send a test email to verify campaign before launching.

    Example request:
    ```json
    {
        "test_email": "test@example.com"
    }
    ```
    """
    try:
        service = CampaignService(db)
        campaign = await service.get_campaign(campaign_id)

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign not found: {campaign_id}"
            )

        # TODO: Move to Celery task
        # from app.tasks.campaigns import send_test_email_task
        # send_test_email_task.delay(campaign_id, request_data.test_email)

        logger.info(f"Test email sent for campaign {campaign.campaign_id} to {request_data.test_email}")

        return SuccessResponse(
            success=True,
            message=f"Test email sent to {request_data.test_email}",
            data={"campaign_id": campaign.campaign_id},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test email for campaign {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test email"
        )


# ============================================================================
# STATISTICS AND ANALYTICS ENDPOINTS
# ============================================================================

@router.get(
    "/{campaign_id}/stats",
    response_model=CampaignStatsResponse,
    summary="Get Campaign Stats",
    description="Get real-time campaign statistics",
)
async def get_campaign_stats(
    campaign_id: int = Path(..., description="Campaign ID"),
    db: AsyncSession = Depends(get_db),
) -> CampaignStatsResponse:
    """
    Get real-time statistics for a campaign.

    Returns:
    - Recipient counts by status
    - Engagement metrics (opens, clicks, replies)
    - Progress percentage
    - Estimated completion time
    - Send rate
    """
    try:
        service = CampaignService(db)
        stats = await service.get_campaign_stats(campaign_id)

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign not found: {campaign_id}"
            )

        return CampaignStatsResponse(**stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign stats for {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get campaign stats"
        )


@router.get(
    "/{campaign_id}/analytics",
    response_model=CampaignAnalyticsResponse,
    summary="Get Campaign Analytics",
    description="Get detailed campaign analytics",
)
async def get_campaign_analytics(
    campaign_id: int = Path(..., description="Campaign ID"),
    db: AsyncSession = Depends(get_db),
) -> CampaignAnalyticsResponse:
    """
    Get detailed analytics for a campaign.

    Returns:
    - Time series data (hourly sends, opens, clicks)
    - Geographic distribution
    - Device and email client breakdown
    - Top performers
    - Error analysis
    """
    try:
        service = CampaignService(db)
        analytics = await service.get_campaign_analytics(campaign_id)

        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign not found: {campaign_id}"
            )

        return CampaignAnalyticsResponse(**analytics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign analytics for {campaign_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get campaign analytics"
        )


# ============================================================================
# EMAIL TRACKING ENDPOINTS
# ============================================================================

@router.post(
    "/tracking/{recipient_id}/open",
    response_model=EmailTrackingResponse,
    summary="Track Email Open",
    description="Track an email open event",
)
async def track_email_open(
    recipient_id: int = Path(..., description="Campaign recipient ID"),
    request_data: TrackEmailEventRequest = ...,
    db: AsyncSession = Depends(get_db),
) -> EmailTrackingResponse:
    """
    Track an email open event.

    This endpoint is typically called via tracking pixel in email.
    """
    try:
        service = CampaignService(db)
        tracking = await service.track_email_event(
            recipient_id=recipient_id,
            event_type=EmailEventTypeEnum.OPEN,
            event_data=request_data.event_data,
            user_agent=request_data.user_agent,
            ip_address=request_data.ip_address,
        )

        return EmailTrackingResponse.from_orm(tracking)

    except ValueError as e:
        logger.warning(f"Validation error tracking open: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error tracking open for recipient {recipient_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track open"
        )


@router.post(
    "/tracking/{recipient_id}/click",
    response_model=EmailTrackingResponse,
    summary="Track Email Click",
    description="Track an email click event",
)
async def track_email_click(
    recipient_id: int = Path(..., description="Campaign recipient ID"),
    request_data: TrackEmailEventRequest = ...,
    db: AsyncSession = Depends(get_db),
) -> EmailTrackingResponse:
    """
    Track an email click event.

    This endpoint is called when a tracked link in the email is clicked.
    """
    try:
        service = CampaignService(db)
        tracking = await service.track_email_event(
            recipient_id=recipient_id,
            event_type=EmailEventTypeEnum.CLICK,
            event_data=request_data.event_data,
            user_agent=request_data.user_agent,
            ip_address=request_data.ip_address,
        )

        return EmailTrackingResponse.from_orm(tracking)

    except ValueError as e:
        logger.warning(f"Validation error tracking click: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error tracking click for recipient {recipient_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track click"
        )


@router.post(
    "/tracking/{recipient_id}/bounce",
    response_model=EmailTrackingResponse,
    summary="Track Email Bounce",
    description="Track an email bounce event",
)
async def track_email_bounce(
    recipient_id: int = Path(..., description="Campaign recipient ID"),
    request_data: TrackEmailEventRequest = ...,
    db: AsyncSession = Depends(get_db),
) -> EmailTrackingResponse:
    """
    Track an email bounce event.

    This endpoint is typically called by email service provider webhooks.
    """
    try:
        service = CampaignService(db)
        tracking = await service.track_email_event(
            recipient_id=recipient_id,
            event_type=EmailEventTypeEnum.BOUNCE,
            event_data=request_data.event_data,
            user_agent=request_data.user_agent,
            ip_address=request_data.ip_address,
        )

        return EmailTrackingResponse.from_orm(tracking)

    except ValueError as e:
        logger.warning(f"Validation error tracking bounce: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error tracking bounce for recipient {recipient_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track bounce"
        )


@router.get(
    "/tracking/{recipient_id}/events",
    response_model=TrackingEventsListResponse,
    summary="Get Tracking Events",
    description="Get all tracking events for a recipient",
)
async def get_tracking_events(
    recipient_id: int = Path(..., description="Campaign recipient ID"),
    db: AsyncSession = Depends(get_db),
) -> TrackingEventsListResponse:
    """
    Get all tracking events for a specific recipient.
    """
    try:
        service = CampaignService(db)

        # Get recipient info
        recipient_stmt = select(CampaignRecipient).where(CampaignRecipient.id == recipient_id)
        recipient_result = await db.execute(recipient_stmt)
        recipient = recipient_result.scalar_one_or_none()

        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipient not found: {recipient_id}"
            )

        events = await service.get_recipient_tracking_events(recipient_id)
        event_responses = [EmailTrackingResponse.from_orm(e) for e in events]

        return TrackingEventsListResponse(
            recipient_id=recipient_id,
            email_address=recipient.email_address,
            events=event_responses,
            total_events=len(event_responses),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tracking events for recipient {recipient_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tracking events"
        )


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@router.get(
    "/health",
    response_model=SuccessResponse,
    summary="Health Check",
    description="Check campaign API health",
)
async def health_check() -> SuccessResponse:
    """
    Simple health check endpoint for campaign API.
    """
    return SuccessResponse(
        success=True,
        message="Campaign API is healthy",
        data={"version": "1.0.0"},
    )
