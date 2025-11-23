"""Create AI-GYM tables

Revision ID: 022_create_ai_gym_tables
Revises: 021
Create Date: 2025-11-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = '022_create_ai_gym_tables'
down_revision = '021_create_campaign_management_tables'
depends_on = None


def upgrade():
    # Create ai_model_metrics table
    op.create_table('ai_model_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.String(length=100), nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False),
        sa.Column('completion_tokens', sa.Integer(), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('cost_usd', sa.Float(), nullable=False),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('user_approved', sa.Boolean(), nullable=True),
        sa.Column('edit_distance', sa.Integer(), nullable=True),
        sa.Column('error_occurred', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_model_metrics_model_id'), 'ai_model_metrics', ['model_id'], unique=False)
    op.create_index(op.f('ix_ai_model_metrics_task_type'), 'ai_model_metrics', ['task_type'], unique=False)
    op.create_index(op.f('ix_ai_model_metrics_created_at'), 'ai_model_metrics', ['created_at'], unique=False)

    # Add AI-GYM columns to existing ab_test_variants table
    op.add_column('ab_test_variants', sa.Column('avg_quality_score', sa.Float(), nullable=True))
    op.add_column('ab_test_variants', sa.Column('avg_cost_usd', sa.Float(), nullable=True))
    op.add_column('ab_test_variants', sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('ab_test_variants', sa.Column('model_id', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_ab_test_variants_model_id'), 'ab_test_variants', ['model_id'], unique=False)


def downgrade():
    # Drop AI-GYM columns from ab_test_variants
    op.drop_index(op.f('ix_ab_test_variants_model_id'), table_name='ab_test_variants')
    op.drop_column('ab_test_variants', 'model_id')
    op.drop_column('ab_test_variants', 'metadata')
    op.drop_column('ab_test_variants', 'avg_cost_usd')
    op.drop_column('ab_test_variants', 'avg_quality_score')

    # Drop ai_model_metrics table
    op.drop_index(op.f('ix_ai_model_metrics_created_at'), table_name='ai_model_metrics')
    op.drop_index(op.f('ix_ai_model_metrics_task_type'), table_name='ai_model_metrics')
    op.drop_index(op.f('ix_ai_model_metrics_model_id'), table_name='ai_model_metrics')
    op.drop_table('ai_model_metrics')
