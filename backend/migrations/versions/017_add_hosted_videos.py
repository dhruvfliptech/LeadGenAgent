"""Add hosted_videos and video_views tables for Phase 4 video hosting

Revision ID: 017_add_hosted_videos
Revises: 016_add_linkedin_source_field
Create Date: 2025-11-04 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '017_add_hosted_videos'
down_revision = '016_add_linkedin_source_field'
branch_label = None
depends_on = None


def upgrade():
    """Upgrade database schema."""

    # Create hosted_videos table
    op.create_table(
        'hosted_videos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('composed_video_id', sa.Integer(), nullable=True),
        sa.Column('demo_site_id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),

        # Hosting details
        sa.Column('hosting_provider', sa.String(50), nullable=False),
        sa.Column('provider_video_id', sa.String(255), nullable=False),

        # URLs
        sa.Column('share_url', sa.Text(), nullable=False),
        sa.Column('embed_url', sa.Text(), nullable=False),
        sa.Column('thumbnail_url', sa.Text(), nullable=True),
        sa.Column('download_url', sa.Text(), nullable=True),

        # Metadata
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # Video properties
        sa.Column('privacy', sa.String(20), nullable=False, server_default='unlisted'),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.Text(), nullable=True),
        sa.Column('format', sa.String(20), nullable=True),
        sa.Column('resolution', sa.String(20), nullable=True),
        sa.Column('fps', sa.Integer(), nullable=True),
        sa.Column('bitrate_kbps', sa.Integer(), nullable=True),
        sa.Column('codec', sa.String(50), nullable=True),

        # Status tracking
        sa.Column('status', sa.String(50), nullable=False, server_default='uploading'),
        sa.Column('upload_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('upload_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('upload_time_seconds', sa.Float(), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),

        # Error handling
        sa.Column('upload_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('retry_after', sa.DateTime(timezone=True), nullable=True),

        # Analytics - view tracking
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unique_viewers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('avg_watch_percentage', sa.Float(), nullable=True),
        sa.Column('avg_watch_duration_seconds', sa.Float(), nullable=True),
        sa.Column('total_watch_time_seconds', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('completion_rate', sa.Float(), nullable=True),

        # Analytics - engagement
        sa.Column('likes_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('comments_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('shares_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('click_through_rate', sa.Float(), nullable=True),

        # Provider-specific analytics
        sa.Column('loom_analytics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('provider_analytics', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # Cost tracking
        sa.Column('hosting_cost_monthly', sa.Numeric(10, 4), nullable=False, server_default='0.0'),
        sa.Column('storage_cost_monthly', sa.Numeric(10, 4), nullable=False, server_default='0.0'),
        sa.Column('bandwidth_cost_monthly', sa.Numeric(10, 4), nullable=False, server_default='0.0'),
        sa.Column('bandwidth_used_gb', sa.Numeric(10, 2), nullable=False, server_default='0.0'),
        sa.Column('total_cost_usd', sa.Numeric(10, 4), nullable=False, server_default='0.0'),
        sa.Column('cost_per_view', sa.Numeric(10, 4), nullable=True),

        # S3-specific fields
        sa.Column('s3_bucket', sa.String(255), nullable=True),
        sa.Column('s3_key', sa.String(500), nullable=True),
        sa.Column('s3_region', sa.String(50), nullable=True),
        sa.Column('cloudfront_distribution_id', sa.String(255), nullable=True),
        sa.Column('cloudfront_url', sa.Text(), nullable=True),
        sa.Column('signed_url_expiration', sa.DateTime(timezone=True), nullable=True),

        # Loom-specific fields
        sa.Column('loom_folder_id', sa.String(255), nullable=True),
        sa.Column('loom_workspace_id', sa.String(255), nullable=True),
        sa.Column('loom_video_password', sa.String(255), nullable=True),

        # Delivery optimization
        sa.Column('cdn_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('cdn_provider', sa.String(50), nullable=True),
        sa.Column('edge_locations', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # Transcoding
        sa.Column('transcoded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('transcoding_profile', sa.String(50), nullable=True),
        sa.Column('transcoding_cost', sa.Numeric(10, 4), nullable=True),

        # Metadata and configuration
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('upload_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # Flags
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('analytics_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('download_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('comments_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('embed_enabled', sa.Boolean(), nullable=False, server_default='true'),

        # Expiration
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('auto_delete_after_days', sa.Integer(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['demo_site_id'], ['demo_sites.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE')
    )

    # Create indexes for hosted_videos
    op.create_index('ix_hosted_videos_demo_site_id', 'hosted_videos', ['demo_site_id'])
    op.create_index('ix_hosted_videos_lead_id', 'hosted_videos', ['lead_id'])
    op.create_index('ix_hosted_videos_hosting_provider', 'hosted_videos', ['hosting_provider'])
    op.create_index('ix_hosted_videos_provider_video_id', 'hosted_videos', ['provider_video_id'], unique=True)
    op.create_index('ix_hosted_videos_title', 'hosted_videos', ['title'])
    op.create_index('ix_hosted_videos_company_name', 'hosted_videos', ['company_name'])
    op.create_index('ix_hosted_videos_privacy', 'hosted_videos', ['privacy'])
    op.create_index('ix_hosted_videos_status', 'hosted_videos', ['status'])
    op.create_index('ix_hosted_videos_upload_completed_at', 'hosted_videos', ['upload_completed_at'])
    op.create_index('ix_hosted_videos_view_count', 'hosted_videos', ['view_count'])
    op.create_index('ix_hosted_videos_last_viewed_at', 'hosted_videos', ['last_viewed_at'])
    op.create_index('ix_hosted_videos_total_cost_usd', 'hosted_videos', ['total_cost_usd'])
    op.create_index('ix_hosted_videos_is_active', 'hosted_videos', ['is_active'])
    op.create_index('ix_hosted_videos_is_deleted', 'hosted_videos', ['is_deleted'])
    op.create_index('ix_hosted_videos_expires_at', 'hosted_videos', ['expires_at'])
    op.create_index('ix_hosted_videos_created_at', 'hosted_videos', ['created_at'])
    op.create_index('ix_hosted_videos_deleted_at', 'hosted_videos', ['deleted_at'])

    # Create video_views table
    op.create_table(
        'video_views',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hosted_video_id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=True),

        # Viewer information
        sa.Column('viewer_ip', sa.String(45), nullable=True),
        sa.Column('viewer_user_agent', sa.Text(), nullable=True),
        sa.Column('viewer_location', sa.String(255), nullable=True),
        sa.Column('viewer_country', sa.String(2), nullable=True),
        sa.Column('viewer_city', sa.String(100), nullable=True),
        sa.Column('viewer_region', sa.String(100), nullable=True),

        # Device information
        sa.Column('viewer_device', sa.String(50), nullable=True),
        sa.Column('viewer_os', sa.String(50), nullable=True),
        sa.Column('viewer_browser', sa.String(50), nullable=True),
        sa.Column('screen_resolution', sa.String(20), nullable=True),

        # Watch metrics
        sa.Column('watch_duration_seconds', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('watch_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),

        # Engagement timeline
        sa.Column('play_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('pause_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('seek_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('replay_count', sa.Integer(), nullable=False, server_default='0'),

        # Quality of experience
        sa.Column('playback_quality', sa.String(20), nullable=True),
        sa.Column('buffering_events', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_buffering_seconds', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('average_bitrate', sa.Integer(), nullable=True),
        sa.Column('dropped_frames', sa.Integer(), nullable=False, server_default='0'),

        # Interaction tracking
        sa.Column('clicked_cta', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('cta_clicked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cta_type', sa.String(50), nullable=True),

        # Engagement actions
        sa.Column('liked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('commented', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('shared', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('downloaded', sa.Boolean(), nullable=False, server_default='false'),

        # Session tracking
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('session_duration_seconds', sa.Float(), nullable=True),
        sa.Column('is_first_view', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('previous_view_id', sa.Integer(), nullable=True),

        # Referral tracking
        sa.Column('referrer_url', sa.Text(), nullable=True),
        sa.Column('referrer_domain', sa.String(255), nullable=True),
        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),
        sa.Column('utm_content', sa.String(100), nullable=True),

        # Watch progress tracking
        sa.Column('watch_progress', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('engagement_points', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # Provider-specific data
        sa.Column('provider_view_id', sa.String(255), nullable=True),
        sa.Column('provider_analytics', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # Timestamps
        sa.Column('viewed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('view_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('view_ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        # Flags
        sa.Column('is_bot', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_suspicious', sa.Boolean(), nullable=False, server_default='false'),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['hosted_video_id'], ['hosted_videos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['previous_view_id'], ['video_views.id'], ondelete='SET NULL')
    )

    # Create indexes for video_views
    op.create_index('ix_video_views_hosted_video_id', 'video_views', ['hosted_video_id'])
    op.create_index('ix_video_views_lead_id', 'video_views', ['lead_id'])
    op.create_index('ix_video_views_viewer_ip', 'video_views', ['viewer_ip'])
    op.create_index('ix_video_views_viewer_country', 'video_views', ['viewer_country'])
    op.create_index('ix_video_views_viewer_device', 'video_views', ['viewer_device'])
    op.create_index('ix_video_views_completed', 'video_views', ['completed'])
    op.create_index('ix_video_views_session_id', 'video_views', ['session_id'])
    op.create_index('ix_video_views_referrer_domain', 'video_views', ['referrer_domain'])
    op.create_index('ix_video_views_utm_source', 'video_views', ['utm_source'])
    op.create_index('ix_video_views_provider_view_id', 'video_views', ['provider_view_id'], unique=True)
    op.create_index('ix_video_views_viewed_at', 'video_views', ['viewed_at'])
    op.create_index('ix_video_views_is_bot', 'video_views', ['is_bot'])


def downgrade():
    """Downgrade database schema."""

    # Drop video_views table
    op.drop_index('ix_video_views_is_bot', table_name='video_views')
    op.drop_index('ix_video_views_viewed_at', table_name='video_views')
    op.drop_index('ix_video_views_provider_view_id', table_name='video_views')
    op.drop_index('ix_video_views_utm_source', table_name='video_views')
    op.drop_index('ix_video_views_referrer_domain', table_name='video_views')
    op.drop_index('ix_video_views_session_id', table_name='video_views')
    op.drop_index('ix_video_views_completed', table_name='video_views')
    op.drop_index('ix_video_views_viewer_device', table_name='video_views')
    op.drop_index('ix_video_views_viewer_country', table_name='video_views')
    op.drop_index('ix_video_views_viewer_ip', table_name='video_views')
    op.drop_index('ix_video_views_lead_id', table_name='video_views')
    op.drop_index('ix_video_views_hosted_video_id', table_name='video_views')
    op.drop_table('video_views')

    # Drop hosted_videos table
    op.drop_index('ix_hosted_videos_deleted_at', table_name='hosted_videos')
    op.drop_index('ix_hosted_videos_created_at', table_name='hosted_videos')
    op.drop_index('ix_hosted_videos_expires_at', table_name='hosted_videos')
    op.drop_index('ix_hosted_videos_is_deleted', table_name='hosted_videos')
    op.drop_index('ix_hosted_videos_is_active', table_name='hosted_videos')
    op.drop_index('ix_hosted_videos_total_cost_usd', table_name='hosted_videos')
    op.drop_index('ix_hosted_videos_last_viewed_at', table_name='hosted_videos')
    op.drop_index('ix_hosted_videos_view_count', table_name='hosted_videos')
    op.drop_index('ix_hosted_videos_upload_completed_at', table_name='hosted_videos')
    op.drop_index('ix_hosted_videos_status', table_name='hosted_videos')
    op.drop_index('ix_hosted_videos_privacy', table_name='hosted_videos')
    op.drop_index('ix_hosted_videos_company_name', table_name='hosted_videos')
    op.drop_index('ix_hosted_videos_title', table_name='hosted_videos')
    op.drop_index('ix_hosted_videos_provider_video_id', table_name='hosted_videos')
    op.drop_index('ix_hosted_videos_hosting_provider', table_name='hosted_videos')
    op.drop_index('ix_hosted_videos_lead_id', table_name='hosted_videos')
    op.drop_index('ix_hosted_videos_demo_site_id', table_name='hosted_videos')
    op.drop_table('hosted_videos')
