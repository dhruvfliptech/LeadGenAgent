"""Create campaign management tables for email campaigns and event tracking

Revision ID: 021
Revises: 020
Create Date: 2025-11-05 12:00:00.000000

Tables created:
- campaigns: Main campaign tracking table with metrics
- campaign_recipients: Individual recipient tracking with delivery status
- email_tracking: Granular event tracking for opens, clicks, bounces

Indexes:
- campaigns(campaign_id) UNIQUE
- campaigns(status)
- campaigns(created_by)
- campaigns(scheduled_at)
- campaigns(started_at)
- campaigns(created_at)
- campaign_recipients(campaign_id)
- campaign_recipients(lead_id)
- campaign_recipients(email_address)
- campaign_recipients(status)
- campaign_recipients(sent_at)
- email_tracking(campaign_recipient_id)
- email_tracking(event_type)
- email_tracking(ip_address)
- email_tracking(created_at)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade():
    """Create campaign management tables."""

    # Create campaigns table
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.VARCHAR(100), nullable=False),
        sa.Column('name', sa.VARCHAR(255), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.VARCHAR(50), server_default='draft', nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_recipients', sa.Integer(), server_default='0', nullable=False),
        sa.Column('emails_sent', sa.Integer(), server_default='0', nullable=False),
        sa.Column('emails_opened', sa.Integer(), server_default='0', nullable=False),
        sa.Column('emails_clicked', sa.Integer(), server_default='0', nullable=False),
        sa.Column('emails_replied', sa.Integer(), server_default='0', nullable=False),
        sa.Column('emails_bounced', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('campaign_id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL')
    )

    # Create campaigns indexes
    op.create_index('ix_campaigns_campaign_id', 'campaigns', ['campaign_id'], unique=True)
    op.create_index('ix_campaigns_name', 'campaigns', ['name'])
    op.create_index('ix_campaigns_status', 'campaigns', ['status'])
    op.create_index('ix_campaigns_created_by', 'campaigns', ['created_by'])
    op.create_index('ix_campaigns_scheduled_at', 'campaigns', ['scheduled_at'])
    op.create_index('ix_campaigns_started_at', 'campaigns', ['started_at'])
    op.create_index('ix_campaigns_created_at', 'campaigns', ['created_at'])

    # Create campaign_recipients table
    op.create_table(
        'campaign_recipients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('email_address', sa.VARCHAR(255), nullable=False),
        sa.Column('status', sa.VARCHAR(50), server_default='pending', nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('clicked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('replied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('bounced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('campaign_id', 'lead_id', name='uq_campaign_recipients_campaign_lead')
    )

    # Create campaign_recipients indexes
    op.create_index('ix_campaign_recipients_campaign_id', 'campaign_recipients', ['campaign_id'])
    op.create_index('ix_campaign_recipients_lead_id', 'campaign_recipients', ['lead_id'])
    op.create_index('ix_campaign_recipients_email_address', 'campaign_recipients', ['email_address'])
    op.create_index('ix_campaign_recipients_status', 'campaign_recipients', ['status'])
    op.create_index('ix_campaign_recipients_sent_at', 'campaign_recipients', ['sent_at'])
    op.create_index('ix_campaign_recipients_opened_at', 'campaign_recipients', ['opened_at'])
    op.create_index('ix_campaign_recipients_clicked_at', 'campaign_recipients', ['clicked_at'])
    op.create_index('ix_campaign_recipients_replied_at', 'campaign_recipients', ['replied_at'])
    op.create_index('ix_campaign_recipients_bounced_at', 'campaign_recipients', ['bounced_at'])

    # Create email_tracking table
    op.create_table(
        'email_tracking',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_recipient_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.VARCHAR(50), nullable=False),
        sa.Column('event_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['campaign_recipient_id'], ['campaign_recipients.id'], ondelete='CASCADE')
    )

    # Create email_tracking indexes
    op.create_index('ix_email_tracking_campaign_recipient_id', 'email_tracking', ['campaign_recipient_id'])
    op.create_index('ix_email_tracking_event_type', 'email_tracking', ['event_type'])
    op.create_index('ix_email_tracking_ip_address', 'email_tracking', ['ip_address'])
    op.create_index('ix_email_tracking_created_at', 'email_tracking', ['created_at'])

    # Create composite index for efficient queries on campaign metrics
    op.create_index('ix_campaign_recipients_campaign_status', 'campaign_recipients', ['campaign_id', 'status'])
    op.create_index('ix_email_tracking_recipient_event', 'email_tracking', ['campaign_recipient_id', 'event_type'])


def downgrade():
    """Drop campaign management tables."""

    # Drop indexes first (if needed)
    op.drop_index('ix_email_tracking_recipient_event', 'email_tracking')
    op.drop_index('ix_campaign_recipients_campaign_status', 'campaign_recipients')
    op.drop_index('ix_email_tracking_created_at', 'email_tracking')
    op.drop_index('ix_email_tracking_ip_address', 'email_tracking')
    op.drop_index('ix_email_tracking_event_type', 'email_tracking')
    op.drop_index('ix_email_tracking_campaign_recipient_id', 'email_tracking')

    op.drop_index('ix_campaign_recipients_bounced_at', 'campaign_recipients')
    op.drop_index('ix_campaign_recipients_replied_at', 'campaign_recipients')
    op.drop_index('ix_campaign_recipients_clicked_at', 'campaign_recipients')
    op.drop_index('ix_campaign_recipients_opened_at', 'campaign_recipients')
    op.drop_index('ix_campaign_recipients_sent_at', 'campaign_recipients')
    op.drop_index('ix_campaign_recipients_status', 'campaign_recipients')
    op.drop_index('ix_campaign_recipients_email_address', 'campaign_recipients')
    op.drop_index('ix_campaign_recipients_lead_id', 'campaign_recipients')
    op.drop_index('ix_campaign_recipients_campaign_id', 'campaign_recipients')

    op.drop_index('ix_campaigns_created_at', 'campaigns')
    op.drop_index('ix_campaigns_started_at', 'campaigns')
    op.drop_index('ix_campaigns_scheduled_at', 'campaigns')
    op.drop_index('ix_campaigns_created_by', 'campaigns')
    op.drop_index('ix_campaigns_status', 'campaigns')
    op.drop_index('ix_campaigns_name', 'campaigns')
    op.drop_index('ix_campaigns_campaign_id', 'campaigns')

    # Drop tables
    op.drop_table('email_tracking')
    op.drop_table('campaign_recipients')
    op.drop_table('campaigns')
