"""
Create LinkedIn Contacts Tables

Revision ID: 023
Revises: 022
Create Date: 2025-01-XX

Creates tables for LinkedIn contact import and messaging:
- linkedin_contacts: Imported contacts from LinkedIn CSV
- linkedin_messages: Message history and tracking
- linkedin_connections: OAuth tokens and connection status
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers
revision = '023'
down_revision = '022'  # Update based on your last migration
branch_labels = None
depends_on = None


def upgrade():
    """Create LinkedIn contacts tables."""

    # Create linkedin_contacts table
    op.create_table(
        'linkedin_contacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=255), nullable=False),
        sa.Column('last_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('linkedin_url', sa.String(length=500), nullable=True),
        sa.Column('company', sa.String(length=500), nullable=True),
        sa.Column('position', sa.String(length=500), nullable=True),
        sa.Column('headline', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('industry', sa.String(length=255), nullable=True),
        sa.Column('profile_picture_url', sa.String(length=1000), nullable=True),
        sa.Column('connected_on', sa.DateTime(), nullable=True),
        sa.Column('mutual_connections_count', sa.Integer(), default=0),
        sa.Column('profile_data', JSON, nullable=True),
        sa.Column('imported_from', sa.String(length=50), default='csv'),
        sa.Column('import_batch_id', sa.String(length=100), nullable=True),
        sa.Column('csv_filename', sa.String(length=500), nullable=True),
        sa.Column('last_messaged_at', sa.DateTime(), nullable=True),
        sa.Column('total_messages_sent', sa.Integer(), default=0),
        sa.Column('last_message_status', sa.String(length=50), nullable=True),
        sa.Column('can_message', sa.Boolean(), default=True),
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('campaign_ids', JSON, default=list),
        sa.Column('tags', JSON, default=list),
        sa.Column('response_received', sa.Boolean(), default=False),
        sa.Column('last_response_at', sa.DateTime(), nullable=True),
        sa.Column('engagement_score', sa.Integer(), default=0),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), default='active'),
        sa.Column('is_premium', sa.Boolean(), default=False),
        sa.Column('unsubscribed', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for linkedin_contacts
    op.create_index('idx_linkedin_first_name', 'linkedin_contacts', ['first_name'])
    op.create_index('idx_linkedin_last_name', 'linkedin_contacts', ['last_name'])
    op.create_index('idx_linkedin_email', 'linkedin_contacts', ['email'])
    op.create_index('idx_linkedin_url', 'linkedin_contacts', ['linkedin_url'], unique=True)
    op.create_index('idx_linkedin_name', 'linkedin_contacts', ['first_name', 'last_name'])
    op.create_index('idx_linkedin_company', 'linkedin_contacts', ['company'])
    op.create_index('idx_linkedin_status', 'linkedin_contacts', ['status', 'can_message'])
    op.create_index('idx_linkedin_import', 'linkedin_contacts', ['imported_from', 'import_batch_id'])
    op.create_index('idx_linkedin_lead_id', 'linkedin_contacts', ['lead_id'])

    # Create foreign key to leads table
    op.create_foreign_key(
        'fk_linkedin_contacts_lead_id',
        'linkedin_contacts',
        'leads',
        ['lead_id'],
        ['id'],
        ondelete='SET NULL',
    )

    # Create linkedin_messages table
    op.create_table(
        'linkedin_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('message_content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=50), default='direct'),
        sa.Column('linkedin_message_id', sa.String(length=255), nullable=True),
        sa.Column('conversation_id', sa.String(length=255), nullable=True),
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('personalized_fields', JSON, default=dict),
        sa.Column('status', sa.String(length=50), default='pending'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('replied', sa.Boolean(), default=False),
        sa.Column('reply_at', sa.DateTime(), nullable=True),
        sa.Column('reply_content', sa.Text(), nullable=True),
        sa.Column('clicked_link', sa.Boolean(), default=False),
        sa.Column('click_count', sa.Integer(), default=0),
        sa.Column('scheduled_for', sa.DateTime(), nullable=True),
        sa.Column('priority', sa.Integer(), default=0),
        sa.Column('rate_limit_group', sa.String(length=100), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('metadata', JSON, default=dict),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for linkedin_messages
    op.create_index('idx_message_contact_id', 'linkedin_messages', ['contact_id'])
    op.create_index('idx_message_linkedin_id', 'linkedin_messages', ['linkedin_message_id'], unique=True)
    op.create_index('idx_message_conversation_id', 'linkedin_messages', ['conversation_id'])
    op.create_index('idx_message_campaign_id', 'linkedin_messages', ['campaign_id'])
    op.create_index('idx_message_status', 'linkedin_messages', ['status'])
    op.create_index('idx_message_sent_at', 'linkedin_messages', ['sent_at'])
    op.create_index('idx_message_scheduled_for', 'linkedin_messages', ['scheduled_for'])
    op.create_index('idx_message_created_at', 'linkedin_messages', ['created_at'])
    op.create_index('idx_message_status_date', 'linkedin_messages', ['status', 'created_at'])
    op.create_index('idx_message_campaign', 'linkedin_messages', ['campaign_id', 'status'])
    op.create_index('idx_message_scheduled', 'linkedin_messages', ['scheduled_for', 'status'])

    # Create foreign keys for linkedin_messages
    op.create_foreign_key(
        'fk_linkedin_messages_contact_id',
        'linkedin_messages',
        'linkedin_contacts',
        ['contact_id'],
        ['id'],
        ondelete='CASCADE',
    )

    op.create_foreign_key(
        'fk_linkedin_messages_campaign_id',
        'linkedin_messages',
        'campaigns',
        ['campaign_id'],
        ['id'],
        ondelete='SET NULL',
    )

    # Create linkedin_connections table
    op.create_table(
        'linkedin_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('account_name', sa.String(length=255), nullable=True),
        sa.Column('linkedin_user_id', sa.String(length=255), nullable=True),
        sa.Column('profile_email', sa.String(length=255), nullable=True),
        sa.Column('profile_name', sa.String(length=500), nullable=True),
        sa.Column('profile_picture_url', sa.String(length=1000), nullable=True),
        sa.Column('profile_url', sa.String(length=500), nullable=True),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_type', sa.String(length=50), default='Bearer'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('scope', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_valid', sa.Boolean(), default=True),
        sa.Column('last_validated_at', sa.DateTime(), nullable=True),
        sa.Column('daily_messages_sent', sa.Integer(), default=0),
        sa.Column('daily_limit_reset_at', sa.DateTime(), nullable=True),
        sa.Column('rate_limit_exceeded', sa.Boolean(), default=False),
        sa.Column('total_messages_sent', sa.Integer(), default=0),
        sa.Column('total_connections_imported', sa.Integer(), default=0),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('error_count', sa.Integer(), default=0),
        sa.Column('connection_metadata', JSON, default=dict),
        sa.Column('connected_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for linkedin_connections
    op.create_index('idx_connection_user_id', 'linkedin_connections', ['user_id'])
    op.create_index('idx_connection_linkedin_user_id', 'linkedin_connections', ['linkedin_user_id'], unique=True)
    op.create_index('idx_connection_is_active', 'linkedin_connections', ['is_active'])
    op.create_index('idx_connection_active', 'linkedin_connections', ['is_active', 'is_valid'])

    print("LinkedIn contacts tables created successfully")


def downgrade():
    """Drop LinkedIn contacts tables."""

    # Drop tables in reverse order (due to foreign keys)
    op.drop_table('linkedin_messages')
    op.drop_table('linkedin_connections')
    op.drop_table('linkedin_contacts')

    print("LinkedIn contacts tables dropped successfully")
