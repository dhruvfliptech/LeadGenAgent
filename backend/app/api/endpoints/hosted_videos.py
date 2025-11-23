"""
Hosted Videos API endpoints for Phase 4 Video Hosting.

Provides REST API for video hosting, management, and analytics.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.hosted_videos import HostedVideo, VideoView
from app.models.demo_sites import DemoSite
from app.models.leads import Lead
from app.services.video.video_host_manager import (
    VideoHostManager,
    VideoMetadata,
    HostedVideoResponse,
    VideoHostManagerError
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models

class UploadVideoRequest(BaseModel):
    """Request to upload video."""
    video_path: str = Field(..., description="Path to video file")
    title: str = Field(..., description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    demo_site_id: int = Field(..., description="Demo site ID")
    lead_id: int = Field(..., description="Lead ID")
    company_name: Optional[str] = Field(None, description="Company name")
    tags: List[str] = Field(default_factory=list, description="Video tags")
    privacy: str = Field("unlisted", description="Privacy setting")
    host_preference: Optional[str] = Field(None, description="Preferred host (loom, s3, auto)")
    duration_seconds: Optional[float] = None
    resolution: Optional[str] = None
    file_size_bytes: Optional[int] = None


class UpdateVideoRequest(BaseModel):
    """Request to update video metadata."""
    title: Optional[str] = None
    description: Optional[str] = None
    privacy: Optional[str] = None


class TrackViewRequest(BaseModel):
    """Request to track video view."""
    viewer_ip: Optional[str] = None
    viewer_location: Optional[str] = None
    viewer_device: Optional[str] = None
    viewer_os: Optional[str] = None
    viewer_browser: Optional[str] = None
    watch_duration_seconds: float = 0.0
    watch_percentage: float = 0.0
    completed: bool = False
    clicked_cta: bool = False
    session_id: Optional[str] = None
    referrer_url: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


class VideoAnalyticsResponse(BaseModel):
    """Video analytics response."""
    video_id: int
    provider: str
    views: Dict[str, Any]
    engagement: Dict[str, Any]
    cost: Dict[str, Any]
    provider_analytics: Optional[Dict[str, Any]] = None


class HostingStatsResponse(BaseModel):
    """Hosting statistics response."""
    total_videos: int
    by_provider: Dict[str, int]
    total_views: int
    total_storage_gb: float
    total_cost_usd: float
    cost_per_video: float
    cost_per_view: float


# Endpoints

@router.post("/upload", response_model=HostedVideoResponse)
async def upload_video(
    request: UploadVideoRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload video to hosting provider.

    Uploads video to Loom (primary) or S3 (fallback) and creates database record.

    Args:
        request: Upload request with video details
        db: Database session

    Returns:
        Hosted video details with shareable URLs

    Raises:
        HTTPException: If upload fails
    """
    try:
        # Verify video file exists
        if not os.path.exists(request.video_path):
            raise HTTPException(status_code=404, detail=f"Video file not found: {request.video_path}")

        # Verify demo site exists
        result = await db.execute(
            select(DemoSite).where(DemoSite.id == request.demo_site_id)
        )
        demo_site = result.scalar_one_or_none()
        if not demo_site:
            raise HTTPException(status_code=404, detail=f"Demo site not found: {request.demo_site_id}")

        # Verify lead exists
        result = await db.execute(
            select(Lead).where(Lead.id == request.lead_id)
        )
        lead = result.scalar_one_or_none()
        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead not found: {request.lead_id}")

        # Get file info if not provided
        file_size_bytes = request.file_size_bytes or os.path.getsize(request.video_path)

        # Create metadata
        metadata = VideoMetadata(
            title=request.title,
            description=request.description,
            demo_site_id=request.demo_site_id,
            lead_id=request.lead_id,
            company_name=request.company_name or lead.business_name,
            tags=request.tags,
            privacy=request.privacy,
            duration_seconds=request.duration_seconds,
            resolution=request.resolution,
            file_size_bytes=file_size_bytes
        )

        # Upload video
        manager = VideoHostManager(db)
        hosted_video = await manager.upload_video(
            video_path=request.video_path,
            metadata=metadata,
            host_preference=request.host_preference
        )

        logger.info(f"Video uploaded successfully: {hosted_video.id} ({hosted_video.hosting_provider})")

        return hosted_video

    except VideoHostManagerError as e:
        logger.error(f"Video upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during video upload: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


@router.get("/{video_id}", response_model=Dict[str, Any])
async def get_video(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get video details.

    Args:
        video_id: Hosted video ID
        db: Database session

    Returns:
        Video details

    Raises:
        HTTPException: If video not found
    """
    result = await db.execute(
        select(HostedVideo).where(HostedVideo.id == video_id)
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video not found: {video_id}")

    return video.to_dict()


@router.get("/{video_id}/share")
async def get_shareable_link(
    video_id: int,
    regenerate: bool = Query(True, description="Regenerate expired S3 URLs"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get shareable link for video.

    Args:
        video_id: Hosted video ID
        regenerate: Regenerate S3 signed URL if expired
        db: Database session

    Returns:
        Shareable URL

    Raises:
        HTTPException: If video not found
    """
    try:
        manager = VideoHostManager(db)
        share_url = await manager.get_shareable_link(
            hosted_video_id=video_id,
            regenerate_if_expired=regenerate
        )

        return {
            "video_id": video_id,
            "share_url": share_url
        }

    except VideoHostManagerError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get shareable link: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get shareable link: {e}")


@router.get("/{video_id}/embed")
async def get_embed_code(
    video_id: int,
    width: int = Query(640, description="Embed width"),
    height: int = Query(360, description="Embed height"),
    autoplay: bool = Query(False, description="Auto-play video"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get embed code for video.

    Args:
        video_id: Hosted video ID
        width: Embed width
        height: Embed height
        autoplay: Auto-play video
        db: Database session

    Returns:
        HTML embed code

    Raises:
        HTTPException: If video not found
    """
    try:
        manager = VideoHostManager(db)
        embed_code = await manager.get_embed_code(
            hosted_video_id=video_id,
            width=width,
            height=height,
            autoplay=autoplay
        )

        return {
            "video_id": video_id,
            "embed_code": embed_code,
            "width": width,
            "height": height
        }

    except VideoHostManagerError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get embed code: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get embed code: {e}")


@router.put("/{video_id}", response_model=Dict[str, Any])
async def update_video(
    video_id: int,
    request: UpdateVideoRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update video metadata.

    Args:
        video_id: Hosted video ID
        request: Update request
        db: Database session

    Returns:
        Success status

    Raises:
        HTTPException: If video not found or update fails
    """
    try:
        manager = VideoHostManager(db)
        success = await manager.update_video_metadata(
            hosted_video_id=video_id,
            title=request.title,
            description=request.description,
            privacy=request.privacy
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update video")

        return {
            "video_id": video_id,
            "success": True,
            "message": "Video updated successfully"
        }

    except VideoHostManagerError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update video: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update video: {e}")


@router.delete("/{video_id}")
async def delete_video(
    video_id: int,
    delete_from_provider: bool = Query(True, description="Also delete from hosting provider"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete video.

    Args:
        video_id: Hosted video ID
        delete_from_provider: Also delete from Loom/S3
        db: Database session

    Returns:
        Success status

    Raises:
        HTTPException: If video not found or deletion fails
    """
    try:
        manager = VideoHostManager(db)
        success = await manager.delete_video(
            hosted_video_id=video_id,
            delete_from_provider=delete_from_provider
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete video")

        return {
            "video_id": video_id,
            "success": True,
            "message": "Video deleted successfully"
        }

    except VideoHostManagerError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete video: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete video: {e}")


@router.get("/demo/{demo_id}", response_model=List[Dict[str, Any]])
async def get_videos_for_demo(
    demo_id: int,
    include_deleted: bool = Query(False, description="Include deleted videos"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all videos for a demo site.

    Args:
        demo_id: Demo site ID
        include_deleted: Include soft-deleted videos
        db: Database session

    Returns:
        List of videos

    Raises:
        HTTPException: If demo site not found
    """
    # Verify demo site exists
    result = await db.execute(
        select(DemoSite).where(DemoSite.id == demo_id)
    )
    demo_site = result.scalar_one_or_none()
    if not demo_site:
        raise HTTPException(status_code=404, detail=f"Demo site not found: {demo_id}")

    # Get videos
    query = select(HostedVideo).where(HostedVideo.demo_site_id == demo_id)

    if not include_deleted:
        query = query.where(HostedVideo.is_deleted == False)

    result = await db.execute(query.order_by(HostedVideo.created_at.desc()))
    videos = result.scalars().all()

    return [video.to_dict() for video in videos]


@router.get("/{video_id}/analytics", response_model=VideoAnalyticsResponse)
async def get_video_analytics(
    video_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get video analytics.

    Args:
        video_id: Hosted video ID
        db: Database session

    Returns:
        Analytics data

    Raises:
        HTTPException: If video not found
    """
    try:
        manager = VideoHostManager(db)
        analytics = await manager.get_analytics(video_id)

        return VideoAnalyticsResponse(**analytics)

    except VideoHostManagerError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {e}")


@router.post("/{video_id}/track-view")
async def track_video_view(
    video_id: int,
    request: TrackViewRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Track video view.

    Records view event with engagement metrics.

    Args:
        video_id: Hosted video ID
        request: View tracking data
        background_tasks: Background task handler
        db: Database session

    Returns:
        Success status

    Raises:
        HTTPException: If video not found
    """
    # Verify video exists
    result = await db.execute(
        select(HostedVideo).where(HostedVideo.id == video_id)
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video not found: {video_id}")

    try:
        # Create view record
        view = VideoView(
            hosted_video_id=video_id,
            lead_id=video.lead_id,
            viewer_ip=request.viewer_ip,
            viewer_location=request.viewer_location,
            viewer_device=request.viewer_device,
            viewer_os=request.viewer_os,
            viewer_browser=request.viewer_browser,
            watch_duration_seconds=request.watch_duration_seconds,
            watch_percentage=request.watch_percentage,
            completed=request.completed,
            clicked_cta=request.clicked_cta,
            session_id=request.session_id,
            referrer_url=request.referrer_url,
            utm_source=request.utm_source,
            utm_medium=request.utm_medium,
            utm_campaign=request.utm_campaign,
            viewed_at=datetime.now(timezone.utc)
        )

        db.add(view)

        # Update video stats
        await db.execute(
            update(HostedVideo)
            .where(HostedVideo.id == video_id)
            .values(
                view_count=HostedVideo.view_count + 1,
                last_viewed_at=datetime.now(timezone.utc),
                total_watch_time_seconds=HostedVideo.total_watch_time_seconds + request.watch_duration_seconds
            )
        )

        await db.commit()

        # Schedule background task to update analytics
        background_tasks.add_task(update_video_analytics, video_id, db)

        logger.info(f"Tracked view for video {video_id}: {request.watch_percentage:.1f}% watched")

        return {
            "video_id": video_id,
            "success": True,
            "message": "View tracked successfully"
        }

    except Exception as e:
        logger.error(f"Failed to track view: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to track view: {e}")


@router.get("/stats/overview", response_model=HostingStatsResponse)
async def get_hosting_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall hosting statistics.

    Returns:
        Hosting statistics including costs and usage

    """
    try:
        manager = VideoHostManager(db)
        stats = await manager.get_hosting_stats()

        return HostingStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get hosting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get hosting stats: {e}")


@router.get("/lead/{lead_id}", response_model=List[Dict[str, Any]])
async def get_videos_for_lead(
    lead_id: int,
    include_deleted: bool = Query(False, description="Include deleted videos"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all videos for a lead.

    Args:
        lead_id: Lead ID
        include_deleted: Include soft-deleted videos
        db: Database session

    Returns:
        List of videos

    Raises:
        HTTPException: If lead not found
    """
    # Verify lead exists
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead not found: {lead_id}")

    # Get videos
    query = select(HostedVideo).where(HostedVideo.lead_id == lead_id)

    if not include_deleted:
        query = query.where(HostedVideo.is_deleted == False)

    result = await db.execute(query.order_by(HostedVideo.created_at.desc()))
    videos = result.scalars().all()

    return [video.to_dict() for video in videos]


@router.get("/{video_id}/views", response_model=List[Dict[str, Any]])
async def get_video_views(
    video_id: int,
    limit: int = Query(100, description="Maximum results"),
    offset: int = Query(0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed view records for video.

    Args:
        video_id: Hosted video ID
        limit: Maximum results
        offset: Pagination offset
        db: Database session

    Returns:
        List of view records

    Raises:
        HTTPException: If video not found
    """
    # Verify video exists
    result = await db.execute(
        select(HostedVideo).where(HostedVideo.id == video_id)
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail=f"Video not found: {video_id}")

    # Get views
    result = await db.execute(
        select(VideoView)
        .where(VideoView.hosted_video_id == video_id)
        .order_by(VideoView.viewed_at.desc())
        .limit(limit)
        .offset(offset)
    )
    views = result.scalars().all()

    return [view.to_dict() for view in views]


# Background tasks

async def update_video_analytics(video_id: int, db: AsyncSession):
    """
    Background task to update video analytics.

    Calculates aggregate metrics from view records.

    Args:
        video_id: Hosted video ID
        db: Database session
    """
    try:
        # Get all views
        result = await db.execute(
            select(VideoView).where(VideoView.hosted_video_id == video_id)
        )
        views = result.scalars().all()

        if not views:
            return

        # Calculate metrics
        total_views = len(views)
        unique_viewers = len(set(v.viewer_ip for v in views if v.viewer_ip))
        avg_watch_percentage = sum(v.watch_percentage for v in views) / total_views
        avg_watch_duration = sum(v.watch_duration_seconds for v in views) / total_views
        completion_rate = sum(1 for v in views if v.completed) / total_views * 100
        click_through_rate = sum(1 for v in views if v.clicked_cta) / total_views * 100

        # Update video
        await db.execute(
            update(HostedVideo)
            .where(HostedVideo.id == video_id)
            .values(
                unique_viewers=unique_viewers,
                avg_watch_percentage=avg_watch_percentage,
                avg_watch_duration_seconds=avg_watch_duration,
                completion_rate=completion_rate,
                click_through_rate=click_through_rate
            )
        )

        await db.commit()

        logger.info(f"Updated analytics for video {video_id}")

    except Exception as e:
        logger.error(f"Failed to update video analytics: {e}")
        await db.rollback()
