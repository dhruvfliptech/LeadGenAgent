"""Create campaign metrics tables for performance tracking

Revision ID: 024_create_campaign_metrics_tables
Revises: 023_create_auto_response_tables
Create Date: 2025-11-05

Creates:
- campaign_metrics: Aggregated campaign performance statistics
- campaign_metrics_snapshots: Point-in-time metric snapshots
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '024_create_campaign_metrics_tables'
down_revision = '023_create_auto_response_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create campaign metrics tables"""

    # Create campaign_metrics table
    op.create_table(
        'campaign_metrics',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id'), unique=True, nullable=False, index=True),

        # Send metrics
        sa.Column('total_recipients', sa.Integer(), default=0),
        sa.Column('total_sent', sa.Integer(), default=0),
        sa.Column('total_queued', sa.Integer(), default=0),
        sa.Column('total_sending', sa.Integer(), default=0),
        sa.Column('total_failed', sa.Integer(), default=0),

        # Delivery metrics
        sa.Column('total_delivered', sa.Integer(), default=0),
        sa.Column('total_bounced', sa.Integer(), default=0),
        sa.Column('total_rejected', sa.Integer(), default=0),
        sa.Column('hard_bounces', sa.Integer(), default=0),
        sa.Column('soft_bounces', sa.Integer(), default=0),

        # Engagement metrics
        sa.Column('total_opened', sa.Integer(), default=0),
        sa.Column('unique_opens', sa.Integer(), default=0),
        sa.Column('total_clicked', sa.Integer(), default=0),
        sa.Column('unique_clicks', sa.Integer(), default=0),
        sa.Column('total_replied', sa.Integer(), default=0),
        sa.Column('total_unsubscribed', sa.Integer(), default=0),
        sa.Column('total_spam_reports', sa.Integer(), default=0),

        # Conversion metrics
        sa.Column('total_conversions', sa.Integer(), default=0),
        sa.Column('conversion_value', sa.Float(), default=0.0),
        sa.Column('total_revenue', sa.Float(), default=0.0),

        # Calculated rates (as percentages)
        sa.Column('delivery_rate', sa.Float(), default=0.0),
        sa.Column('bounce_rate', sa.Float(), default=0.0),
        sa.Column('open_rate', sa.Float(), default=0.0),
        sa.Column('click_rate', sa.Float(), default=0.0),
        sa.Column('click_to_open_rate', sa.Float(), default=0.0),
        sa.Column('reply_rate', sa.Float(), default=0.0),
        sa.Column('unsubscribe_rate', sa.Float(), default=0.0),
        sa.Column('spam_rate', sa.Float(), default=0.0),
        sa.Column('conversion_rate', sa.Float(), default=0.0),

        # Time-based metrics
        sa.Column('first_open_at', sa.DateTime(), nullable=True),
        sa.Column('last_open_at', sa.DateTime(), nullable=True),
        sa.Column('first_click_at', sa.DateTime(), nullable=True),
        sa.Column('last_click_at', sa.DateTime(), nullable=True),
        sa.Column('average_time_to_open', sa.Integer(), nullable=True),  # Seconds
        sa.Column('average_time_to_click', sa.Integer(), nullable=True),  # Seconds

        # Cost and ROI metrics
        sa.Column('total_cost', sa.Float(), default=0.0),
        sa.Column('cost_per_send', sa.Float(), default=0.0),
        sa.Column('cost_per_open', sa.Float(), default=0.0),
        sa.Column('cost_per_click', sa.Float(), default=0.0),
        sa.Column('cost_per_conversion', sa.Float(), default=0.0),
        sa.Column('roi', sa.Float(), default=0.0),

        # Quality scores
        sa.Column('sender_reputation_score', sa.Float(), nullable=True),
        sa.Column('content_quality_score', sa.Float(), nullable=True),
        sa.Column('engagement_quality_score', sa.Float(), nullable=True),

        # A/B Testing
        sa.Column('is_test_campaign', sa.Boolean(), default=False),
        sa.Column('test_group', sa.String(50), nullable=True),
        sa.Column('statistical_significance', sa.Float(), nullable=True),

        # Timestamps
        sa.Column('metrics_started_at', sa.DateTime(), nullable=True),
        sa.Column('metrics_updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_activity_at', sa.DateTime(), nullable=True),
    )

    # Create indexes for campaign_metrics
    op.create_index('idx_metrics_rates', 'campaign_metrics', ['delivery_rate', 'open_rate', 'click_rate'])
    op.create_index('idx_metrics_roi', 'campaign_metrics', ['roi', 'conversion_rate'])

    # Create campaign_metrics_snapshots table
    op.create_table(
        'campaign_metrics_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id'), nullable=False, index=True),
        sa.Column('metrics_id', sa.Integer(), sa.ForeignKey('campaign_metrics.id'), nullable=False, index=True),

        # Snapshot timing
        sa.Column('snapshot_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column('snapshot_type', sa.String(50), server_default='auto', index=True),

        # Snapshot data (copy of key metrics at this point in time)
        sa.Column('total_sent', sa.Integer(), default=0),
        sa.Column('total_delivered', sa.Integer(), default=0),
        sa.Column('unique_opens', sa.Integer(), default=0),
        sa.Column('unique_clicks', sa.Integer(), default=0),
        sa.Column('open_rate', sa.Float(), default=0.0),
        sa.Column('click_rate', sa.Float(), default=0.0),
        sa.Column('total_conversions', sa.Integer(), default=0),
        sa.Column('conversion_rate', sa.Float(), default=0.0),
    )

    # Create indexes for campaign_metrics_snapshots
    op.create_index('idx_snapshot_campaign_time', 'campaign_metrics_snapshots', ['campaign_id', 'snapshot_at'])


def downgrade():
    """Drop campaign metrics tables"""

    # Drop indexes
    op.drop_index('idx_snapshot_campaign_time', 'campaign_metrics_snapshots')
    op.drop_index('idx_metrics_roi', 'campaign_metrics')
    op.drop_index('idx_metrics_rates', 'campaign_metrics')

    # Drop tables
    op.drop_table('campaign_metrics_snapshots')
    op.drop_table('campaign_metrics')
