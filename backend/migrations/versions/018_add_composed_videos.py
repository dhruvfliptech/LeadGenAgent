"""Add composed videos and composition jobs tables

Revision ID: 018_add_composed_videos
Revises: 017_add_screen_recordings
Create Date: 2024-11-04 22:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '018_add_composed_videos'
down_revision = '017_add_screen_recordings'
branch_labels = None
depends_on = None


def upgrade():
    """Create composed videos and composition jobs tables."""

    # Create composed_videos table
    op.create_table(
        'composed_videos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('demo_site_id', sa.Integer(), nullable=False),
        sa.Column('screen_recording_id', sa.Integer(), nullable=True),
        sa.Column('voiceover_id', sa.Integer(), nullable=True),
        sa.Column('video_script_id', sa.Integer(), nullable=True),
        sa.Column('lead_id', sa.Integer(), nullable=False),

        # File paths
        sa.Column('video_file_path', sa.Text(), nullable=False),
        sa.Column('video_versions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('quality_2160p_path', sa.Text(), nullable=True),
        sa.Column('quality_1080p_path', sa.Text(), nullable=True),
        sa.Column('quality_720p_path', sa.Text(), nullable=True),
        sa.Column('quality_480p_path', sa.Text(), nullable=True),
        sa.Column('quality_360p_path', sa.Text(), nullable=True),
        sa.Column('thumbnail_path', sa.Text(), nullable=True),
        sa.Column('thumbnail_timestamp', sa.Float(), nullable=True, server_default='5.0'),

        # Video metadata
        sa.Column('duration_seconds', sa.Float(), nullable=False),
        sa.Column('resolution', sa.String(length=20), nullable=False),
        sa.Column('format', sa.String(length=20), nullable=False, server_default='mp4'),
        sa.Column('fps', sa.Integer(), nullable=True, server_default='30'),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('total_size_all_versions', sa.Integer(), nullable=True),

        # Audio metadata
        sa.Column('audio_codec', sa.String(length=20), nullable=True, server_default='aac'),
        sa.Column('audio_bitrate', sa.String(length=20), nullable=True, server_default='192k'),
        sa.Column('audio_sample_rate', sa.Integer(), nullable=True, server_default='44100'),

        # Video metadata
        sa.Column('video_codec', sa.String(length=20), nullable=True, server_default='h264'),
        sa.Column('video_bitrate', sa.String(length=20), nullable=True),
        sa.Column('crf', sa.Integer(), nullable=True),

        # Processing status
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('encoding_time_seconds', sa.Float(), nullable=True),
        sa.Column('total_processing_time', sa.Float(), nullable=True),

        # Composition configuration
        sa.Column('composition_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # Branding and overlays
        sa.Column('branding_applied', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('logo_used', sa.String(length=255), nullable=True),
        sa.Column('logo_position', sa.String(length=50), nullable=True),
        sa.Column('watermark_text', sa.String(length=255), nullable=True),
        sa.Column('overlays_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('overlays_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # Intro/Outro
        sa.Column('has_intro', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('intro_duration', sa.Float(), nullable=True),
        sa.Column('intro_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('has_outro', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('outro_duration', sa.Float(), nullable=True),
        sa.Column('outro_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # Background music
        sa.Column('has_background_music', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('background_music_path', sa.Text(), nullable=True),
        sa.Column('background_music_volume', sa.Float(), nullable=True),

        # Quality and optimization
        sa.Column('web_optimized', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('preset', sa.String(length=50), nullable=True, server_default='fast'),

        # Error handling
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_retry_at', sa.DateTime(timezone=True), nullable=True),

        # Cost tracking
        sa.Column('cost_estimate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('cpu_time_seconds', sa.Float(), nullable=True),
        sa.Column('memory_peak_mb', sa.Float(), nullable=True),

        # Analytics
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),

        # Version tracking
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('parent_video_id', sa.Integer(), nullable=True),

        # Source file tracking
        sa.Column('source_recording_path', sa.Text(), nullable=True),
        sa.Column('source_voiceover_path', sa.Text(), nullable=True),
        sa.Column('source_files_validated', sa.Boolean(), nullable=False, server_default='false'),

        # FFmpeg details
        sa.Column('ffmpeg_command', sa.Text(), nullable=True),
        sa.Column('ffmpeg_version', sa.String(length=100), nullable=True),
        sa.Column('ffmpeg_output', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),

        # Flags
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['demo_site_id'], ['demo_sites.id'], ),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.ForeignKeyConstraint(['parent_video_id'], ['composed_videos.id'], )
    )

    # Create indexes for composed_videos
    op.create_index('ix_composed_videos_id', 'composed_videos', ['id'])
    op.create_index('ix_composed_videos_demo_site_id', 'composed_videos', ['demo_site_id'])
    op.create_index('ix_composed_videos_lead_id', 'composed_videos', ['lead_id'])
    op.create_index('ix_composed_videos_screen_recording_id', 'composed_videos', ['screen_recording_id'])
    op.create_index('ix_composed_videos_voiceover_id', 'composed_videos', ['voiceover_id'])
    op.create_index('ix_composed_videos_video_script_id', 'composed_videos', ['video_script_id'])
    op.create_index('ix_composed_videos_status', 'composed_videos', ['status'])
    op.create_index('ix_composed_videos_created_at', 'composed_videos', ['created_at'])
    op.create_index('ix_composed_videos_completed_at', 'composed_videos', ['completed_at'])
    op.create_index('ix_composed_videos_deleted_at', 'composed_videos', ['deleted_at'])
    op.create_index('ix_composed_videos_is_active', 'composed_videos', ['is_active'])
    op.create_index('ix_composed_videos_is_deleted', 'composed_videos', ['is_deleted'])

    # Create composition_jobs table
    op.create_table(
        'composition_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('composed_video_id', sa.Integer(), nullable=True),
        sa.Column('demo_site_id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),

        # Job details
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='queued'),
        sa.Column('progress', sa.Float(), nullable=False, server_default='0.0'),

        # Configuration
        sa.Column('job_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # Processing details
        sa.Column('worker_id', sa.String(length=100), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),

        # Error handling
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('last_retry_at', sa.DateTime(timezone=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['composed_video_id'], ['composed_videos.id'], ),
        sa.ForeignKeyConstraint(['demo_site_id'], ['demo_sites.id'], ),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], )
    )

    # Create indexes for composition_jobs
    op.create_index('ix_composition_jobs_id', 'composition_jobs', ['id'])
    op.create_index('ix_composition_jobs_composed_video_id', 'composition_jobs', ['composed_video_id'])
    op.create_index('ix_composition_jobs_demo_site_id', 'composition_jobs', ['demo_site_id'])
    op.create_index('ix_composition_jobs_lead_id', 'composition_jobs', ['lead_id'])
    op.create_index('ix_composition_jobs_status', 'composition_jobs', ['status'])
    op.create_index('ix_composition_jobs_created_at', 'composition_jobs', ['created_at'])


def downgrade():
    """Drop composed videos and composition jobs tables."""

    # Drop composition_jobs indexes
    op.drop_index('ix_composition_jobs_created_at', table_name='composition_jobs')
    op.drop_index('ix_composition_jobs_status', table_name='composition_jobs')
    op.drop_index('ix_composition_jobs_lead_id', table_name='composition_jobs')
    op.drop_index('ix_composition_jobs_demo_site_id', table_name='composition_jobs')
    op.drop_index('ix_composition_jobs_composed_video_id', table_name='composition_jobs')
    op.drop_index('ix_composition_jobs_id', table_name='composition_jobs')

    # Drop composition_jobs table
    op.drop_table('composition_jobs')

    # Drop composed_videos indexes
    op.drop_index('ix_composed_videos_is_deleted', table_name='composed_videos')
    op.drop_index('ix_composed_videos_is_active', table_name='composed_videos')
    op.drop_index('ix_composed_videos_deleted_at', table_name='composed_videos')
    op.drop_index('ix_composed_videos_completed_at', table_name='composed_videos')
    op.drop_index('ix_composed_videos_created_at', table_name='composed_videos')
    op.drop_index('ix_composed_videos_status', table_name='composed_videos')
    op.drop_index('ix_composed_videos_video_script_id', table_name='composed_videos')
    op.drop_index('ix_composed_videos_voiceover_id', table_name='composed_videos')
    op.drop_index('ix_composed_videos_screen_recording_id', table_name='composed_videos')
    op.drop_index('ix_composed_videos_lead_id', table_name='composed_videos')
    op.drop_index('ix_composed_videos_demo_site_id', table_name='composed_videos')
    op.drop_index('ix_composed_videos_id', table_name='composed_videos')

    # Drop composed_videos table
    op.drop_table('composed_videos')
