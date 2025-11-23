"""Add source field to leads table for multi-source support

Revision ID: 014_add_linkedin_source
Revises: 013_add_email_conversations
Create Date: 2025-11-04 10:00:00.000000

This migration adds a 'source' field to the leads table to support
multiple lead sources (craigslist, linkedin, google_maps, etc.).

The source field allows us to:
- Track where each lead came from
- Filter leads by source
- Apply source-specific processing rules
- Generate source-specific reports
"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers
revision = '016_add_linkedin_source'
down_revision = '015'  # After email_finder_tables
branch_labels = None
depends_on = None


def upgrade():
    """Add source column to leads table."""

    # Add source column with default value 'craigslist'
    op.add_column('leads', sa.Column(
        'source',
        sa.String(length=50),
        nullable=False,
        server_default='craigslist',
        comment='Lead source: craigslist, linkedin, google_maps, indeed, etc.'
    ))

    # Create index on source for faster filtering
    op.create_index(
        'idx_leads_source',
        'leads',
        ['source'],
        unique=False
    )

    # Create composite index on source + status for common queries
    op.create_index(
        'idx_leads_source_status',
        'leads',
        ['source', 'status'],
        unique=False
    )

    # Create composite index on source + scraped_at for time-based queries
    op.create_index(
        'idx_leads_source_scraped_at',
        'leads',
        ['source', 'scraped_at'],
        unique=False
    )

    print("✓ Added source field to leads table")
    print("✓ Created indexes for source-based queries")
    print("  Supported sources: craigslist, linkedin, google_maps, indeed, monster, ziprecruiter")


def downgrade():
    """Remove source column and indexes."""

    # Drop indexes
    op.drop_index('idx_leads_source_scraped_at', table_name='leads')
    op.drop_index('idx_leads_source_status', table_name='leads')
    op.drop_index('idx_leads_source', table_name='leads')

    # Drop column
    op.drop_column('leads', 'source')

    print("✓ Removed source field and indexes from leads table")
