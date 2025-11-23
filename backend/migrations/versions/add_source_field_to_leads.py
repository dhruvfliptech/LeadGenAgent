"""Add source field to leads table for multi-source tracking

Revision ID: add_source_field
Revises:
Create Date: 2025-11-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_source_field'
down_revision = None  # Update this to the latest revision ID in your migrations
branch_labels = None
depends_on = None


def upgrade():
    # Add source column to leads table
    op.add_column('leads', sa.Column('source', sa.String(length=50), nullable=False, server_default='craigslist'))

    # Create index on source column
    op.create_index(op.f('ix_leads_source'), 'leads', ['source'], unique=False)


def downgrade():
    # Remove index
    op.drop_index(op.f('ix_leads_source'), table_name='leads')

    # Remove source column
    op.drop_column('leads', 'source')
