"""
Add qualification criteria table for lead scoring.

Revision ID: 006
Create Date: 2024-08-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '006'
down_revision = '005'


def upgrade():
    """Create qualification_criteria table."""
    
    op.create_table(
        'qualification_criteria',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Keywords
        sa.Column('required_keywords', postgresql.JSON(), nullable=True),
        sa.Column('preferred_keywords', postgresql.JSON(), nullable=True),
        sa.Column('excluded_keywords', postgresql.JSON(), nullable=True),
        
        # Compensation
        sa.Column('min_compensation', sa.Float(), nullable=True),
        sa.Column('max_compensation', sa.Float(), nullable=True),
        sa.Column('compensation_type', sa.String(50), nullable=True),
        
        # Location
        sa.Column('preferred_locations', postgresql.JSON(), nullable=True),
        sa.Column('max_distance_miles', sa.Float(), nullable=True),
        sa.Column('remote_acceptable', sa.Boolean(), default=True, nullable=False),
        
        # Employment
        sa.Column('preferred_employment_types', postgresql.JSON(), nullable=True),
        sa.Column('internship_acceptable', sa.Boolean(), default=True, nullable=False),
        sa.Column('nonprofit_acceptable', sa.Boolean(), default=True, nullable=False),
        
        # Weights
        sa.Column('keyword_weight', sa.Float(), default=0.3, nullable=False),
        sa.Column('compensation_weight', sa.Float(), default=0.2, nullable=False),
        sa.Column('location_weight', sa.Float(), default=0.2, nullable=False),
        sa.Column('employment_type_weight', sa.Float(), default=0.15, nullable=False),
        sa.Column('freshness_weight', sa.Float(), default=0.15, nullable=False),
        
        # Thresholds
        sa.Column('min_score_threshold', sa.Float(), default=0.5, nullable=False),
        sa.Column('auto_qualify_threshold', sa.Float(), default=0.8, nullable=False),
        sa.Column('auto_reject_threshold', sa.Float(), default=0.2, nullable=False),
        
        # Requirements
        sa.Column('max_days_old', sa.Integer(), default=7, nullable=False),
        sa.Column('require_contact_info', sa.Boolean(), default=False, nullable=False),
        sa.Column('require_compensation_info', sa.Boolean(), default=False, nullable=False),
        
        # Custom rules
        sa.Column('custom_rules', postgresql.JSON(), nullable=True),
        
        # Status
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_qualification_criteria_name', 'qualification_criteria', ['name'], unique=True)
    op.create_index('ix_qualification_criteria_is_active', 'qualification_criteria', ['is_active'])


def downgrade():
    """Drop qualification_criteria table."""
    
    op.drop_index('ix_qualification_criteria_is_active', 'qualification_criteria')
    op.drop_index('ix_qualification_criteria_name', 'qualification_criteria')
    op.drop_table('qualification_criteria')