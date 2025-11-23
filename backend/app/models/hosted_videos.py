"""
HostedVideo and VideoView models for Phase 4 Video Hosting.

Tracks videos uploaded to Loom or S3, with analytics and cost tracking.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base
import enum


class HostingProvider(str, enum.Enum):
    """Video hosting provider options."""
    LOOM = "loom"
    S3 = "s3"
    YOUTUBE = "youtube"
    VIMEO = "vimeo"


class VideoStatus(str, enum.Enum):
    """Video hosting status."""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class VideoPrivacy(str, enum.Enum):
    """Video privacy settings."""
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"


class HostedVideo(Base):
    """
    HostedVideo model for tracking videos uploaded to Loom or S3.

    Stores video hosting metadata, URLs, analytics, and cost tracking
    for videos created during the demo automation workflow.
    """

    __tablename__ = "hosted_videos"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys - track relationship to composed video and demo site
    composed_video_id = Column(Integer, nullable=True, index=True)  # FK to composed_videos (when implemented)
    demo_site_id = Column(Integer, ForeignKey("demo_sites.id"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)

    # Relationships
    demo_site = relationship("DemoSite", backref="hosted_videos")
    lead = relationship("Lead", backref="hosted_videos")

    # Hosting details
    hosting_provider = Column(String(50), nullable=False, index=True)  # loom, s3, youtube, vimeo
    provider_video_id = Column(String(255), nullable=False, unique=True, index=True)  # Provider's video ID

    # URLs
    share_url = Column(Text, nullable=False)  # Shareable URL (e.g., https://loom.com/share/abc123)
    embed_url = Column(Text, nullable=False)  # Embed URL (e.g., https://loom.com/embed/abc123)
    thumbnail_url = Column(Text, nullable=True)  # Thumbnail image URL
    download_url = Column(Text, nullable=True)  # Direct download URL (S3 signed URL)

    # Metadata
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    company_name = Column(String(255), nullable=True, index=True)  # Extracted from lead
    tags = Column(JSON, nullable=True)  # ["demo", "company-name", "industry"]

    # Video properties
    privacy = Column(String(20), nullable=False, default="unlisted", index=True)
    duration_seconds = Column(Float, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    file_path = Column(Text, nullable=True)  # Local path (if still stored)
    format = Column(String(20), nullable=True)  # mp4, webm, mov
    resolution = Column(String(20), nullable=True)  # 1920x1080, 1280x720
    fps = Column(Integer, nullable=True)  # Frames per second
    bitrate_kbps = Column(Integer, nullable=True)
    codec = Column(String(50), nullable=True)  # h264, vp9

    # Status tracking
    status = Column(String(50), nullable=False, default="uploading", index=True)
    upload_started_at = Column(DateTime(timezone=True), nullable=True)
    upload_completed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    upload_time_seconds = Column(Float, nullable=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_time_seconds = Column(Float, nullable=True)

    # Error handling
    upload_attempts = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    retry_after = Column(DateTime(timezone=True), nullable=True)

    # Analytics - view tracking
    view_count = Column(Integer, default=0, nullable=False, index=True)
    unique_viewers = Column(Integer, default=0, nullable=False)
    last_viewed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    avg_watch_percentage = Column(Float, nullable=True)  # 0.0 - 100.0
    avg_watch_duration_seconds = Column(Float, nullable=True)
    total_watch_time_seconds = Column(Float, default=0.0, nullable=False)
    completion_rate = Column(Float, nullable=True)  # Percentage who watched to end

    # Analytics - engagement
    likes_count = Column(Integer, default=0, nullable=False)
    comments_count = Column(Integer, default=0, nullable=False)
    shares_count = Column(Integer, default=0, nullable=False)
    click_through_rate = Column(Float, nullable=True)  # CTA clicks / views

    # Provider-specific analytics (JSON)
    loom_analytics = Column(JSON, nullable=True)  # Detailed Loom analytics
    provider_analytics = Column(JSON, nullable=True)  # Generic provider analytics

    # Cost tracking
    hosting_cost_monthly = Column(Numeric(10, 4), default=0.0, nullable=False)
    storage_cost_monthly = Column(Numeric(10, 4), default=0.0, nullable=False)
    bandwidth_cost_monthly = Column(Numeric(10, 4), default=0.0, nullable=False)
    bandwidth_used_gb = Column(Numeric(10, 2), default=0.0, nullable=False)
    total_cost_usd = Column(Numeric(10, 4), default=0.0, nullable=False, index=True)
    cost_per_view = Column(Numeric(10, 4), nullable=True)  # total_cost / view_count

    # S3-specific fields
    s3_bucket = Column(String(255), nullable=True)
    s3_key = Column(String(500), nullable=True)
    s3_region = Column(String(50), nullable=True)
    cloudfront_distribution_id = Column(String(255), nullable=True)
    cloudfront_url = Column(Text, nullable=True)
    signed_url_expiration = Column(DateTime(timezone=True), nullable=True)

    # Loom-specific fields
    loom_folder_id = Column(String(255), nullable=True)
    loom_workspace_id = Column(String(255), nullable=True)
    loom_video_password = Column(String(255), nullable=True)  # For password-protected videos

    # Delivery optimization
    cdn_enabled = Column(Boolean, default=False, nullable=False)
    cdn_provider = Column(String(50), nullable=True)  # cloudfront, fastly, cloudflare
    edge_locations = Column(JSON, nullable=True)  # List of CDN edge locations

    # Transcoding (if done)
    transcoded = Column(Boolean, default=False, nullable=False)
    transcoding_profile = Column(String(50), nullable=True)  # 720p, 1080p, adaptive
    transcoding_cost = Column(Numeric(10, 4), nullable=True)

    # Metadata and configuration
    video_metadata = Column(JSON, nullable=True)  # Additional flexible metadata
    upload_metadata = Column(JSON, nullable=True)  # Upload configuration used

    # Flags
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    analytics_enabled = Column(Boolean, default=True, nullable=False)
    download_enabled = Column(Boolean, default=False, nullable=False)
    comments_enabled = Column(Boolean, default=False, nullable=False)
    embed_enabled = Column(Boolean, default=True, nullable=False)

    # Expiration (for temporary videos)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    auto_delete_after_days = Column(Integer, nullable=True)  # Auto-delete after N days

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    def __repr__(self):
        return f"<HostedVideo(id={self.id}, provider='{self.hosting_provider}', title='{self.title}', status='{self.status}')>"

    def to_dict(self):
        """Convert hosted video to dictionary for API responses."""
        return {
            'id': self.id,
            'composed_video_id': self.composed_video_id,
            'demo_site_id': self.demo_site_id,
            'lead_id': self.lead_id,
            'hosting': {
                'provider': self.hosting_provider,
                'provider_video_id': self.provider_video_id,
                'status': self.status
            },
            'urls': {
                'share_url': self.share_url,
                'embed_url': self.embed_url,
                'thumbnail_url': self.thumbnail_url,
                'download_url': self.download_url if self.download_enabled else None
            },
            'metadata': {
                'title': self.title,
                'description': self.description,
                'company_name': self.company_name,
                'tags': self.tags or [],
                'privacy': self.privacy
            },
            'video_properties': {
                'duration_seconds': self.duration_seconds,
                'file_size_bytes': self.file_size_bytes,
                'format': self.format,
                'resolution': self.resolution,
                'fps': self.fps,
                'bitrate_kbps': self.bitrate_kbps,
                'codec': self.codec
            },
            'timing': {
                'upload_time_seconds': self.upload_time_seconds,
                'processing_time_seconds': self.processing_time_seconds,
                'total_time_seconds': (self.upload_time_seconds or 0) + (self.processing_time_seconds or 0)
            },
            'analytics': {
                'view_count': self.view_count,
                'unique_viewers': self.unique_viewers,
                'last_viewed_at': self.last_viewed_at.isoformat() if self.last_viewed_at else None,
                'avg_watch_percentage': self.avg_watch_percentage,
                'avg_watch_duration_seconds': self.avg_watch_duration_seconds,
                'total_watch_time_seconds': self.total_watch_time_seconds,
                'completion_rate': self.completion_rate,
                'engagement': {
                    'likes': self.likes_count,
                    'comments': self.comments_count,
                    'shares': self.shares_count,
                    'click_through_rate': self.click_through_rate
                }
            },
            'cost': {
                'hosting_monthly': float(self.hosting_cost_monthly),
                'storage_monthly': float(self.storage_cost_monthly),
                'bandwidth_monthly': float(self.bandwidth_cost_monthly),
                'bandwidth_gb': float(self.bandwidth_used_gb),
                'total_usd': float(self.total_cost_usd),
                'cost_per_view': float(self.cost_per_view) if self.cost_per_view else None
            },
            'flags': {
                'is_active': self.is_active,
                'is_deleted': self.is_deleted,
                'analytics_enabled': self.analytics_enabled,
                'download_enabled': self.download_enabled,
                'comments_enabled': self.comments_enabled,
                'embed_enabled': self.embed_enabled,
                'cdn_enabled': self.cdn_enabled,
                'transcoded': self.transcoded
            },
            'timestamps': {
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'upload_completed_at': self.upload_completed_at.isoformat() if self.upload_completed_at else None,
                'expires_at': self.expires_at.isoformat() if self.expires_at else None,
                'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
            },
            'error': self.error_message if self.status == 'failed' else None
        }


class VideoView(Base):
    """
    VideoView model for tracking individual video views and engagement.

    Records detailed analytics for each video view, including watch time,
    completion, viewer information, and engagement metrics.
    """

    __tablename__ = "video_views"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    hosted_video_id = Column(Integer, ForeignKey("hosted_videos.id"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)  # If known

    # Relationships
    hosted_video = relationship("HostedVideo", backref="views")
    lead = relationship("Lead", backref="video_views")

    # Viewer information
    viewer_ip = Column(String(45), nullable=True, index=True)  # IPv4 or IPv6
    viewer_user_agent = Column(Text, nullable=True)
    viewer_location = Column(String(255), nullable=True)  # City, State, Country
    viewer_country = Column(String(2), nullable=True, index=True)  # ISO country code
    viewer_city = Column(String(100), nullable=True)
    viewer_region = Column(String(100), nullable=True)

    # Device information
    viewer_device = Column(String(50), nullable=True, index=True)  # desktop, mobile, tablet
    viewer_os = Column(String(50), nullable=True)  # Windows, macOS, iOS, Android
    viewer_browser = Column(String(50), nullable=True)  # Chrome, Safari, Firefox
    screen_resolution = Column(String(20), nullable=True)  # 1920x1080

    # Watch metrics
    watch_duration_seconds = Column(Float, nullable=False, default=0.0)
    watch_percentage = Column(Float, nullable=False, default=0.0)  # 0.0 - 100.0
    completed = Column(Boolean, default=False, nullable=False, index=True)

    # Engagement timeline
    play_count = Column(Integer, default=1, nullable=False)  # Times play button pressed
    pause_count = Column(Integer, default=0, nullable=False)
    seek_count = Column(Integer, default=0, nullable=False)
    replay_count = Column(Integer, default=0, nullable=False)

    # Quality of experience
    playback_quality = Column(String(20), nullable=True)  # 1080p, 720p, 480p, auto
    buffering_events = Column(Integer, default=0, nullable=False)
    total_buffering_seconds = Column(Float, default=0.0, nullable=False)
    average_bitrate = Column(Integer, nullable=True)
    dropped_frames = Column(Integer, default=0, nullable=False)

    # Interaction tracking
    clicked_cta = Column(Boolean, default=False, nullable=False)  # Clicked call-to-action
    cta_clicked_at = Column(DateTime(timezone=True), nullable=True)
    cta_type = Column(String(50), nullable=True)  # button, link, overlay

    # Engagement actions
    liked = Column(Boolean, default=False, nullable=False)
    commented = Column(Boolean, default=False, nullable=False)
    shared = Column(Boolean, default=False, nullable=False)
    downloaded = Column(Boolean, default=False, nullable=False)

    # Session tracking
    session_id = Column(String(255), nullable=True, index=True)  # Unique session identifier
    session_duration_seconds = Column(Float, nullable=True)  # Total session time
    is_first_view = Column(Boolean, default=True, nullable=False)  # First view by this viewer
    previous_view_id = Column(Integer, ForeignKey("video_views.id"), nullable=True)

    # Referral tracking
    referrer_url = Column(Text, nullable=True)  # Where viewer came from
    referrer_domain = Column(String(255), nullable=True, index=True)
    utm_source = Column(String(100), nullable=True, index=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    utm_content = Column(String(100), nullable=True)

    # Watch progress tracking (JSON array of timestamps)
    watch_progress = Column(JSON, nullable=True)  # [{"timestamp": 10.5, "action": "pause"}, ...]
    engagement_points = Column(JSON, nullable=True)  # Timestamps of high engagement

    # Provider-specific data
    provider_view_id = Column(String(255), nullable=True, unique=True)  # Loom's view ID
    provider_analytics = Column(JSON, nullable=True)  # Additional provider data

    # Timestamps
    viewed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    view_started_at = Column(DateTime(timezone=True), nullable=True)
    view_ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Flags
    is_bot = Column(Boolean, default=False, nullable=False, index=True)  # Detected as bot
    is_suspicious = Column(Boolean, default=False, nullable=False)  # Suspicious activity

    def __repr__(self):
        return f"<VideoView(id={self.id}, hosted_video_id={self.hosted_video_id}, watch_percentage={self.watch_percentage:.1f}%)>"

    def to_dict(self):
        """Convert video view to dictionary for API responses."""
        return {
            'id': self.id,
            'hosted_video_id': self.hosted_video_id,
            'lead_id': self.lead_id,
            'viewer': {
                'ip': self.viewer_ip,
                'location': self.viewer_location,
                'country': self.viewer_country,
                'city': self.viewer_city,
                'device': self.viewer_device,
                'os': self.viewer_os,
                'browser': self.viewer_browser,
                'screen_resolution': self.screen_resolution
            },
            'watch_metrics': {
                'duration_seconds': self.watch_duration_seconds,
                'percentage': self.watch_percentage,
                'completed': self.completed,
                'play_count': self.play_count,
                'pause_count': self.pause_count,
                'seek_count': self.seek_count,
                'replay_count': self.replay_count
            },
            'quality': {
                'playback_quality': self.playback_quality,
                'buffering_events': self.buffering_events,
                'total_buffering_seconds': self.total_buffering_seconds,
                'average_bitrate': self.average_bitrate,
                'dropped_frames': self.dropped_frames
            },
            'engagement': {
                'clicked_cta': self.clicked_cta,
                'cta_clicked_at': self.cta_clicked_at.isoformat() if self.cta_clicked_at else None,
                'liked': self.liked,
                'commented': self.commented,
                'shared': self.shared,
                'downloaded': self.downloaded
            },
            'session': {
                'session_id': self.session_id,
                'session_duration_seconds': self.session_duration_seconds,
                'is_first_view': self.is_first_view
            },
            'referral': {
                'referrer_url': self.referrer_url,
                'referrer_domain': self.referrer_domain,
                'utm_source': self.utm_source,
                'utm_medium': self.utm_medium,
                'utm_campaign': self.utm_campaign
            },
            'timestamps': {
                'viewed_at': self.viewed_at.isoformat() if self.viewed_at else None,
                'view_started_at': self.view_started_at.isoformat() if self.view_started_at else None,
                'view_ended_at': self.view_ended_at.isoformat() if self.view_ended_at else None
            },
            'flags': {
                'is_bot': self.is_bot,
                'is_suspicious': self.is_suspicious
            }
        }
