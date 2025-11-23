"""
Video Host Manager for Phase 4 Video Hosting.

Unified interface for Loom and S3 video hosting with automatic failover.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from decimal import Decimal
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.integrations.loom_client import (
    LoomClient,
    LoomVideo,
    LoomClientError,
    LoomQuotaExceededError,
    LoomUploadError
)
from app.integrations.s3_video_storage import (
    S3VideoStorage,
    S3Upload,
    S3StorageError
)
from app.models.hosted_videos import HostedVideo, VideoView
from app.models.demo_sites import DemoSite
from app.models.leads import Lead

logger = logging.getLogger(__name__)


class VideoMetadata(BaseModel):
    """Video metadata for hosting."""
    title: str
    description: Optional[str] = None
    demo_site_id: int
    lead_id: int
    company_name: Optional[str] = None
    tags: List[str] = []
    privacy: str = "unlisted"
    duration_seconds: Optional[float] = None
    resolution: Optional[str] = None
    file_size_bytes: Optional[int] = None


class HostedVideoResponse(BaseModel):
    """Response model for hosted video."""
    id: int
    hosting_provider: str
    provider_video_id: str
    share_url: str
    embed_url: str
    thumbnail_url: Optional[str]
    status: str
    privacy: str
    analytics_enabled: bool
    view_count: int = 0
    upload_time_seconds: Optional[float]
    cost_usd: float


class VideoHostManagerError(Exception):
    """Base exception for video host manager errors."""
    pass


class VideoHostManager:
    """
    Unified video hosting manager with Loom and S3 support.

    Features:
    - Smart host selection (Loom vs S3)
    - Automatic failover on errors
    - Cost optimization
    - Analytics tracking
    - Unified interface
    """

    def __init__(
        self,
        db: AsyncSession,
        loom_client: Optional[LoomClient] = None,
        s3_storage: Optional[S3VideoStorage] = None,
        default_host: str = "loom",
        enable_failover: bool = True
    ):
        """
        Initialize video host manager.

        Args:
            db: Database session
            loom_client: Loom client instance (or auto-created)
            s3_storage: S3 storage instance (or auto-created)
            default_host: Default hosting provider (loom, s3)
            enable_failover: Enable automatic failover
        """
        self.db = db
        self.default_host = os.getenv("VIDEO_HOST_PRIMARY", default_host)
        self.fallback_host = os.getenv("VIDEO_HOST_FALLBACK", "s3")
        self.enable_failover = enable_failover

        # Initialize clients
        self._loom_client = loom_client
        self._s3_storage = s3_storage

        # Cost tracking
        self.loom_cost_per_user_monthly = 12.0  # Business plan
        self.s3_storage_cost_per_gb = 0.023
        self.s3_transfer_cost_per_gb = 0.085

        logger.info(f"Initialized VideoHostManager: default={self.default_host}, failover={enable_failover}")

    @property
    def loom_client(self) -> Optional[LoomClient]:
        """Get or create Loom client."""
        if self._loom_client is None and os.getenv("LOOM_API_KEY"):
            try:
                self._loom_client = LoomClient()
            except Exception as e:
                logger.warning(f"Failed to initialize Loom client: {e}")
        return self._loom_client

    @property
    def s3_storage(self) -> Optional[S3VideoStorage]:
        """Get or create S3 storage."""
        if self._s3_storage is None and os.getenv("S3_BUCKET_NAME"):
            try:
                self._s3_storage = S3VideoStorage()
            except Exception as e:
                logger.warning(f"Failed to initialize S3 storage: {e}")
        return self._s3_storage

    async def upload_video(
        self,
        video_path: str,
        metadata: VideoMetadata,
        host_preference: Optional[str] = None
    ) -> HostedVideoResponse:
        """
        Upload video to hosting provider.

        Args:
            video_path: Path to video file
            metadata: Video metadata
            host_preference: Preferred host (loom, s3, auto) or None for default

        Returns:
            HostedVideoResponse with hosting details

        Raises:
            VideoHostManagerError: If upload fails on all providers
        """
        # Determine hosting provider
        host = self._select_host(host_preference, metadata)

        logger.info(f"Uploading video to {host}: {metadata.title}")

        # Try primary host
        try:
            if host == "loom":
                return await self._upload_to_loom(video_path, metadata)
            elif host == "s3":
                return await self._upload_to_s3(video_path, metadata)
            else:
                raise VideoHostManagerError(f"Unsupported hosting provider: {host}")

        except (LoomClientError, LoomQuotaExceededError, LoomUploadError) as e:
            logger.warning(f"Loom upload failed: {e}")

            # Try failover to S3
            if self.enable_failover and host == "loom" and self.s3_storage:
                logger.info("Failing over to S3...")
                try:
                    return await self._upload_to_s3(video_path, metadata)
                except Exception as s3_error:
                    logger.error(f"S3 failover also failed: {s3_error}")
                    raise VideoHostManagerError(f"Upload failed on both Loom and S3: {e}, {s3_error}")

            raise VideoHostManagerError(f"Upload failed: {e}")

        except S3StorageError as e:
            logger.warning(f"S3 upload failed: {e}")

            # Try failover to Loom
            if self.enable_failover and host == "s3" and self.loom_client:
                logger.info("Failing over to Loom...")
                try:
                    return await self._upload_to_loom(video_path, metadata)
                except Exception as loom_error:
                    logger.error(f"Loom failover also failed: {loom_error}")
                    raise VideoHostManagerError(f"Upload failed on both S3 and Loom: {e}, {loom_error}")

            raise VideoHostManagerError(f"Upload failed: {e}")

    async def _upload_to_loom(
        self,
        video_path: str,
        metadata: VideoMetadata
    ) -> HostedVideoResponse:
        """Upload video to Loom."""
        if not self.loom_client:
            raise VideoHostManagerError("Loom client not configured")

        upload_start = datetime.now(timezone.utc)

        # Upload to Loom
        loom_video = await self.loom_client.upload_video(
            video_path=video_path,
            title=metadata.title,
            description=metadata.description,
            privacy=metadata.privacy or "unlisted",
            folder_id=self.loom_client.default_folder_id
        )

        upload_duration = (datetime.now(timezone.utc) - upload_start).total_seconds()

        # Create database record
        hosted_video = HostedVideo(
            demo_site_id=metadata.demo_site_id,
            lead_id=metadata.lead_id,
            hosting_provider="loom",
            provider_video_id=loom_video.video_id,
            share_url=loom_video.share_url,
            embed_url=loom_video.embed_url,
            thumbnail_url=loom_video.thumbnail_url,
            title=metadata.title,
            description=metadata.description,
            company_name=metadata.company_name,
            tags=metadata.tags,
            privacy=metadata.privacy or "unlisted",
            duration_seconds=metadata.duration_seconds,
            file_size_bytes=metadata.file_size_bytes,
            resolution=metadata.resolution,
            status="processing" if loom_video.status == "processing" else "ready",
            upload_started_at=upload_start,
            upload_completed_at=datetime.now(timezone.utc),
            upload_time_seconds=upload_duration,
            loom_folder_id=self.loom_client.default_folder_id,
            loom_workspace_id=self.loom_client.workspace_id,
            hosting_cost_monthly=Decimal(str(self.loom_cost_per_user_monthly)),
            total_cost_usd=Decimal(str(self.loom_cost_per_user_monthly)),
            analytics_enabled=True,
            is_active=True
        )

        self.db.add(hosted_video)
        await self.db.commit()
        await self.db.refresh(hosted_video)

        logger.info(f"Video uploaded to Loom: {hosted_video.id} ({loom_video.video_id})")

        return HostedVideoResponse(
            id=hosted_video.id,
            hosting_provider="loom",
            provider_video_id=loom_video.video_id,
            share_url=loom_video.share_url,
            embed_url=loom_video.embed_url,
            thumbnail_url=loom_video.thumbnail_url,
            status=hosted_video.status,
            privacy=hosted_video.privacy,
            analytics_enabled=True,
            view_count=0,
            upload_time_seconds=upload_duration,
            cost_usd=float(self.loom_cost_per_user_monthly)
        )

    async def _upload_to_s3(
        self,
        video_path: str,
        metadata: VideoMetadata
    ) -> HostedVideoResponse:
        """Upload video to S3."""
        if not self.s3_storage:
            raise VideoHostManagerError("S3 storage not configured")

        upload_start = datetime.now(timezone.utc)

        # Prepare S3 metadata
        s3_metadata = {
            'title': metadata.title,
            'lead_id': str(metadata.lead_id),
            'demo_site_id': str(metadata.demo_site_id)
        }

        if metadata.company_name:
            s3_metadata['company_name'] = metadata.company_name

        # Upload to S3
        s3_upload = await self.s3_storage.upload_video(
            video_path=video_path,
            metadata=s3_metadata
        )

        upload_duration = (datetime.now(timezone.utc) - upload_start).total_seconds()

        # Calculate costs
        storage_cost = self._calculate_s3_storage_cost(s3_upload.size_bytes)

        # Create database record
        hosted_video = HostedVideo(
            demo_site_id=metadata.demo_site_id,
            lead_id=metadata.lead_id,
            hosting_provider="s3",
            provider_video_id=s3_upload.key,
            share_url=s3_upload.signed_url,
            embed_url=s3_upload.signed_url,  # S3 doesn't have embed, use signed URL
            thumbnail_url=None,  # S3 doesn't auto-generate thumbnails
            title=metadata.title,
            description=metadata.description,
            company_name=metadata.company_name,
            tags=metadata.tags,
            privacy="private",  # S3 uses signed URLs, effectively private
            duration_seconds=metadata.duration_seconds,
            file_size_bytes=s3_upload.size_bytes,
            resolution=metadata.resolution,
            status="ready",
            upload_started_at=upload_start,
            upload_completed_at=datetime.now(timezone.utc),
            upload_time_seconds=upload_duration,
            s3_bucket=s3_upload.bucket,
            s3_key=s3_upload.key,
            s3_region=self.s3_storage.region,
            cloudfront_url=s3_upload.cloudfront_url,
            signed_url_expiration=datetime.now(timezone.utc),  # Track expiration
            storage_cost_monthly=Decimal(str(storage_cost)),
            total_cost_usd=Decimal(str(storage_cost)),
            cdn_enabled=bool(s3_upload.cloudfront_url),
            analytics_enabled=False,  # S3 doesn't have built-in analytics
            is_active=True
        )

        self.db.add(hosted_video)
        await self.db.commit()
        await self.db.refresh(hosted_video)

        logger.info(f"Video uploaded to S3: {hosted_video.id} ({s3_upload.key})")

        return HostedVideoResponse(
            id=hosted_video.id,
            hosting_provider="s3",
            provider_video_id=s3_upload.key,
            share_url=s3_upload.signed_url,
            embed_url=s3_upload.signed_url,
            thumbnail_url=None,
            status="ready",
            privacy="private",
            analytics_enabled=False,
            view_count=0,
            upload_time_seconds=upload_duration,
            cost_usd=storage_cost
        )

    async def get_shareable_link(
        self,
        hosted_video_id: int,
        include_analytics: bool = True,
        regenerate_if_expired: bool = True
    ) -> str:
        """
        Get shareable link for video.

        Args:
            hosted_video_id: Hosted video ID
            include_analytics: Include analytics tracking
            regenerate_if_expired: Regenerate S3 signed URL if expired

        Returns:
            Shareable URL
        """
        result = await self.db.execute(
            select(HostedVideo).where(HostedVideo.id == hosted_video_id)
        )
        video = result.scalar_one_or_none()

        if not video:
            raise VideoHostManagerError(f"Video not found: {hosted_video_id}")

        if video.hosting_provider == "loom":
            return video.share_url

        elif video.hosting_provider == "s3":
            # Check if signed URL expired
            if regenerate_if_expired and self.s3_storage:
                if video.signed_url_expiration and video.signed_url_expiration < datetime.now(timezone.utc):
                    logger.info(f"Regenerating expired S3 signed URL for video {video.id}")
                    new_url = await self.s3_storage.generate_signed_url(video.s3_key)

                    # Update database
                    await self.db.execute(
                        update(HostedVideo)
                        .where(HostedVideo.id == hosted_video_id)
                        .values(
                            share_url=new_url,
                            signed_url_expiration=datetime.now(timezone.utc)
                        )
                    )
                    await self.db.commit()

                    return new_url

            return video.share_url

        else:
            raise VideoHostManagerError(f"Unsupported provider: {video.hosting_provider}")

    async def get_embed_code(
        self,
        hosted_video_id: int,
        width: int = 640,
        height: int = 360,
        autoplay: bool = False
    ) -> str:
        """
        Get embed code for video.

        Args:
            hosted_video_id: Hosted video ID
            width: Embed width
            height: Embed height
            autoplay: Auto-play video

        Returns:
            HTML embed code
        """
        result = await self.db.execute(
            select(HostedVideo).where(HostedVideo.id == hosted_video_id)
        )
        video = result.scalar_one_or_none()

        if not video:
            raise VideoHostManagerError(f"Video not found: {hosted_video_id}")

        if video.hosting_provider == "loom" and self.loom_client:
            return await self.loom_client.get_embed_code(
                video_id=video.provider_video_id,
                width=width,
                height=height,
                autoplay=autoplay
            )

        elif video.hosting_provider == "s3":
            # Generate HTML5 video embed
            video_url = await self.get_shareable_link(hosted_video_id)
            autoplay_attr = "autoplay" if autoplay else ""

            return f'''<video width="{width}" height="{height}" controls {autoplay_attr}>
    <source src="{video_url}" type="video/mp4">
    Your browser does not support the video tag.
</video>'''

        else:
            raise VideoHostManagerError(f"Unsupported provider: {video.hosting_provider}")

    async def update_video_metadata(
        self,
        hosted_video_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        privacy: Optional[str] = None
    ) -> bool:
        """
        Update video metadata.

        Args:
            hosted_video_id: Hosted video ID
            title: New title
            description: New description
            privacy: New privacy setting

        Returns:
            True if successful
        """
        result = await self.db.execute(
            select(HostedVideo).where(HostedVideo.id == hosted_video_id)
        )
        video = result.scalar_one_or_none()

        if not video:
            raise VideoHostManagerError(f"Video not found: {hosted_video_id}")

        # Update provider metadata
        if video.hosting_provider == "loom" and self.loom_client:
            success = await self.loom_client.update_video(
                video_id=video.provider_video_id,
                title=title,
                description=description,
                privacy=privacy
            )

            if not success:
                return False

        # Update database
        update_data = {}
        if title is not None:
            update_data['title'] = title
        if description is not None:
            update_data['description'] = description
        if privacy is not None:
            update_data['privacy'] = privacy

        if update_data:
            await self.db.execute(
                update(HostedVideo)
                .where(HostedVideo.id == hosted_video_id)
                .values(**update_data)
            )
            await self.db.commit()

        logger.info(f"Updated video metadata: {hosted_video_id}")
        return True

    async def get_analytics(self, hosted_video_id: int) -> Dict[str, Any]:
        """
        Get video analytics.

        Args:
            hosted_video_id: Hosted video ID

        Returns:
            Analytics dictionary
        """
        result = await self.db.execute(
            select(HostedVideo).where(HostedVideo.id == hosted_video_id)
        )
        video = result.scalar_one_or_none()

        if not video:
            raise VideoHostManagerError(f"Video not found: {hosted_video_id}")

        analytics = {
            'video_id': video.id,
            'provider': video.hosting_provider,
            'views': {
                'total': video.view_count,
                'unique': video.unique_viewers,
                'last_viewed': video.last_viewed_at.isoformat() if video.last_viewed_at else None
            },
            'engagement': {
                'avg_watch_percentage': video.avg_watch_percentage,
                'avg_watch_duration_seconds': video.avg_watch_duration_seconds,
                'total_watch_time_seconds': video.total_watch_time_seconds,
                'completion_rate': video.completion_rate,
                'likes': video.likes_count,
                'comments': video.comments_count,
                'shares': video.shares_count
            },
            'cost': {
                'hosting_monthly': float(video.hosting_cost_monthly),
                'storage_monthly': float(video.storage_cost_monthly),
                'bandwidth_monthly': float(video.bandwidth_cost_monthly),
                'total_usd': float(video.total_cost_usd),
                'cost_per_view': float(video.cost_per_view) if video.cost_per_view else None
            }
        }

        # Fetch provider analytics if available
        if video.hosting_provider == "loom" and self.loom_client:
            try:
                loom_analytics = await self.loom_client.get_video_analytics(video.provider_video_id)
                analytics['provider_analytics'] = {
                    'engagement_score': loom_analytics.engagement_score,
                    'top_referrers': loom_analytics.top_referrers,
                    'viewer_locations': loom_analytics.viewer_locations,
                    'daily_views': loom_analytics.daily_views
                }
            except Exception as e:
                logger.warning(f"Failed to fetch Loom analytics: {e}")

        return analytics

    async def delete_video(self, hosted_video_id: int, delete_from_provider: bool = True) -> bool:
        """
        Delete video.

        Args:
            hosted_video_id: Hosted video ID
            delete_from_provider: Also delete from hosting provider

        Returns:
            True if successful
        """
        result = await self.db.execute(
            select(HostedVideo).where(HostedVideo.id == hosted_video_id)
        )
        video = result.scalar_one_or_none()

        if not video:
            raise VideoHostManagerError(f"Video not found: {hosted_video_id}")

        # Delete from provider
        if delete_from_provider:
            if video.hosting_provider == "loom" and self.loom_client:
                await self.loom_client.delete_video(video.provider_video_id)
            elif video.hosting_provider == "s3" and self.s3_storage:
                await self.s3_storage.delete_video(video.s3_key)

        # Soft delete in database
        await self.db.execute(
            update(HostedVideo)
            .where(HostedVideo.id == hosted_video_id)
            .values(
                is_deleted=True,
                deleted_at=datetime.now(timezone.utc),
                is_active=False
            )
        )
        await self.db.commit()

        logger.info(f"Deleted video: {hosted_video_id}")
        return True

    def _select_host(self, preference: Optional[str], metadata: VideoMetadata) -> str:
        """
        Select hosting provider based on preference and requirements.

        Args:
            preference: User preference (loom, s3, auto, None)
            metadata: Video metadata

        Returns:
            Selected hosting provider
        """
        if preference and preference != "auto":
            return preference

        # Auto-selection logic
        if preference == "auto" or preference is None:
            # Use Loom for high-value leads (better analytics)
            # Use S3 for bulk distribution (lower cost)

            # For now, use default host
            return self.default_host

        return self.default_host

    def _calculate_s3_storage_cost(self, size_bytes: int) -> float:
        """Calculate monthly S3 storage cost."""
        size_gb = size_bytes / (1024 ** 3)
        return size_gb * self.s3_storage_cost_per_gb

    def _calculate_s3_bandwidth_cost(self, bandwidth_gb: float) -> float:
        """Calculate S3 bandwidth cost."""
        return bandwidth_gb * self.s3_transfer_cost_per_gb

    async def get_hosting_stats(self) -> Dict[str, Any]:
        """
        Get overall hosting statistics.

        Returns:
            Statistics dictionary
        """
        # Get video counts by provider
        result = await self.db.execute(
            select(HostedVideo).where(HostedVideo.is_deleted == False)
        )
        videos = result.scalars().all()

        loom_count = sum(1 for v in videos if v.hosting_provider == "loom")
        s3_count = sum(1 for v in videos if v.hosting_provider == "s3")

        total_cost = sum(float(v.total_cost_usd) for v in videos)
        total_views = sum(v.view_count for v in videos)
        total_storage_gb = sum(v.file_size_bytes or 0 for v in videos) / (1024 ** 3)

        return {
            'total_videos': len(videos),
            'by_provider': {
                'loom': loom_count,
                's3': s3_count
            },
            'total_views': total_views,
            'total_storage_gb': total_storage_gb,
            'total_cost_usd': total_cost,
            'cost_per_video': total_cost / len(videos) if videos else 0,
            'cost_per_view': total_cost / total_views if total_views > 0 else 0
        }
