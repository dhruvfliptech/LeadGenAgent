"""
Loom API Client for Phase 4 Video Hosting.

Provides integration with Loom's API for video uploads, management, and analytics.
"""

import os
import logging
import aiohttp
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LoomVideo(BaseModel):
    """Loom video response model."""
    video_id: str
    share_url: str
    embed_url: str
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    status: str = "processing"  # processing, ready, failed
    privacy: str = "unlisted"
    created_at: datetime
    view_count: int = 0
    title: Optional[str] = None
    description: Optional[str] = None
    folder_id: Optional[str] = None
    workspace_id: Optional[str] = None

    # Additional metadata
    resolution: Optional[str] = None
    file_size_bytes: Optional[int] = None
    transcoding_status: Optional[str] = None


class LoomAnalytics(BaseModel):
    """Loom video analytics model."""
    video_id: str
    total_views: int
    unique_viewers: int
    avg_watch_percentage: float
    total_watch_time_seconds: float
    completion_rate: float
    engagement_score: Optional[float] = None
    top_referrers: List[Dict[str, Any]] = []
    viewer_locations: List[Dict[str, Any]] = []
    daily_views: List[Dict[str, Any]] = []


class LoomClientError(Exception):
    """Base exception for Loom client errors."""
    pass


class LoomAuthenticationError(LoomClientError):
    """Raised when authentication fails."""
    pass


class LoomQuotaExceededError(LoomClientError):
    """Raised when API quota is exceeded."""
    pass


class LoomUploadError(LoomClientError):
    """Raised when video upload fails."""
    pass


class LoomClient:
    """
    Loom API Client for video hosting and management.

    Features:
    - Upload videos to Loom
    - Generate shareable links
    - Track video analytics
    - Manage video privacy settings
    - Organize videos in folders
    """

    BASE_URL = "https://www.loom.com/api/v1"
    UPLOAD_URL = "https://www.loom.com/api/v1/videos"

    def __init__(
        self,
        api_key: Optional[str] = None,
        workspace_id: Optional[str] = None,
        default_privacy: str = "unlisted",
        default_folder_id: Optional[str] = None,
        timeout_seconds: int = 300
    ):
        """
        Initialize Loom client.

        Args:
            api_key: Loom API key (defaults to LOOM_API_KEY env var)
            workspace_id: Loom workspace ID (optional)
            default_privacy: Default privacy setting for uploads
            default_folder_id: Default folder for organizing videos
            timeout_seconds: Timeout for API requests
        """
        self.api_key = api_key or os.getenv("LOOM_API_KEY")
        if not self.api_key:
            raise LoomAuthenticationError("LOOM_API_KEY environment variable not set")

        self.workspace_id = workspace_id or os.getenv("LOOM_WORKSPACE_ID")
        self.default_privacy = default_privacy
        self.default_folder_id = default_folder_id or os.getenv("LOOM_FOLDER_ID")
        self.timeout_seconds = timeout_seconds

        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout_seconds)
            )
        return self.session

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def upload_video(
        self,
        video_path: str,
        title: str,
        description: Optional[str] = None,
        privacy: Optional[str] = None,
        folder_id: Optional[str] = None,
        password: Optional[str] = None,
        notify_collaborators: bool = False
    ) -> LoomVideo:
        """
        Upload video to Loom.

        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            privacy: Privacy setting (public, unlisted, private)
            folder_id: Folder to organize video
            password: Password for password-protected videos
            notify_collaborators: Send notification to workspace collaborators

        Returns:
            LoomVideo object with upload details

        Raises:
            LoomUploadError: If upload fails
            LoomQuotaExceededError: If quota exceeded
        """
        if not os.path.exists(video_path):
            raise LoomUploadError(f"Video file not found: {video_path}")

        file_size = os.path.getsize(video_path)
        logger.info(f"Uploading video to Loom: {title} ({file_size / 1024 / 1024:.2f} MB)")

        try:
            # Step 1: Create video record
            session = await self._get_session()

            video_data = {
                "title": title,
                "privacy": privacy or self.default_privacy or "unlisted",
                "notify_collaborators": notify_collaborators
            }

            if description:
                video_data["description"] = description

            if folder_id or self.default_folder_id:
                video_data["folder_id"] = folder_id or self.default_folder_id

            if password and (privacy or self.default_privacy) == "private":
                video_data["password"] = password

            if self.workspace_id:
                video_data["workspace_id"] = self.workspace_id

            # Create video record
            async with session.post(f"{self.BASE_URL}/videos", json=video_data) as response:
                if response.status == 401:
                    raise LoomAuthenticationError("Invalid API key")
                elif response.status == 429:
                    raise LoomQuotaExceededError("Loom API quota exceeded")
                elif response.status == 413:
                    raise LoomUploadError("Video file too large")
                elif response.status >= 400:
                    error_text = await response.text()
                    raise LoomUploadError(f"Failed to create video record: {response.status} - {error_text}")

                video_record = await response.json()
                video_id = video_record.get("id")
                upload_url = video_record.get("upload_url")

            if not video_id or not upload_url:
                raise LoomUploadError("Invalid response from Loom API")

            logger.info(f"Created Loom video record: {video_id}")

            # Step 2: Upload video file
            upload_start = datetime.now(timezone.utc)

            with open(video_path, "rb") as video_file:
                # Create form data for multipart upload
                form_data = aiohttp.FormData()
                form_data.add_field(
                    "file",
                    video_file,
                    filename=os.path.basename(video_path),
                    content_type="video/mp4"
                )

                # Upload with separate timeout for large files
                upload_timeout = aiohttp.ClientTimeout(total=self.timeout_seconds * 2)
                async with session.post(
                    upload_url,
                    data=form_data,
                    timeout=upload_timeout
                ) as upload_response:
                    if upload_response.status >= 400:
                        error_text = await upload_response.text()
                        raise LoomUploadError(f"Upload failed: {upload_response.status} - {error_text}")

            upload_duration = (datetime.now(timezone.utc) - upload_start).total_seconds()
            logger.info(f"Video uploaded successfully in {upload_duration:.2f}s")

            # Step 3: Get video details
            video = await self.get_video_details(video_id)

            return video

        except aiohttp.ClientError as e:
            logger.error(f"Network error during upload: {e}")
            raise LoomUploadError(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            raise LoomUploadError(f"Upload failed: {e}")

    async def get_video_details(self, video_id: str) -> LoomVideo:
        """
        Get video details from Loom.

        Args:
            video_id: Loom video ID

        Returns:
            LoomVideo object with video details
        """
        session = await self._get_session()

        async with session.get(f"{self.BASE_URL}/videos/{video_id}") as response:
            if response.status == 404:
                raise LoomClientError(f"Video not found: {video_id}")
            elif response.status >= 400:
                error_text = await response.text()
                raise LoomClientError(f"Failed to get video details: {error_text}")

            data = await response.json()

        return self._parse_video_response(data)

    async def update_video(
        self,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        privacy: Optional[str] = None,
        folder_id: Optional[str] = None,
        password: Optional[str] = None
    ) -> bool:
        """
        Update video metadata.

        Args:
            video_id: Loom video ID
            title: New title
            description: New description
            privacy: New privacy setting
            folder_id: Move to folder
            password: Set password

        Returns:
            True if successful
        """
        session = await self._get_session()

        update_data = {}
        if title is not None:
            update_data["title"] = title
        if description is not None:
            update_data["description"] = description
        if privacy is not None:
            update_data["privacy"] = privacy
        if folder_id is not None:
            update_data["folder_id"] = folder_id
        if password is not None:
            update_data["password"] = password

        if not update_data:
            return True  # Nothing to update

        async with session.patch(
            f"{self.BASE_URL}/videos/{video_id}",
            json=update_data
        ) as response:
            if response.status >= 400:
                error_text = await response.text()
                logger.error(f"Failed to update video: {error_text}")
                return False

        logger.info(f"Updated video {video_id}")
        return True

    async def delete_video(self, video_id: str) -> bool:
        """
        Delete video from Loom.

        Args:
            video_id: Loom video ID

        Returns:
            True if successful
        """
        session = await self._get_session()

        async with session.delete(f"{self.BASE_URL}/videos/{video_id}") as response:
            if response.status in [200, 204]:
                logger.info(f"Deleted video {video_id}")
                return True
            elif response.status == 404:
                logger.warning(f"Video not found: {video_id}")
                return False
            else:
                error_text = await response.text()
                logger.error(f"Failed to delete video: {error_text}")
                return False

    async def get_video_analytics(self, video_id: str) -> LoomAnalytics:
        """
        Get video analytics from Loom.

        Args:
            video_id: Loom video ID

        Returns:
            LoomAnalytics object with engagement metrics
        """
        session = await self._get_session()

        async with session.get(f"{self.BASE_URL}/videos/{video_id}/analytics") as response:
            if response.status >= 400:
                error_text = await response.text()
                raise LoomClientError(f"Failed to get analytics: {error_text}")

            data = await response.json()

        return self._parse_analytics_response(video_id, data)

    async def list_videos(
        self,
        folder_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List videos in workspace.

        Args:
            folder_id: Filter by folder
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of video dictionaries
        """
        session = await self._get_session()

        params = {
            "limit": limit,
            "offset": offset
        }

        if folder_id:
            params["folder_id"] = folder_id

        if self.workspace_id:
            params["workspace_id"] = self.workspace_id

        async with session.get(f"{self.BASE_URL}/videos", params=params) as response:
            if response.status >= 400:
                error_text = await response.text()
                raise LoomClientError(f"Failed to list videos: {error_text}")

            data = await response.json()

        return data.get("videos", [])

    async def create_folder(self, name: str) -> str:
        """
        Create folder for organizing videos.

        Args:
            name: Folder name

        Returns:
            Folder ID
        """
        session = await self._get_session()

        folder_data = {"name": name}
        if self.workspace_id:
            folder_data["workspace_id"] = self.workspace_id

        async with session.post(f"{self.BASE_URL}/folders", json=folder_data) as response:
            if response.status >= 400:
                error_text = await response.text()
                raise LoomClientError(f"Failed to create folder: {error_text}")

            data = await response.json()

        folder_id = data.get("id")
        logger.info(f"Created folder '{name}': {folder_id}")
        return folder_id

    async def get_embed_code(
        self,
        video_id: str,
        width: int = 640,
        height: int = 360,
        autoplay: bool = False,
        hide_owner: bool = False,
        hide_share: bool = False
    ) -> str:
        """
        Generate embed code for video.

        Args:
            video_id: Loom video ID
            width: Embed width
            height: Embed height
            autoplay: Auto-play video
            hide_owner: Hide owner information
            hide_share: Hide share button

        Returns:
            HTML embed code
        """
        embed_url = f"https://www.loom.com/embed/{video_id}"

        params = []
        if autoplay:
            params.append("autoplay=1")
        if hide_owner:
            params.append("hide_owner=true")
        if hide_share:
            params.append("hide_share=true")

        if params:
            embed_url += "?" + "&".join(params)

        embed_code = f'''<iframe
    src="{embed_url}"
    frameborder="0"
    webkitallowfullscreen
    mozallowfullscreen
    allowfullscreen
    style="width: {width}px; height: {height}px;">
</iframe>'''

        return embed_code

    async def get_workspace_info(self) -> Dict[str, Any]:
        """
        Get workspace information and quotas.

        Returns:
            Workspace details including usage and limits
        """
        session = await self._get_session()

        workspace_id = self.workspace_id or "default"

        async with session.get(f"{self.BASE_URL}/workspaces/{workspace_id}") as response:
            if response.status >= 400:
                error_text = await response.text()
                raise LoomClientError(f"Failed to get workspace info: {error_text}")

            data = await response.json()

        return data

    async def check_quota(self) -> Dict[str, Any]:
        """
        Check current API quota and usage.

        Returns:
            Dictionary with quota information
        """
        try:
            workspace_info = await self.get_workspace_info()

            return {
                "videos_used": workspace_info.get("videos_count", 0),
                "videos_limit": workspace_info.get("videos_limit", -1),  # -1 = unlimited
                "storage_used_gb": workspace_info.get("storage_used_bytes", 0) / (1024**3),
                "storage_limit_gb": workspace_info.get("storage_limit_bytes", 0) / (1024**3),
                "remaining_videos": workspace_info.get("videos_remaining", -1)
            }
        except Exception as e:
            logger.warning(f"Failed to check quota: {e}")
            return {
                "videos_used": 0,
                "videos_limit": -1,
                "storage_used_gb": 0.0,
                "storage_limit_gb": 0.0,
                "remaining_videos": -1
            }

    def _parse_video_response(self, data: Dict[str, Any]) -> LoomVideo:
        """Parse Loom API video response."""
        video_id = data.get("id", "")

        return LoomVideo(
            video_id=video_id,
            share_url=data.get("share_url", f"https://www.loom.com/share/{video_id}"),
            embed_url=data.get("embed_url", f"https://www.loom.com/embed/{video_id}"),
            thumbnail_url=data.get("thumbnail_url"),
            duration_seconds=data.get("duration"),
            status=data.get("status", "processing"),
            privacy=data.get("privacy", "unlisted"),
            created_at=self._parse_datetime(data.get("created_at")),
            view_count=data.get("view_count", 0),
            title=data.get("title"),
            description=data.get("description"),
            folder_id=data.get("folder_id"),
            workspace_id=data.get("workspace_id"),
            resolution=data.get("resolution"),
            file_size_bytes=data.get("file_size"),
            transcoding_status=data.get("transcoding_status")
        )

    def _parse_analytics_response(self, video_id: str, data: Dict[str, Any]) -> LoomAnalytics:
        """Parse Loom API analytics response."""
        return LoomAnalytics(
            video_id=video_id,
            total_views=data.get("total_views", 0),
            unique_viewers=data.get("unique_viewers", 0),
            avg_watch_percentage=data.get("avg_watch_percentage", 0.0),
            total_watch_time_seconds=data.get("total_watch_time", 0.0),
            completion_rate=data.get("completion_rate", 0.0),
            engagement_score=data.get("engagement_score"),
            top_referrers=data.get("top_referrers", []),
            viewer_locations=data.get("viewer_locations", []),
            daily_views=data.get("daily_views", [])
        )

    def _parse_datetime(self, dt_string: Optional[str]) -> datetime:
        """Parse datetime string from Loom API."""
        if not dt_string:
            return datetime.now(timezone.utc)

        try:
            # Try ISO format first
            return datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
        except:
            # Fallback to current time
            return datetime.now(timezone.utc)


# Convenience function for quick uploads
async def upload_to_loom(
    video_path: str,
    title: str,
    description: Optional[str] = None,
    privacy: str = "unlisted"
) -> LoomVideo:
    """
    Quick function to upload video to Loom.

    Args:
        video_path: Path to video file
        title: Video title
        description: Video description
        privacy: Privacy setting

    Returns:
        LoomVideo object
    """
    async with LoomClient() as client:
        return await client.upload_video(
            video_path=video_path,
            title=title,
            description=description,
            privacy=privacy
        )
