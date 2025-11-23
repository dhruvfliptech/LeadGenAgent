"""
Enhanced lead metadata fields for complete data capture.

Revision ID: 005
Create Date: 2024-08-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '005'
down_revision = '004'


def upgrade():
    """Add enhanced metadata fields to leads table."""
    
    # Add new columns for enhanced metadata
    op.add_column('leads', sa.Column('body_html', sa.Text(), nullable=True))
    op.add_column('leads', sa.Column('compensation', sa.String(255), nullable=True))
    op.add_column('leads', sa.Column('employment_type', postgresql.ARRAY(sa.String()), nullable=True))
    
    # Add boolean columns with nullable first, then update defaults
    op.add_column('leads', sa.Column('is_remote', sa.Boolean(), nullable=True))
    op.add_column('leads', sa.Column('is_internship', sa.Boolean(), nullable=True))
    op.add_column('leads', sa.Column('is_nonprofit', sa.Boolean(), nullable=True))
    
    # Set default values for existing records
    op.execute("UPDATE leads SET is_remote = FALSE WHERE is_remote IS NULL")
    op.execute("UPDATE leads SET is_internship = FALSE WHERE is_internship IS NULL")
    op.execute("UPDATE leads SET is_nonprofit = FALSE WHERE is_nonprofit IS NULL")
    
    # Now make them NOT NULL
    op.alter_column('leads', 'is_remote', nullable=False)
    op.alter_column('leads', 'is_internship', nullable=False)
    op.alter_column('leads', 'is_nonprofit', nullable=False)
    op.add_column('leads', sa.Column('neighborhood', sa.String(255), nullable=True))
    op.add_column('leads', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('leads', sa.Column('longitude', sa.Float(), nullable=True))
    op.add_column('leads', sa.Column('reply_email', sa.String(255), nullable=True))
    op.add_column('leads', sa.Column('reply_phone', sa.String(50), nullable=True))
    op.add_column('leads', sa.Column('reply_contact_name', sa.String(255), nullable=True))
    op.add_column('leads', sa.Column('image_urls', postgresql.JSON(), nullable=True))
    op.add_column('leads', sa.Column('attributes', postgresql.JSON(), nullable=True))
    
    # AI Analysis fields
    op.add_column('leads', sa.Column('qualification_score', sa.Float(), nullable=True))
    op.add_column('leads', sa.Column('qualification_reasoning', sa.Text(), nullable=True))
    op.add_column('leads', sa.Column('generated_responses', postgresql.JSON(), nullable=True))
    
    # Additional tracking fields
    op.add_column('leads', sa.Column('has_been_qualified', sa.Boolean(), nullable=True))
    op.execute("UPDATE leads SET has_been_qualified = FALSE WHERE has_been_qualified IS NULL")
    op.alter_column('leads', 'has_been_qualified', nullable=False)
    op.add_column('leads', sa.Column('qualified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('leads', sa.Column('response_sent_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('leads', sa.Column('response_method', sa.String(50), nullable=True))  # email, craigslist_reply, etc.
    
    # Create indexes for new fields
    op.create_index('ix_leads_compensation', 'leads', ['compensation'])
    op.create_index('ix_leads_is_remote', 'leads', ['is_remote'])
    op.create_index('ix_leads_qualification_score', 'leads', ['qualification_score'])
    op.create_index('ix_leads_has_been_qualified', 'leads', ['has_been_qualified'])
    op.create_index('ix_leads_reply_email', 'leads', ['reply_email'])


def downgrade():
    """Remove enhanced metadata fields from leads table."""
    
    # Drop indexes
    op.drop_index('ix_leads_reply_email', 'leads')
    op.drop_index('ix_leads_has_been_qualified', 'leads')
    op.drop_index('ix_leads_qualification_score', 'leads')
    op.drop_index('ix_leads_is_remote', 'leads')
    op.drop_index('ix_leads_compensation', 'leads')
    
    # Drop columns
    op.drop_column('leads', 'response_method')
    op.drop_column('leads', 'response_sent_at')
    op.drop_column('leads', 'qualified_at')
    op.drop_column('leads', 'has_been_qualified')
    op.drop_column('leads', 'generated_responses')
    op.drop_column('leads', 'qualification_reasoning')
    op.drop_column('leads', 'qualification_score')
    op.drop_column('leads', 'attributes')
    op.drop_column('leads', 'image_urls')
    op.drop_column('leads', 'reply_contact_name')
    op.drop_column('leads', 'reply_phone')
    op.drop_column('leads', 'reply_email')
    op.drop_column('leads', 'longitude')
    op.drop_column('leads', 'latitude')
    op.drop_column('leads', 'neighborhood')
    op.drop_column('leads', 'is_nonprofit')
    op.drop_column('leads', 'is_internship')
    op.drop_column('leads', 'is_remote')
    op.drop_column('leads', 'employment_type')
    op.drop_column('leads', 'compensation')
    op.drop_column('leads', 'body_html')