"""add ai mvp fields to leads

Revision ID: 011
Revises: 010
Create Date: 2025-11-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    """Add AI MVP fields to leads table for website analysis and email generation."""

    # Add AI MVP fields
    op.add_column('leads', sa.Column('ai_analysis', sa.Text(), nullable=True))
    op.add_column('leads', sa.Column('ai_model', sa.String(length=100), nullable=True))
    op.add_column('leads', sa.Column('ai_cost', sa.Float(), nullable=True))
    op.add_column('leads', sa.Column('ai_request_id', sa.Integer(), nullable=True))
    op.add_column('leads', sa.Column('generated_email_subject', sa.Text(), nullable=True))
    op.add_column('leads', sa.Column('generated_email_body', sa.Text(), nullable=True))


def downgrade():
    """Remove AI MVP fields from leads table."""

    op.drop_column('leads', 'generated_email_body')
    op.drop_column('leads', 'generated_email_subject')
    op.drop_column('leads', 'ai_request_id')
    op.drop_column('leads', 'ai_cost')
    op.drop_column('leads', 'ai_model')
    op.drop_column('leads', 'ai_analysis')
