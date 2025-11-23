"""Add video_scripts table for Phase 4

Revision ID: 017
Revises: 016_add_linkedin_source_field
Create Date: 2025-01-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '017'
down_revision = '016_add_linkedin_source_field'
branch_labels = None
depends_on = None


def upgrade():
    """Create video_scripts table for Phase 4 video automation."""

    op.create_table(
        'video_scripts',
        sa.Column('id', sa.Integer(), nullable=False),

        # Foreign keys
        sa.Column('demo_site_id', sa.Integer(), nullable=False, index=True),
        sa.Column('lead_id', sa.Integer(), nullable=False, index=True),

        # Script configuration
        sa.Column('script_style', sa.String(50), nullable=False, index=True),

        # Script content
        sa.Column('sections', sa.JSON(), nullable=False),

        # Duration
        sa.Column('total_duration_seconds', sa.Integer(), nullable=False, index=True),

        # Messaging
        sa.Column('target_audience', sa.Text(), nullable=True),
        sa.Column('key_messages', sa.JSON(), nullable=True),

        # AI generation metadata
        sa.Column('ai_model_used', sa.String(100), nullable=True),
        sa.Column('ai_cost', sa.Float(), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('completion_tokens', sa.Integer(), nullable=True),
        sa.Column('generation_time_seconds', sa.Float(), nullable=True),

        # Script metadata
        sa.Column('metadata', sa.JSON(), nullable=True),

        # Validation and quality
        sa.Column('validation_warnings', sa.JSON(), nullable=True),
        sa.Column('is_approved', sa.String(50), nullable=False, default='pending', index=True),
        sa.Column('approved_by', sa.String(255), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_notes', sa.Text(), nullable=True),

        # Versioning
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('parent_script_id', sa.Integer(), nullable=True),

        # Usage tracking
        sa.Column('video_generated', sa.String(50), nullable=False, default='pending', index=True),
        sa.Column('video_id', sa.Integer(), nullable=True),
        sa.Column('video_url', sa.Text(), nullable=True),
        sa.Column('times_viewed', sa.Integer(), nullable=False, default=0),
        sa.Column('last_viewed_at', sa.DateTime(timezone=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, index=True),

        # Flags
        sa.Column('is_active', sa.String(50), nullable=False, default='active', index=True),
        sa.Column('is_deleted', sa.String(50), nullable=False, default='false', index=True),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['demo_site_id'], ['demo_sites.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_script_id'], ['video_scripts.id'], ondelete='SET NULL')
    )

    # Create indexes for common queries
    op.create_index('ix_video_scripts_demo_site_lead', 'video_scripts', ['demo_site_id', 'lead_id'])
    op.create_index('ix_video_scripts_style_approved', 'video_scripts', ['script_style', 'is_approved'])
    op.create_index('ix_video_scripts_duration', 'video_scripts', ['total_duration_seconds'])

    print("video_scripts table created successfully!")


def downgrade():
    """Drop video_scripts table."""

    # Drop indexes first
    op.drop_index('ix_video_scripts_duration', table_name='video_scripts')
    op.drop_index('ix_video_scripts_style_approved', table_name='video_scripts')
    op.drop_index('ix_video_scripts_demo_site_lead', table_name='video_scripts')

    # Drop table
    op.drop_table('video_scripts')

    print("video_scripts table dropped successfully!")
