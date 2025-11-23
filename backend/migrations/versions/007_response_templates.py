"""
Add response templates table for personalized response generation.

Revision ID: 007
Create Date: 2024-08-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '007'
down_revision = '006'


def upgrade():
    """Create response_templates table."""
    
    op.create_table(
        'response_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Template content
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        
        # Template type
        sa.Column('template_type', sa.String(50), default='general', nullable=False),
        sa.Column('communication_method', sa.String(50), default='email', nullable=False),
        
        # Variables
        sa.Column('required_variables', postgresql.JSON(), nullable=True),
        sa.Column('optional_variables', postgresql.JSON(), nullable=True),
        
        # Performance tracking
        sa.Column('times_used', sa.Integer(), default=0, nullable=False),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('avg_response_time', sa.Float(), nullable=True),
        
        # A/B Testing
        sa.Column('variant_group', sa.String(50), nullable=True),
        sa.Column('variant_name', sa.String(50), nullable=True),
        
        # Customization
        sa.Column('tone', sa.String(50), default='professional', nullable=False),
        sa.Column('length', sa.String(50), default='medium', nullable=False),
        
        # AI Enhancement
        sa.Column('use_ai_enhancement', sa.Boolean(), default=True, nullable=False),
        sa.Column('ai_instructions', sa.Text(), nullable=True),
        
        # Status
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_response_templates_name', 'response_templates', ['name'], unique=True)
    op.create_index('ix_response_templates_template_type', 'response_templates', ['template_type'])
    op.create_index('ix_response_templates_is_active', 'response_templates', ['is_active'])
    op.create_index('ix_response_templates_variant_group', 'response_templates', ['variant_group'])


def downgrade():
    """Drop response_templates table."""
    
    op.drop_index('ix_response_templates_variant_group', 'response_templates')
    op.drop_index('ix_response_templates_is_active', 'response_templates')
    op.drop_index('ix_response_templates_template_type', 'response_templates')
    op.drop_index('ix_response_templates_name', 'response_templates')
    op.drop_table('response_templates')