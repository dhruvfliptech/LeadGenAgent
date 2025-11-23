"""Create leads table

Revision ID: 004
Revises: 003
Create Date: 2025-01-27 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Create leads table."""
    op.create_table(
        'leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('craigslist_id', sa.String(50), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('contact_name', sa.String(255), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('subcategory', sa.String(100), nullable=True),
        sa.Column('is_processed', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_contacted', sa.Boolean(), nullable=False, default=False),
        sa.Column('status', sa.String(50), nullable=False, default='new'),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scraped_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'])
    )
    
    # Create indexes
    op.create_index('ix_leads_craigslist_id', 'leads', ['craigslist_id'], unique=True)
    op.create_index('ix_leads_email', 'leads', ['email'])
    op.create_index('ix_leads_phone', 'leads', ['phone'])
    op.create_index('ix_leads_location_id', 'leads', ['location_id'])
    op.create_index('ix_leads_category', 'leads', ['category'])
    op.create_index('ix_leads_subcategory', 'leads', ['subcategory'])
    op.create_index('ix_leads_is_processed', 'leads', ['is_processed'])
    op.create_index('ix_leads_is_contacted', 'leads', ['is_contacted'])
    op.create_index('ix_leads_status', 'leads', ['status'])
    op.create_index('ix_leads_posted_at', 'leads', ['posted_at'])
    op.create_index('ix_leads_scraped_at', 'leads', ['scraped_at'])
    op.create_index('ix_leads_created_at', 'leads', ['created_at'])
    op.create_index('ix_leads_updated_at', 'leads', ['updated_at'])


def downgrade():
    """Drop leads table."""
    op.drop_table('leads')
