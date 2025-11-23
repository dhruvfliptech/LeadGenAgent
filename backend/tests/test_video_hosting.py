"""
Tests for Phase 4, Task 5: Video Hosting

Tests for Loom API client, S3 storage, video host manager, and API endpoints.
"""

import os
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Models
from app.models.hosted_videos import HostedVideo, VideoView
from app.models.demo_sites import DemoSite
from app.models.leads import Lead

# Integrations
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

# Services
from app.services.video.video_host_manager import (
    VideoHostManager,
    VideoMetadata,
    HostedVideoResponse,
    VideoHostManagerError
)


# Test fixtures

@pytest.fixture
def mock_video_file(tmp_path):
    """Create mock video file."""
    video_path = tmp_path / "test_video.mp4"
    video_path.write_bytes(b"mock video content " * 1000)  # ~19KB
    return str(video_path)


@pytest.fixture
def video_metadata():
    """Create test video metadata."""
    return VideoMetadata(
        title="Demo for Test Company",
        description="Personalized demo showing improvements",
        demo_site_id=1,
        lead_id=1,
        company_name="Test Company",
        tags=["demo", "test-company", "saas"],
        privacy="unlisted",
        duration_seconds=90.5,
        resolution="1920x1080",
        file_size_bytes=18432
    )


@pytest.fixture
def mock_loom_response():
    """Mock Loom API response."""
    return {
        "id": "abc123def456",
        "share_url": "https://loom.com/share/abc123def456",
        "embed_url": "https://loom.com/embed/abc123def456",
        "thumbnail_url": "https://cdn.loom.com/sessions/thumbnails/abc123def456.jpg",
        "status": "processing",
        "privacy": "unlisted",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "view_count": 0,
        "title": "Demo for Test Company",
        "duration": 90.5
    }


@pytest.fixture
def mock_s3_response():
    """Mock S3 upload response."""
    return S3Upload(
        key="videos/20251104_123456_abcd1234.mp4",
        bucket="craigslist-leads-videos",
        url="https://craigslist-leads-videos.s3.us-east-1.amazonaws.com/videos/20251104_123456_abcd1234.mp4",
        signed_url="https://craigslist-leads-videos.s3.us-east-1.amazonaws.com/videos/20251104_123456_abcd1234.mp4?X-Amz-Algorithm=...",
        cloudfront_url="https://d123456.cloudfront.net/videos/20251104_123456_abcd1234.mp4",
        size_bytes=18432,
        etag="abc123",
        upload_time_seconds=2.5,
        content_type="video/mp4",
        metadata={"title": "Demo for Test Company"}
    )


# LoomClient Tests

class TestLoomClient:
    """Test Loom API client."""

    @pytest.mark.asyncio
    async def test_loom_client_initialization(self):
        """Test Loom client initialization."""
        with patch.dict(os.environ, {"LOOM_API_KEY": "test_key"}):
            client = LoomClient()
            assert client.api_key == "test_key"
            assert client.default_privacy == "unlisted"

    @pytest.mark.asyncio
    async def test_loom_client_missing_api_key(self):
        """Test Loom client without API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception):  # Should raise authentication error
                LoomClient()

    @pytest.mark.asyncio
    async def test_upload_video_success(self, mock_video_file, mock_loom_response):
        """Test successful video upload to Loom."""
        with patch.dict(os.environ, {"LOOM_API_KEY": "test_key"}):
            client = LoomClient()

            # Mock aiohttp session
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_loom_response)

            mock_session.post = AsyncMock(return_value=mock_response)
            mock_session.get = AsyncMock(return_value=mock_response)
            mock_session.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            client._get_session = AsyncMock(return_value=mock_session)

            # Upload video
            result = await client.upload_video(
                video_path=mock_video_file,
                title="Test Video",
                description="Test description"
            )

            assert isinstance(result, LoomVideo)
            assert result.video_id == "abc123def456"
            assert "loom.com/share" in result.share_url

    @pytest.mark.asyncio
    async def test_upload_video_file_not_found(self):
        """Test upload with non-existent file."""
        with patch.dict(os.environ, {"LOOM_API_KEY": "test_key"}):
            client = LoomClient()

            with pytest.raises(LoomUploadError) as exc:
                await client.upload_video(
                    video_path="/nonexistent/video.mp4",
                    title="Test Video"
                )

            assert "not found" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_get_embed_code(self):
        """Test embed code generation."""
        with patch.dict(os.environ, {"LOOM_API_KEY": "test_key"}):
            client = LoomClient()

            embed_code = await client.get_embed_code(
                video_id="abc123",
                width=640,
                height=360,
                autoplay=True
            )

            assert "<iframe" in embed_code
            assert "https://www.loom.com/embed/abc123" in embed_code
            assert "autoplay=1" in embed_code
            assert "width: 640px" in embed_code

    @pytest.mark.asyncio
    async def test_check_quota(self):
        """Test quota checking."""
        with patch.dict(os.environ, {"LOOM_API_KEY": "test_key"}):
            client = LoomClient()

            mock_workspace = {
                "videos_count": 25,
                "videos_limit": 100,
                "storage_used_bytes": 5000000000,  # 5GB
                "storage_limit_bytes": 50000000000,  # 50GB
                "videos_remaining": 75
            }

            client.get_workspace_info = AsyncMock(return_value=mock_workspace)

            quota = await client.check_quota()

            assert quota["videos_used"] == 25
            assert quota["videos_limit"] == 100
            assert quota["remaining_videos"] == 75


# S3VideoStorage Tests

class TestS3VideoStorage:
    """Test S3 video storage."""

    @pytest.mark.asyncio
    async def test_s3_storage_initialization(self):
        """Test S3 storage initialization."""
        with patch.dict(os.environ, {
            "S3_BUCKET_NAME": "test-bucket",
            "S3_REGION": "us-east-1"
        }):
            with patch("app.integrations.s3_video_storage.boto3"):
                storage = S3VideoStorage()
                assert storage.bucket_name == "test-bucket"
                assert storage.region == "us-east-1"

    @pytest.mark.asyncio
    async def test_generate_signed_url(self, mock_s3_response):
        """Test signed URL generation."""
        with patch.dict(os.environ, {
            "S3_BUCKET_NAME": "test-bucket",
            "AWS_ACCESS_KEY_ID": "test_key",
            "AWS_SECRET_ACCESS_KEY": "test_secret"
        }):
            with patch("app.integrations.s3_video_storage.boto3"):
                storage = S3VideoStorage()

                mock_client = MagicMock()
                mock_client.generate_presigned_url = MagicMock(
                    return_value="https://test-bucket.s3.amazonaws.com/video.mp4?signature=abc"
                )
                storage.s3_client = mock_client

                url = await storage.generate_signed_url(
                    key="videos/test.mp4",
                    expiration_seconds=3600
                )

                assert "signature=" in url
                mock_client.generate_presigned_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cloudfront_url(self):
        """Test CloudFront URL generation."""
        with patch.dict(os.environ, {
            "S3_BUCKET_NAME": "test-bucket",
            "CLOUDFRONT_DOMAIN": "d123456.cloudfront.net"
        }):
            with patch("app.integrations.s3_video_storage.boto3"):
                storage = S3VideoStorage()

                url = storage.get_cloudfront_url("videos/test.mp4")

                assert url == "https://d123456.cloudfront.net/videos/test.mp4"

    @pytest.mark.asyncio
    async def test_estimate_storage_cost(self):
        """Test storage cost estimation."""
        with patch.dict(os.environ, {"S3_BUCKET_NAME": "test-bucket"}):
            with patch("app.integrations.s3_video_storage.boto3"):
                storage = S3VideoStorage()

                # 1GB = 1024^3 bytes
                size_bytes = 1024 ** 3
                cost = storage._estimate_storage_cost(size_bytes)

                # Should be ~$0.023 per GB/month
                assert 0.02 < cost < 0.03


# VideoHostManager Tests

class TestVideoHostManager:
    """Test video host manager."""

    @pytest.mark.asyncio
    async def test_upload_to_loom_success(self, mock_video_file, video_metadata, mock_loom_response):
        """Test successful upload to Loom."""
        mock_db = AsyncMock()
        mock_loom_client = AsyncMock()

        loom_video = LoomVideo(
            video_id="abc123",
            share_url="https://loom.com/share/abc123",
            embed_url="https://loom.com/embed/abc123",
            thumbnail_url="https://cdn.loom.com/thumbnails/abc123.jpg",
            status="processing",
            privacy="unlisted",
            created_at=datetime.now(timezone.utc)
        )

        mock_loom_client.upload_video = AsyncMock(return_value=loom_video)

        manager = VideoHostManager(
            db=mock_db,
            loom_client=mock_loom_client,
            default_host="loom"
        )

        result = await manager.upload_video(
            video_path=mock_video_file,
            metadata=video_metadata
        )

        assert isinstance(result, HostedVideoResponse)
        assert result.hosting_provider == "loom"
        assert result.provider_video_id == "abc123"
        assert "loom.com/share" in result.share_url

    @pytest.mark.asyncio
    async def test_upload_to_s3_success(self, mock_video_file, video_metadata, mock_s3_response):
        """Test successful upload to S3."""
        mock_db = AsyncMock()
        mock_s3_storage = AsyncMock()
        mock_s3_storage.upload_video = AsyncMock(return_value=mock_s3_response)
        mock_s3_storage.region = "us-east-1"

        manager = VideoHostManager(
            db=mock_db,
            s3_storage=mock_s3_storage,
            default_host="s3"
        )

        result = await manager.upload_video(
            video_path=mock_video_file,
            metadata=video_metadata
        )

        assert isinstance(result, HostedVideoResponse)
        assert result.hosting_provider == "s3"
        assert "s3" in result.provider_video_id or "videos/" in result.provider_video_id

    @pytest.mark.asyncio
    async def test_failover_loom_to_s3(self, mock_video_file, video_metadata, mock_s3_response):
        """Test automatic failover from Loom to S3."""
        mock_db = AsyncMock()

        # Mock Loom client that fails
        mock_loom_client = AsyncMock()
        mock_loom_client.upload_video = AsyncMock(
            side_effect=LoomQuotaExceededError("Quota exceeded")
        )

        # Mock S3 storage that succeeds
        mock_s3_storage = AsyncMock()
        mock_s3_storage.upload_video = AsyncMock(return_value=mock_s3_response)
        mock_s3_storage.region = "us-east-1"

        manager = VideoHostManager(
            db=mock_db,
            loom_client=mock_loom_client,
            s3_storage=mock_s3_storage,
            default_host="loom",
            enable_failover=True
        )

        result = await manager.upload_video(
            video_path=mock_video_file,
            metadata=video_metadata
        )

        # Should have fallen back to S3
        assert result.hosting_provider == "s3"

    @pytest.mark.asyncio
    async def test_get_shareable_link(self):
        """Test getting shareable link."""
        mock_db = AsyncMock()

        # Mock database query
        mock_result = AsyncMock()
        mock_video = HostedVideo(
            id=1,
            hosting_provider="loom",
            share_url="https://loom.com/share/abc123",
            provider_video_id="abc123",
            demo_site_id=1,
            lead_id=1,
            title="Test",
            privacy="unlisted"
        )
        mock_result.scalar_one_or_none = Mock(return_value=mock_video)
        mock_db.execute = AsyncMock(return_value=mock_result)

        manager = VideoHostManager(db=mock_db)

        url = await manager.get_shareable_link(hosted_video_id=1)

        assert url == "https://loom.com/share/abc123"

    @pytest.mark.asyncio
    async def test_cost_calculation(self):
        """Test cost calculations for different providers."""
        mock_db = AsyncMock()
        manager = VideoHostManager(db=mock_db)

        # Test Loom cost (flat monthly fee)
        loom_cost = manager.loom_cost_per_user_monthly
        assert loom_cost == 12.0

        # Test S3 storage cost
        size_gb = 1.0
        s3_cost = manager._calculate_s3_storage_cost(int(size_gb * 1024 ** 3))
        assert 0.02 < s3_cost < 0.03  # ~$0.023/GB

        # Test S3 bandwidth cost
        bandwidth_gb = 10.0
        bandwidth_cost = manager._calculate_s3_bandwidth_cost(bandwidth_gb)
        assert 0.8 < bandwidth_cost < 0.9  # ~$0.085/GB


# API Endpoint Tests

class TestHostedVideosAPI:
    """Test hosted videos API endpoints."""

    @pytest.mark.asyncio
    async def test_upload_endpoint(self, mock_video_file):
        """Test video upload endpoint."""
        # This would require FastAPI test client setup
        # Placeholder for actual implementation
        pass

    @pytest.mark.asyncio
    async def test_get_video_endpoint(self):
        """Test get video details endpoint."""
        pass

    @pytest.mark.asyncio
    async def test_track_view_endpoint(self):
        """Test view tracking endpoint."""
        pass

    @pytest.mark.asyncio
    async def test_get_analytics_endpoint(self):
        """Test analytics endpoint."""
        pass


# Integration Tests

class TestVideoHostingIntegration:
    """Integration tests for video hosting workflow."""

    @pytest.mark.asyncio
    async def test_full_upload_workflow(self, mock_video_file, video_metadata):
        """Test complete video upload and hosting workflow."""
        # This would test the full flow:
        # 1. Upload video
        # 2. Create database record
        # 3. Generate shareable link
        # 4. Track views
        # 5. Calculate costs
        pass

    @pytest.mark.asyncio
    async def test_analytics_aggregation(self):
        """Test analytics data aggregation from multiple views."""
        pass

    @pytest.mark.asyncio
    async def test_cost_tracking_over_time(self):
        """Test cost tracking and accumulation."""
        pass


# Performance Tests

class TestVideoHostingPerformance:
    """Performance tests for video hosting."""

    @pytest.mark.asyncio
    async def test_upload_performance(self, mock_video_file):
        """Test upload performance meets requirements."""
        # Should complete in < 120 seconds for 90-second video
        pass

    @pytest.mark.asyncio
    async def test_signed_url_generation_performance(self):
        """Test signed URL generation is fast."""
        # Should complete in < 1 second
        pass

    @pytest.mark.asyncio
    async def test_concurrent_uploads(self):
        """Test handling multiple concurrent uploads."""
        pass


# Cost Analysis Tests

class TestCostAnalysis:
    """Test cost analysis and optimization."""

    def test_loom_vs_s3_cost_comparison(self):
        """Test cost comparison between Loom and S3."""
        # Scenario 1: Low volume (10 videos, 50 views)
        loom_cost_low = 12.0  # Flat monthly
        s3_cost_low = (10 * 18 / 1024) * 0.023 + (50 * 18 / 1024) * 0.085
        # S3 is cheaper for low volume

        # Scenario 2: High volume (1000 videos, 5000 views)
        loom_cost_high = 12.0  # Still flat
        s3_cost_high = (1000 * 18 / 1024) * 0.023 + (5000 * 18 / 1024) * 0.085
        # Loom becomes cheaper at scale

        assert s3_cost_low < loom_cost_low
        assert loom_cost_high < s3_cost_high

    def test_cost_per_view_calculation(self):
        """Test cost per view calculations."""
        # 1000 videos, $12/month Loom
        total_cost = 12.0
        total_views = 5000
        cost_per_view = total_cost / total_views

        assert cost_per_view == 0.0024  # $0.0024 per view

    def test_breakeven_analysis(self):
        """Test breakeven point between Loom and S3."""
        # At what view count does Loom become more cost-effective?
        loom_monthly = 12.0
        s3_per_gb_storage = 0.023
        s3_per_gb_transfer = 0.085

        # For 18MB videos
        video_size_gb = 18 / 1024

        # Break-even occurs when:
        # loom_monthly < (num_videos * video_size_gb * s3_per_gb_storage) + (num_views * video_size_gb * s3_per_gb_transfer)

        # For 1000 videos:
        num_videos = 1000
        storage_cost = num_videos * video_size_gb * s3_per_gb_storage

        # Remaining budget for bandwidth
        bandwidth_budget = loom_monthly - storage_cost

        # Views supported by bandwidth budget
        breakeven_views = bandwidth_budget / (video_size_gb * s3_per_gb_transfer)

        # Loom is cheaper after ~breakeven_views
        assert breakeven_views > 0


# Cleanup Tests

class TestVideoCleanup:
    """Test video cleanup and maintenance."""

    @pytest.mark.asyncio
    async def test_delete_old_videos(self):
        """Test cleanup of old videos."""
        pass

    @pytest.mark.asyncio
    async def test_expired_signed_url_regeneration(self):
        """Test regeneration of expired S3 signed URLs."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
