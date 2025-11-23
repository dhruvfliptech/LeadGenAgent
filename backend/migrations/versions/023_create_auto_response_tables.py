"""Create auto-response tables for template-based responses

Revision ID: 023_create_auto_response_tables
Revises: 022_create_n8n_workflow_system
Create Date: 2025-11-05

Creates:
- auto_responses: Generated responses with delivery tracking
- response_variables: Template variable definitions
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = '023_create_auto_response_tables'
down_revision = '022_create_n8n_workflow_system'
branch_labels = None
depends_on = None


def upgrade():
    """Create auto-response tables"""

    # Create auto_responses table
    op.create_table(
        'auto_responses',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.id'), nullable=False, index=True),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('response_templates.id'), nullable=False, index=True),

        # Generated content
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),

        # Personalization
        sa.Column('personalization_data', JSON, server_default='{}'),
        sa.Column('variables_used', JSON, server_default='[]'),

        # Scheduling
        sa.Column('delay_minutes', sa.Integer(), default=0),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True, index=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True, index=True),

        # Delivery status
        sa.Column('status', sa.String(50), server_default='pending', index=True),
        sa.Column('delivery_status', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0),

        # Engagement tracking
        sa.Column('email_opened', sa.Boolean(), default=False),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('open_count', sa.Integer(), default=0),
        sa.Column('email_clicked', sa.Boolean(), default=False),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('click_count', sa.Integer(), default=0),
        sa.Column('lead_responded', sa.Boolean(), default=False),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.Column('response_content', sa.Text(), nullable=True),

        # A/B Testing
        sa.Column('variant_id', sa.String(100), nullable=True, index=True),

        # AI Enhancement
        sa.Column('ai_enhanced', sa.Boolean(), default=False),
        sa.Column('ai_model_used', sa.String(100), nullable=True),
        sa.Column('ai_enhancement_cost', sa.Float(), nullable=True),

        # Email headers and metadata
        sa.Column('message_id', sa.String(255), unique=True, index=True),
        sa.Column('from_address', sa.String(255)),
        sa.Column('to_address', sa.String(255)),
        sa.Column('cc_addresses', JSON, server_default='[]'),
        sa.Column('bcc_addresses', JSON, server_default='[]'),

        # Tracking tokens
        sa.Column('tracking_token', sa.String(255), unique=True, index=True),
        sa.Column('unsubscribe_token', sa.String(255), unique=True, index=True),

        # Metrics
        sa.Column('send_duration_ms', sa.Integer(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create indexes for auto_responses
    op.create_index('idx_auto_response_lead_template', 'auto_responses', ['lead_id', 'template_id'])
    op.create_index('idx_auto_response_status_scheduled', 'auto_responses', ['status', 'scheduled_at'])
    op.create_index('idx_auto_response_engagement', 'auto_responses', ['email_opened', 'email_clicked', 'lead_responded'])
    op.create_index('idx_auto_response_variant', 'auto_responses', ['variant_id', 'status'])

    # Create response_variables table
    op.create_table(
        'response_variables',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),

        # Variable definition
        sa.Column('name', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Type information
        sa.Column('variable_type', sa.String(50), server_default='text', nullable=False),
        sa.Column('format_hint', sa.String(100), nullable=True),

        # Default values
        sa.Column('default_value', sa.Text(), nullable=True),
        sa.Column('fallback_value', sa.Text(), nullable=True),

        # Extraction configuration
        sa.Column('source_field', sa.String(100), nullable=True),
        sa.Column('source_path', sa.String(255), nullable=True),
        sa.Column('extraction_function', sa.String(100), nullable=True),

        # Validation
        sa.Column('required', sa.Boolean(), default=False),
        sa.Column('validation_regex', sa.String(500), nullable=True),
        sa.Column('min_length', sa.Integer(), nullable=True),
        sa.Column('max_length', sa.Integer(), nullable=True),

        # Transformation
        sa.Column('transform', sa.String(50), nullable=True),
        sa.Column('truncate_at', sa.Integer(), nullable=True),
        sa.Column('sanitize_html', sa.Boolean(), default=True),

        # Usage tracking
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),

        # Categorization
        sa.Column('category', sa.String(100), server_default='general', index=True),
        sa.Column('is_system', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True, index=True),

        # Examples
        sa.Column('example_value', sa.String(500), nullable=True),

        # Metadata
        sa.Column('variable_metadata', JSON, server_default='{}'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create indexes for response_variables
    op.create_index('idx_variable_category_active', 'response_variables', ['category', 'is_active'])


def downgrade():
    """Drop auto-response tables"""

    # Drop indexes
    op.drop_index('idx_variable_category_active', 'response_variables')
    op.drop_index('idx_auto_response_variant', 'auto_responses')
    op.drop_index('idx_auto_response_engagement', 'auto_responses')
    op.drop_index('idx_auto_response_status_scheduled', 'auto_responses')
    op.drop_index('idx_auto_response_lead_template', 'auto_responses')

    # Drop tables
    op.drop_table('response_variables')
    op.drop_table('auto_responses')
