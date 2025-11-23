"""Add screen recordings tables

Revision ID: 017_add_screen_recordings
Revises: 016_add_linkedin_source_field
Create Date: 2024-11-04 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '017_add_screen_recordings'
down_revision = '016_add_linkedin_source_field'
branch_label = None
depends_on = None


def upgrade():
    # Create recording_sessions table
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
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_stack_trace', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_recording_sessions_session_id', 'recording_sessions', ['session_id'], unique=True)
    op.create_index('ix_recording_sessions_start_time', 'recording_sessions', ['start_time'])
    op.create_index('ix_recording_sessions_end_time', 'recording_sessions', ['end_time'])
    op.create_index('ix_recording_sessions_status', 'recording_sessions', ['status'])
    op.create_index('ix_recording_sessions_created_at', 'recording_sessions', ['created_at'])

    # Create screen_recordings table
    op.create_table(
        'screen_recordings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('demo_site_id', sa.Integer(), nullable=False),
        sa.Column('video_script_id', sa.Integer(), nullable=True),
        sa.Column('lead_id', sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(['demo_site_id'], ['demo_sites.id'], ),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.ForeignKeyConstraint(['recording_session_id'], ['recording_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_screen_recordings_demo_site_id', 'screen_recordings', ['demo_site_id'])
    op.create_index('ix_screen_recordings_video_script_id', 'screen_recordings', ['video_script_id'])
    op.create_index('ix_screen_recordings_lead_id', 'screen_recordings', ['lead_id'])
    op.create_index('ix_screen_recordings_status', 'screen_recordings', ['status'])
    op.create_index('ix_screen_recordings_recording_session_id', 'screen_recordings', ['recording_session_id'])
    op.create_index('ix_screen_recordings_created_at', 'screen_recordings', ['created_at'])
    op.create_index('ix_screen_recordings_recording_started_at', 'screen_recordings', ['recording_started_at'])
    op.create_index('ix_screen_recordings_recording_completed_at', 'screen_recordings', ['recording_completed_at'])
    op.create_index('ix_screen_recordings_is_deleted', 'screen_recordings', ['is_deleted'])

    # Create recording_segments table
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
        sa.ForeignKeyConstraint(['recording_session_id'], ['recording_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_recording_segments_recording_session_id', 'recording_segments', ['recording_session_id'])


def downgrade():
    op.drop_index('ix_recording_segments_recording_session_id', table_name='recording_segments')
    op.drop_table('recording_segments')

    op.drop_index('ix_screen_recordings_is_deleted', table_name='screen_recordings')
    op.drop_index('ix_screen_recordings_recording_completed_at', table_name='screen_recordings')
    op.drop_index('ix_screen_recordings_recording_started_at', table_name='screen_recordings')
    op.drop_index('ix_screen_recordings_created_at', table_name='screen_recordings')
    op.drop_index('ix_screen_recordings_recording_session_id', table_name='screen_recordings')
    op.drop_index('ix_screen_recordings_status', table_name='screen_recordings')
    op.drop_index('ix_screen_recordings_lead_id', table_name='screen_recordings')
    op.drop_index('ix_screen_recordings_video_script_id', table_name='screen_recordings')
    op.drop_index('ix_screen_recordings_demo_site_id', table_name='screen_recordings')
    op.drop_table('screen_recordings')

    op.drop_index('ix_recording_sessions_created_at', table_name='recording_sessions')
    op.drop_index('ix_recording_sessions_status', table_name='recording_sessions')
    op.drop_index('ix_recording_sessions_end_time', table_name='recording_sessions')
    op.drop_index('ix_recording_sessions_start_time', table_name='recording_sessions')
    op.drop_index('ix_recording_sessions_session_id', table_name='recording_sessions')
    op.drop_table('recording_sessions')
