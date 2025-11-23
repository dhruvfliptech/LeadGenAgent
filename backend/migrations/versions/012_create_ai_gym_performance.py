"""create ai_gym_performance table

Revision ID: 012
Revises: 011
Create Date: 2025-11-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade():
    """Create ai_gym_performance table for tracking AI request metrics and costs."""

    op.create_table(
        'ai_gym_performance',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('task_type', sa.String(100), nullable=False, comment='Type of AI task (analyze_website, generate_email, etc.)'),
        sa.Column('model_name', sa.String(200), nullable=False, comment='AI model used (e.g., gpt-4, claude-3-opus)'),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.id', ondelete='SET NULL'), nullable=True, comment='Associated lead ID'),

        # Token usage
        sa.Column('prompt_tokens', sa.Integer(), nullable=True, comment='Number of input tokens'),
        sa.Column('completion_tokens', sa.Integer(), nullable=True, comment='Number of output tokens'),
        sa.Column('total_tokens', sa.Integer(), nullable=True, comment='Total tokens (prompt + completion)'),

        # Performance metrics
        sa.Column('cost', sa.Float(), nullable=True, comment='Cost in USD'),
        sa.Column('duration_seconds', sa.Float(), nullable=True, comment='Request duration in seconds'),
        sa.Column('response_text', sa.Text(), nullable=True, comment='AI response text (for quality analysis)'),

        # Quality scores (AI-GYM evaluation metrics)
        sa.Column('faithfulness_score', sa.Float(), nullable=True, comment='Score 0-1 for factual accuracy'),
        sa.Column('relevance_score', sa.Float(), nullable=True, comment='Score 0-1 for relevance to query'),
        sa.Column('coherence_score', sa.Float(), nullable=True, comment='Score 0-1 for logical coherence'),
        sa.Column('conciseness_score', sa.Float(), nullable=True, comment='Score 0-1 for brevity'),
        sa.Column('composite_score', sa.Float(), nullable=True, comment='Overall quality score (average)'),

        # Business metrics
        sa.Column('conversion_metric', sa.Float(), nullable=True, comment='Business outcome metric (email opened, clicked, etc.)'),

        # Metadata
        sa.Column('metadata', JSONB, nullable=True, comment='Additional metadata as JSON'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )

    # Create indexes for performance
    op.create_index('idx_ai_gym_task_type', 'ai_gym_performance', ['task_type'])
    op.create_index('idx_ai_gym_model_name', 'ai_gym_performance', ['model_name'])
    op.create_index('idx_ai_gym_created_at', 'ai_gym_performance', ['created_at'])
    op.create_index('idx_ai_gym_lead_id', 'ai_gym_performance', ['lead_id'])
    op.create_index('idx_ai_gym_cost', 'ai_gym_performance', ['cost'])


def downgrade():
    """Drop ai_gym_performance table."""

    op.drop_index('idx_ai_gym_cost', table_name='ai_gym_performance')
    op.drop_index('idx_ai_gym_lead_id', table_name='ai_gym_performance')
    op.drop_index('idx_ai_gym_created_at', table_name='ai_gym_performance')
    op.drop_index('idx_ai_gym_model_name', table_name='ai_gym_performance')
    op.drop_index('idx_ai_gym_task_type', table_name='ai_gym_performance')
    op.drop_table('ai_gym_performance')
