"""
Create Phase 4 Video Creation System Tables

This migration creates all tables for the video creation system:
- screen_recordings: Browser screen recording metadata
- recording_sessions: Recording session tracking
- recording_segments: Individual recording segments
- video_scripts: AI-generated video scripts
- voiceovers: Text-to-speech audio files
- voiceover_usage: Daily usage tracking
- voiceover_cache: Audio caching for cost savings
- composed_videos: Final composed videos
- composition_jobs: Video composition job queue
- hosted_videos: Hosted video metadata and analytics
- video_views: Individual video view tracking

Created: 2024-11-05
Revision ID: 022
Revises: 021
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade():
    """Create all Phase 4 video system tables."""

    # ==================== Screen Recordings ====================
    op.create_table(
        'screen_recordings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('demo_site_id', sa.Integer(), nullable=True),
        sa.Column('video_script_id', sa.Integer(), nullable=True),
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('video_file_path', sa.Text(), nullable=True),
        sa.Column('thumbnail_path', sa.Text(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('resolution', sa.String(length=50), nullable=False, server_default='1920x1080'),
        sa.Column('frame_rate', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('format', sa.String(length=20), nullable=False, server_default='mp4'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('recording_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('interactions_performed', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('recording_session_id', sa.Integer(), nullable=True),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('segments_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_frames', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('video_bitrate', sa.Integer(), nullable=True),
        sa.Column('audio_bitrate', sa.Integer(), nullable=True),
        sa.Column('video_codec', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('recording_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recording_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['demo_site_id'], ['demo_sites.id'], ondelete='CASCADE')
    )
    op.create_index('ix_screen_recordings_id', 'screen_recordings', ['id'])
    op.create_index('ix_screen_recordings_lead_id', 'screen_recordings', ['lead_id'])
    op.create_index('ix_screen_recordings_demo_site_id', 'screen_recordings', ['demo_site_id'])
    op.create_index('ix_screen_recordings_status', 'screen_recordings', ['status'])
    op.create_index('ix_screen_recordings_created_at', 'screen_recordings', ['created_at'])
    op.create_index('ix_screen_recordings_is_deleted', 'screen_recordings', ['is_deleted'])

    # ==================== Recording Sessions ====================
    op.create_table(
        'recording_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('browser_context_id', sa.String(length=255), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('segments_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_frames', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('frames_per_second', sa.Float(), nullable=True),
        sa.Column('dropped_frames', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('cpu_usage_percent', sa.Float(), nullable=True),
        sa.Column('memory_usage_mb', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('session_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_stack_trace', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_recording_sessions_id', 'recording_sessions', ['id'])
    op.create_index('ix_recording_sessions_session_id', 'recording_sessions', ['session_id'], unique=True)
    op.create_index('ix_recording_sessions_status', 'recording_sessions', ['status'])
    op.create_index('ix_recording_sessions_created_at', 'recording_sessions', ['created_at'])

    # Add foreign key for recording_session_id in screen_recordings
    op.create_foreign_key(
        'fk_screen_recordings_session_id',
        'screen_recordings',
        'recording_sessions',
        ['recording_session_id'],
        ['id']
    )

    # ==================== Recording Segments ====================
    op.create_table(
        'recording_segments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recording_session_id', sa.Integer(), nullable=False),
        sa.Column('segment_number', sa.Integer(), nullable=False),
        sa.Column('segment_file_path', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('segment_type', sa.String(length=50), nullable=False),
        sa.Column('scene_name', sa.String(length=255), nullable=True),
        sa.Column('frames_count', sa.Integer(), nullable=True),
        sa.Column('average_frame_time_ms', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['recording_session_id'], ['recording_sessions.id'], ondelete='CASCADE')
    )
    op.create_index('ix_recording_segments_id', 'recording_segments', ['id'])
    op.create_index('ix_recording_segments_session_id', 'recording_segments', ['recording_session_id'])

    # ==================== Video Scripts ====================
    op.create_table(
        'video_scripts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('demo_site_id', sa.Integer(), nullable=True),
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('script_style', sa.String(length=50), nullable=False),
        sa.Column('sections', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('total_duration_seconds', sa.Integer(), nullable=False),
        sa.Column('target_audience', sa.Text(), nullable=True),
        sa.Column('key_messages', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_model_used', sa.String(length=100), nullable=True),
        sa.Column('ai_cost', sa.Float(), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('completion_tokens', sa.Integer(), nullable=True),
        sa.Column('generation_time_seconds', sa.Float(), nullable=True),
        sa.Column('script_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('validation_warnings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_approved', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('approved_by', sa.String(length=255), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_notes', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('parent_script_id', sa.Integer(), nullable=True),
        sa.Column('video_generated', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('video_id', sa.Integer(), nullable=True),
        sa.Column('video_url', sa.Text(), nullable=True),
        sa.Column('times_viewed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.String(length=50), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['demo_site_id'], ['demo_sites.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_script_id'], ['video_scripts.id'], ondelete='SET NULL')
    )
    op.create_index('ix_video_scripts_id', 'video_scripts', ['id'])
    op.create_index('ix_video_scripts_lead_id', 'video_scripts', ['lead_id'])
    op.create_index('ix_video_scripts_demo_site_id', 'video_scripts', ['demo_site_id'])
    op.create_index('ix_video_scripts_script_style', 'video_scripts', ['script_style'])
    op.create_index('ix_video_scripts_is_approved', 'video_scripts', ['is_approved'])
    op.create_index('ix_video_scripts_video_generated', 'video_scripts', ['video_generated'])
    op.create_index('ix_video_scripts_created_at', 'video_scripts', ['created_at'])

    # ==================== Voiceovers ====================
    op.create_table(
        'voiceovers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('video_script_id', sa.Integer(), nullable=True),
        sa.Column('demo_site_id', sa.Integer(), nullable=True),
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('voice_preset', sa.String(length=100), nullable=False),
        sa.Column('voice_id', sa.String(length=100), nullable=True),
        sa.Column('voice_name', sa.String(length=255), nullable=True),
        sa.Column('voice_settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('model_id', sa.String(length=100), nullable=False, server_default='eleven_multilingual_v2'),
        sa.Column('audio_file_path', sa.Text(), nullable=True),
        sa.Column('audio_url', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('format', sa.String(length=10), nullable=False, server_default='mp3'),
        sa.Column('sample_rate', sa.Integer(), nullable=False, server_default='44100'),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('characters_processed', sa.Integer(), nullable=False),
        sa.Column('cost_usd', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('api_provider', sa.String(length=50), nullable=False, server_default='elevenlabs'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('voice_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('merge_sections', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('add_section_pauses', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('pause_duration_ms', sa.Integer(), nullable=False, server_default='500'),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['demo_site_id'], ['demo_sites.id'], ondelete='CASCADE')
    )
    op.create_index('ix_voiceovers_id', 'voiceovers', ['id'])
    op.create_index('ix_voiceovers_lead_id', 'voiceovers', ['lead_id'])
    op.create_index('ix_voiceovers_demo_site_id', 'voiceovers', ['demo_site_id'])
    op.create_index('ix_voiceovers_voice_preset', 'voiceovers', ['voice_preset'])
    op.create_index('ix_voiceovers_status', 'voiceovers', ['status'])
    op.create_index('ix_voiceovers_created_at', 'voiceovers', ['created_at'])
    op.create_index('ix_voiceovers_is_deleted', 'voiceovers', ['is_deleted'])

    # ==================== Voiceover Usage ====================
    op.create_table(
        'voiceover_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('characters_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('requests_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost_usd', sa.Numeric(precision=10, scale=4), nullable=False, server_default='0'),
        sa.Column('total_duration_seconds', sa.Float(), nullable=False, server_default='0'),
        sa.Column('avg_duration_seconds', sa.Float(), nullable=True),
        sa.Column('total_file_size_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('voice_preset_usage', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('provider_usage', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_voiceover_usage_id', 'voiceover_usage', ['id'])
    op.create_index('ix_voiceover_usage_date', 'voiceover_usage', ['date'], unique=True)

    # ==================== Voiceover Cache ====================
    op.create_table(
        'voiceover_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cache_key', sa.String(length=64), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=False),
        sa.Column('voice_preset', sa.String(length=100), nullable=False),
        sa.Column('model_id', sa.String(length=100), nullable=False),
        sa.Column('audio_file_path', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('format', sa.String(length=10), nullable=False),
        sa.Column('sample_rate', sa.Integer(), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_voiceover_cache_id', 'voiceover_cache', ['id'])
    op.create_index('ix_voiceover_cache_key', 'voiceover_cache', ['cache_key'], unique=True)
    op.create_index('ix_voiceover_cache_voice_preset', 'voiceover_cache', ['voice_preset'])
    op.create_index('ix_voiceover_cache_created_at', 'voiceover_cache', ['created_at'])
    op.create_index('ix_voiceover_cache_expires_at', 'voiceover_cache', ['expires_at'])

    # ==================== Composed Videos ====================
    op.create_table(
        'composed_videos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('demo_site_id', sa.Integer(), nullable=True),
        sa.Column('screen_recording_id', sa.Integer(), nullable=True),
        sa.Column('voiceover_id', sa.Integer(), nullable=True),
        sa.Column('video_script_id', sa.Integer(), nullable=True),
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('video_file_path', sa.Text(), nullable=False),
        sa.Column('video_versions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('quality_2160p_path', sa.Text(), nullable=True),
        sa.Column('quality_1080p_path', sa.Text(), nullable=True),
        sa.Column('quality_720p_path', sa.Text(), nullable=True),
        sa.Column('quality_480p_path', sa.Text(), nullable=True),
        sa.Column('quality_360p_path', sa.Text(), nullable=True),
        sa.Column('thumbnail_path', sa.Text(), nullable=True),
        sa.Column('thumbnail_timestamp', sa.Float(), server_default='5.0'),
        sa.Column('duration_seconds', sa.Float(), nullable=False),
        sa.Column('resolution', sa.String(length=20), nullable=False),
        sa.Column('format', sa.String(length=20), nullable=False, server_default='mp4'),
        sa.Column('fps', sa.Integer(), server_default='30'),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('total_size_all_versions', sa.Integer(), nullable=True),
        sa.Column('audio_codec', sa.String(length=20), server_default='aac'),
        sa.Column('audio_bitrate', sa.String(length=20), server_default='192k'),
        sa.Column('audio_sample_rate', sa.Integer(), server_default='44100'),
        sa.Column('video_codec', sa.String(length=20), server_default='h264'),
        sa.Column('video_bitrate', sa.String(length=20), nullable=True),
        sa.Column('crf', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('encoding_time_seconds', sa.Float(), nullable=True),
        sa.Column('total_processing_time', sa.Float(), nullable=True),
        sa.Column('composition_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('branding_applied', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('logo_used', sa.String(length=255), nullable=True),
        sa.Column('logo_position', sa.String(length=50), nullable=True),
        sa.Column('watermark_text', sa.String(length=255), nullable=True),
        sa.Column('overlays_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('overlays_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('has_intro', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('intro_duration', sa.Float(), nullable=True),
        sa.Column('intro_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('has_outro', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('outro_duration', sa.Float(), nullable=True),
        sa.Column('outro_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('has_background_music', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('background_music_path', sa.Text(), nullable=True),
        sa.Column('background_music_volume', sa.Float(), nullable=True),
        sa.Column('web_optimized', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('preset', sa.String(length=50), server_default='fast'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cost_estimate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('cpu_time_seconds', sa.Float(), nullable=True),
        sa.Column('memory_peak_mb', sa.Float(), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('parent_video_id', sa.Integer(), nullable=True),
        sa.Column('source_recording_path', sa.Text(), nullable=True),
        sa.Column('source_voiceover_path', sa.Text(), nullable=True),
        sa.Column('source_files_validated', sa.Boolean(), server_default='false'),
        sa.Column('ffmpeg_command', sa.Text(), nullable=True),
        sa.Column('ffmpeg_version', sa.String(length=100), nullable=True),
        sa.Column('ffmpeg_output', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['demo_site_id'], ['demo_sites.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_video_id'], ['composed_videos.id'], ondelete='SET NULL')
    )
    op.create_index('ix_composed_videos_id', 'composed_videos', ['id'])
    op.create_index('ix_composed_videos_lead_id', 'composed_videos', ['lead_id'])
    op.create_index('ix_composed_videos_demo_site_id', 'composed_videos', ['demo_site_id'])
    op.create_index('ix_composed_videos_status', 'composed_videos', ['status'])
    op.create_index('ix_composed_videos_created_at', 'composed_videos', ['created_at'])
    op.create_index('ix_composed_videos_completed_at', 'composed_videos', ['completed_at'])
    op.create_index('ix_composed_videos_is_active', 'composed_videos', ['is_active'])
    op.create_index('ix_composed_videos_is_deleted', 'composed_videos', ['is_deleted'])

    # ==================== Composition Jobs ====================
    op.create_table(
        'composition_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('composed_video_id', sa.Integer(), nullable=True),
        sa.Column('demo_site_id', sa.Integer(), nullable=True),
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='queued'),
        sa.Column('progress', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('job_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('worker_id', sa.String(length=100), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('last_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['composed_video_id'], ['composed_videos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['demo_site_id'], ['demo_sites.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE')
    )
    op.create_index('ix_composition_jobs_id', 'composition_jobs', ['id'])
    op.create_index('ix_composition_jobs_status', 'composition_jobs', ['status'])
    op.create_index('ix_composition_jobs_created_at', 'composition_jobs', ['created_at'])

    # ==================== Hosted Videos ====================
    op.create_table(
        'hosted_videos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('composed_video_id', sa.Integer(), nullable=True),
        sa.Column('demo_site_id', sa.Integer(), nullable=True),
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('hosting_provider', sa.String(length=50), nullable=False),
        sa.Column('provider_video_id', sa.String(length=255), nullable=False),
        sa.Column('share_url', sa.Text(), nullable=False),
        sa.Column('embed_url', sa.Text(), nullable=False),
        sa.Column('thumbnail_url', sa.Text(), nullable=True),
        sa.Column('download_url', sa.Text(), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('privacy', sa.String(length=20), nullable=False, server_default='unlisted'),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.Text(), nullable=True),
        sa.Column('format', sa.String(length=20), nullable=True),
        sa.Column('resolution', sa.String(length=20), nullable=True),
        sa.Column('fps', sa.Integer(), nullable=True),
        sa.Column('bitrate_kbps', sa.Integer(), nullable=True),
        sa.Column('codec', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='uploading'),
        sa.Column('upload_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('upload_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('upload_time_seconds', sa.Float(), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('upload_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('retry_after', sa.DateTime(timezone=True), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unique_viewers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('avg_watch_percentage', sa.Float(), nullable=True),
        sa.Column('avg_watch_duration_seconds', sa.Float(), nullable=True),
        sa.Column('total_watch_time_seconds', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('completion_rate', sa.Float(), nullable=True),
        sa.Column('likes_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('comments_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('shares_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('click_through_rate', sa.Float(), nullable=True),
        sa.Column('loom_analytics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('provider_analytics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('hosting_cost_monthly', sa.Numeric(precision=10, scale=4), nullable=False, server_default='0.0'),
        sa.Column('storage_cost_monthly', sa.Numeric(precision=10, scale=4), nullable=False, server_default='0.0'),
        sa.Column('bandwidth_cost_monthly', sa.Numeric(precision=10, scale=4), nullable=False, server_default='0.0'),
        sa.Column('bandwidth_used_gb', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.0'),
        sa.Column('total_cost_usd', sa.Numeric(precision=10, scale=4), nullable=False, server_default='0.0'),
        sa.Column('cost_per_view', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('s3_bucket', sa.String(length=255), nullable=True),
        sa.Column('s3_key', sa.String(length=500), nullable=True),
        sa.Column('s3_region', sa.String(length=50), nullable=True),
        sa.Column('cloudfront_distribution_id', sa.String(length=255), nullable=True),
        sa.Column('cloudfront_url', sa.Text(), nullable=True),
        sa.Column('signed_url_expiration', sa.DateTime(timezone=True), nullable=True),
        sa.Column('loom_folder_id', sa.String(length=255), nullable=True),
        sa.Column('loom_workspace_id', sa.String(length=255), nullable=True),
        sa.Column('loom_video_password', sa.String(length=255), nullable=True),
        sa.Column('cdn_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('cdn_provider', sa.String(length=50), nullable=True),
        sa.Column('edge_locations', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('transcoded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('transcoding_profile', sa.String(length=50), nullable=True),
        sa.Column('transcoding_cost', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('video_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('upload_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('analytics_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('download_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('comments_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('embed_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('auto_delete_after_days', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['demo_site_id'], ['demo_sites.id'], ondelete='CASCADE')
    )
    op.create_index('ix_hosted_videos_id', 'hosted_videos', ['id'])
    op.create_index('ix_hosted_videos_lead_id', 'hosted_videos', ['lead_id'])
    op.create_index('ix_hosted_videos_demo_site_id', 'hosted_videos', ['demo_site_id'])
    op.create_index('ix_hosted_videos_provider', 'hosted_videos', ['hosting_provider'])
    op.create_index('ix_hosted_videos_provider_video_id', 'hosted_videos', ['provider_video_id'], unique=True)
    op.create_index('ix_hosted_videos_title', 'hosted_videos', ['title'])
    op.create_index('ix_hosted_videos_company_name', 'hosted_videos', ['company_name'])
    op.create_index('ix_hosted_videos_privacy', 'hosted_videos', ['privacy'])
    op.create_index('ix_hosted_videos_status', 'hosted_videos', ['status'])
    op.create_index('ix_hosted_videos_view_count', 'hosted_videos', ['view_count'])
    op.create_index('ix_hosted_videos_last_viewed_at', 'hosted_videos', ['last_viewed_at'])
    op.create_index('ix_hosted_videos_total_cost', 'hosted_videos', ['total_cost_usd'])
    op.create_index('ix_hosted_videos_is_active', 'hosted_videos', ['is_active'])
    op.create_index('ix_hosted_videos_is_deleted', 'hosted_videos', ['is_deleted'])
    op.create_index('ix_hosted_videos_expires_at', 'hosted_videos', ['expires_at'])
    op.create_index('ix_hosted_videos_created_at', 'hosted_videos', ['created_at'])
    op.create_index('ix_hosted_videos_deleted_at', 'hosted_videos', ['deleted_at'])

    # ==================== Video Views ====================
    op.create_table(
        'video_views',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hosted_video_id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('viewer_ip', sa.String(length=45), nullable=True),
        sa.Column('viewer_user_agent', sa.Text(), nullable=True),
        sa.Column('viewer_location', sa.String(length=255), nullable=True),
        sa.Column('viewer_country', sa.String(length=2), nullable=True),
        sa.Column('viewer_city', sa.String(length=100), nullable=True),
        sa.Column('viewer_region', sa.String(length=100), nullable=True),
        sa.Column('viewer_device', sa.String(length=50), nullable=True),
        sa.Column('viewer_os', sa.String(length=50), nullable=True),
        sa.Column('viewer_browser', sa.String(length=50), nullable=True),
        sa.Column('screen_resolution', sa.String(length=20), nullable=True),
        sa.Column('watch_duration_seconds', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('watch_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('play_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('pause_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('seek_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('replay_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('playback_quality', sa.String(length=20), nullable=True),
        sa.Column('buffering_events', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_buffering_seconds', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('average_bitrate', sa.Integer(), nullable=True),
        sa.Column('dropped_frames', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('clicked_cta', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('cta_clicked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cta_type', sa.String(length=50), nullable=True),
        sa.Column('liked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('commented', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('shared', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('downloaded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('session_duration_seconds', sa.Float(), nullable=True),
        sa.Column('is_first_view', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('previous_view_id', sa.Integer(), nullable=True),
        sa.Column('referrer_url', sa.Text(), nullable=True),
        sa.Column('referrer_domain', sa.String(length=255), nullable=True),
        sa.Column('utm_source', sa.String(length=100), nullable=True),
        sa.Column('utm_medium', sa.String(length=100), nullable=True),
        sa.Column('utm_campaign', sa.String(length=100), nullable=True),
        sa.Column('utm_content', sa.String(length=100), nullable=True),
        sa.Column('watch_progress', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('engagement_points', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('provider_view_id', sa.String(length=255), nullable=True),
        sa.Column('provider_analytics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('viewed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('view_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('view_ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_bot', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_suspicious', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['hosted_video_id'], ['hosted_videos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['previous_view_id'], ['video_views.id'], ondelete='SET NULL')
    )
    op.create_index('ix_video_views_id', 'video_views', ['id'])
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

    print("✅ Phase 4 Video Creation System tables created successfully!")


def downgrade():
    """Drop all Phase 4 video system tables."""
    op.drop_table('video_views')
    op.drop_table('hosted_videos')
    op.drop_table('composition_jobs')
    op.drop_table('composed_videos')
    op.drop_table('voiceover_cache')
    op.drop_table('voiceover_usage')
    op.drop_table('voiceovers')
    op.drop_table('video_scripts')
    op.drop_table('recording_segments')
    op.drop_table('recording_sessions')
    op.drop_table('screen_recordings')

    print("✅ Phase 4 Video Creation System tables dropped successfully!")
