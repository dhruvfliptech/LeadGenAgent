"""Add voiceover tables for Phase 4 voice synthesis

Revision ID: 017_add_voiceovers
Revises: 016_add_linkedin_source
Create Date: 2025-11-04 22:00:00.000000

This migration creates tables for voice synthesis functionality:
- voiceovers: Stores generated voiceover audio files
- voiceover_usage: Tracks daily usage statistics
- voiceover_cache: Caches audio for repeated content

Phase 4, Task 2: Voice Synthesis with ElevenLabs
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = '017_add_voiceovers'
down_revision = '016_add_linkedin_source'
branch_labels = None
depends_on = None


def upgrade():
    """Create voiceover tables."""
    
    # Create voiceovers table
    op.create_table(
        'voiceovers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('video_script_id', sa.Integer(), nullable=True),
        sa.Column('demo_site_id', sa.Integer(), nullable=True),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('voice_preset', sa.String(length=100), nullable=False),
        sa.Column('voice_id', sa.String(length=100), nullable=True),
        sa.Column('voice_name', sa.String(length=255), nullable=True),
        sa.Column('voice_settings', sa.JSON(), nullable=True),
        sa.Column('model_id', sa.String(length=100), nullable=False),
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
        sa.Column('metadata', sa.JSON(), nullable=True),
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
        sa.ForeignKeyConstraint(['demo_site_id'], ['demo_sites.id'], ),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        comment='Stores generated voiceover audio files for video scripts'
    )
    
    # Create indexes for voiceovers
    op.create_index('idx_voiceovers_lead_id', 'voiceovers', ['lead_id'])
    op.create_index('idx_voiceovers_demo_site_id', 'voiceovers', ['demo_site_id'])
    op.create_index('idx_voiceovers_status', 'voiceovers', ['status'])
    op.create_index('idx_voiceovers_voice_preset', 'voiceovers', ['voice_preset'])
    op.create_index('idx_voiceovers_created_at', 'voiceovers', ['created_at'])
    op.create_index('idx_voiceovers_is_deleted', 'voiceovers', ['is_deleted'])
    
    # Create voiceover_usage table
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
        sa.Column('voice_preset_usage', sa.JSON(), nullable=True),
        sa.Column('provider_usage', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date'),
        comment='Tracks daily voiceover usage statistics'
    )
    
    # Create index for voiceover_usage
    op.create_index('idx_voiceover_usage_date', 'voiceover_usage', ['date'])
    
    # Create voiceover_cache table
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
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key'),
        comment='Caches audio for frequently used text/voice combinations'
    )
    
    # Create indexes for voiceover_cache
    op.create_index('idx_voiceover_cache_key', 'voiceover_cache', ['cache_key'])
    op.create_index('idx_voiceover_cache_voice_preset', 'voiceover_cache', ['voice_preset'])
    op.create_index('idx_voiceover_cache_created_at', 'voiceover_cache', ['created_at'])
    op.create_index('idx_voiceover_cache_expires_at', 'voiceover_cache', ['expires_at'])
    
    print("✓ Created voiceovers table with indexes")
    print("✓ Created voiceover_usage table for statistics")
    print("✓ Created voiceover_cache table for audio caching")
    print("  Phase 4, Task 2: Voice Synthesis ready")


def downgrade():
    """Drop voiceover tables."""
    
    # Drop voiceover_cache table
    op.drop_index('idx_voiceover_cache_expires_at', table_name='voiceover_cache')
    op.drop_index('idx_voiceover_cache_created_at', table_name='voiceover_cache')
    op.drop_index('idx_voiceover_cache_voice_preset', table_name='voiceover_cache')
    op.drop_index('idx_voiceover_cache_key', table_name='voiceover_cache')
    op.drop_table('voiceover_cache')
    
    # Drop voiceover_usage table
    op.drop_index('idx_voiceover_usage_date', table_name='voiceover_usage')
    op.drop_table('voiceover_usage')
    
    # Drop voiceovers table
    op.drop_index('idx_voiceovers_is_deleted', table_name='voiceovers')
    op.drop_index('idx_voiceovers_created_at', table_name='voiceovers')
    op.drop_index('idx_voiceovers_voice_preset', table_name='voiceovers')
    op.drop_index('idx_voiceovers_status', table_name='voiceovers')
    op.drop_index('idx_voiceovers_demo_site_id', table_name='voiceovers')
    op.drop_index('idx_voiceovers_lead_id', table_name='voiceovers')
    op.drop_table('voiceovers')
    
    print("✓ Removed voiceover tables and indexes")
