"""
Campaign Metrics Models for Email Campaign Performance Tracking

This module provides real-time and aggregated metrics for email campaigns:
- CampaignMetrics: Aggregated campaign performance statistics
- CampaignMetricsSnapshot: Point-in-time metric snapshots for historical analysis
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, Boolean, Index
from sqlalchemy.orm import relationship
from app.models.base import Base


class CampaignMetrics(Base):
    """
    Campaign Metrics Model

    Stores aggregated performance metrics for email campaigns including
    delivery rates, engagement rates, and revenue tracking.
    """
    __tablename__ = "campaign_metrics"

    id = Column(Integer, primary_key=True, index=True)

    # Campaign reference
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), unique=True, nullable=False, index=True)

    # Send metrics
    total_recipients = Column(Integer, default=0)  # Total number of recipients
    total_sent = Column(Integer, default=0)  # Successfully sent
    total_queued = Column(Integer, default=0)  # Waiting to send
    total_sending = Column(Integer, default=0)  # Currently sending
    total_failed = Column(Integer, default=0)  # Failed to send

    # Delivery metrics
    total_delivered = Column(Integer, default=0)  # Successfully delivered
    total_bounced = Column(Integer, default=0)  # Bounced emails
    total_rejected = Column(Integer, default=0)  # Rejected by server
    hard_bounces = Column(Integer, default=0)  # Permanent failures
    soft_bounces = Column(Integer, default=0)  # Temporary failures

    # Engagement metrics
    total_opened = Column(Integer, default=0)  # Email opens
    unique_opens = Column(Integer, default=0)  # Unique recipients who opened
    total_clicked = Column(Integer, default=0)  # Link clicks
    unique_clicks = Column(Integer, default=0)  # Unique recipients who clicked
    total_replied = Column(Integer, default=0)  # Direct replies
    total_unsubscribed = Column(Integer, default=0)  # Unsubscribe requests
    total_spam_reports = Column(Integer, default=0)  # Marked as spam

    # Conversion metrics
    total_conversions = Column(Integer, default=0)  # Conversion events
    conversion_value = Column(Float, default=0.0)  # Total conversion value
    total_revenue = Column(Float, default=0.0)  # Revenue generated

    # Calculated rates (as percentages)
    delivery_rate = Column(Float, default=0.0)  # (delivered / sent) * 100
    bounce_rate = Column(Float, default=0.0)  # (bounced / sent) * 100
    open_rate = Column(Float, default=0.0)  # (unique_opens / delivered) * 100
    click_rate = Column(Float, default=0.0)  # (unique_clicks / delivered) * 100
    click_to_open_rate = Column(Float, default=0.0)  # (unique_clicks / unique_opens) * 100
    reply_rate = Column(Float, default=0.0)  # (replied / delivered) * 100
    unsubscribe_rate = Column(Float, default=0.0)  # (unsubscribed / delivered) * 100
    spam_rate = Column(Float, default=0.0)  # (spam_reports / delivered) * 100
    conversion_rate = Column(Float, default=0.0)  # (conversions / delivered) * 100

    # Time-based metrics
    first_open_at = Column(DateTime, nullable=True)
    last_open_at = Column(DateTime, nullable=True)
    first_click_at = Column(DateTime, nullable=True)
    last_click_at = Column(DateTime, nullable=True)
    average_time_to_open = Column(Integer, nullable=True)  # Seconds
    average_time_to_click = Column(Integer, nullable=True)  # Seconds

    # Cost and ROI metrics
    total_cost = Column(Float, default=0.0)  # Campaign cost
    cost_per_send = Column(Float, default=0.0)
    cost_per_open = Column(Float, default=0.0)
    cost_per_click = Column(Float, default=0.0)
    cost_per_conversion = Column(Float, default=0.0)
    roi = Column(Float, default=0.0)  # Return on investment (revenue / cost - 1) * 100

    # Quality scores
    sender_reputation_score = Column(Float, nullable=True)  # 0-100
    content_quality_score = Column(Float, nullable=True)  # 0-100
    engagement_quality_score = Column(Float, nullable=True)  # 0-100

    # A/B Testing
    is_test_campaign = Column(Boolean, default=False)
    test_group = Column(String(50), nullable=True)  # control, variant_a, variant_b, etc.
    statistical_significance = Column(Float, nullable=True)  # P-value

    # Timestamps
    metrics_started_at = Column(DateTime, nullable=True)  # When first email sent
    metrics_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime, nullable=True)  # Last engagement event

    # Relationship
    campaign = relationship("Campaign", backref="metrics", foreign_keys=[campaign_id])

    # Indexes
    __table_args__ = (
        Index('idx_metrics_rates', 'delivery_rate', 'open_rate', 'click_rate'),
        Index('idx_metrics_roi', 'roi', 'conversion_rate'),
    )

    def __repr__(self):
        return f"<CampaignMetrics(campaign_id={self.campaign_id}, open_rate={self.open_rate:.2f}%)>"

    def calculate_rates(self):
        """Recalculate all rate metrics based on current counts."""
        # Delivery rate
        if self.total_sent > 0:
            self.delivery_rate = (self.total_delivered / self.total_sent) * 100
            self.bounce_rate = (self.total_bounced / self.total_sent) * 100

        # Engagement rates
        if self.total_delivered > 0:
            self.open_rate = (self.unique_opens / self.total_delivered) * 100
            self.click_rate = (self.unique_clicks / self.total_delivered) * 100
            self.reply_rate = (self.total_replied / self.total_delivered) * 100
            self.unsubscribe_rate = (self.total_unsubscribed / self.total_delivered) * 100
            self.spam_rate = (self.total_spam_reports / self.total_delivered) * 100
            self.conversion_rate = (self.total_conversions / self.total_delivered) * 100

        # Click-to-open rate
        if self.unique_opens > 0:
            self.click_to_open_rate = (self.unique_clicks / self.unique_opens) * 100

        # Cost metrics
        if self.total_sent > 0 and self.total_cost > 0:
            self.cost_per_send = self.total_cost / self.total_sent
        if self.unique_opens > 0 and self.total_cost > 0:
            self.cost_per_open = self.total_cost / self.unique_opens
        if self.unique_clicks > 0 and self.total_cost > 0:
            self.cost_per_click = self.total_cost / self.unique_clicks
        if self.total_conversions > 0 and self.total_cost > 0:
            self.cost_per_conversion = self.total_cost / self.total_conversions

        # ROI
        if self.total_cost > 0:
            self.roi = ((self.total_revenue / self.total_cost) - 1) * 100

    @property
    def is_high_performing(self) -> bool:
        """Check if campaign is high-performing based on industry benchmarks."""
        return (
            self.delivery_rate >= 95 and
            self.open_rate >= 20 and
            self.click_rate >= 2.5 and
            self.bounce_rate < 2
        )

    @property
    def needs_attention(self) -> bool:
        """Check if campaign has concerning metrics."""
        return (
            self.bounce_rate > 5 or
            self.spam_rate > 0.1 or
            self.unsubscribe_rate > 0.5 or
            (self.total_sent > 100 and self.open_rate < 10)
        )

    def to_dict(self) -> dict:
        """Convert metrics to dictionary for API responses."""
        return {
            'campaign_id': self.campaign_id,
            'send': {
                'total_recipients': self.total_recipients,
                'total_sent': self.total_sent,
                'total_delivered': self.total_delivered,
                'delivery_rate': round(self.delivery_rate, 2),
            },
            'engagement': {
                'unique_opens': self.unique_opens,
                'unique_clicks': self.unique_clicks,
                'total_replied': self.total_replied,
                'open_rate': round(self.open_rate, 2),
                'click_rate': round(self.click_rate, 2),
                'click_to_open_rate': round(self.click_to_open_rate, 2),
                'reply_rate': round(self.reply_rate, 2),
            },
            'negative': {
                'total_bounced': self.total_bounced,
                'total_unsubscribed': self.total_unsubscribed,
                'total_spam_reports': self.total_spam_reports,
                'bounce_rate': round(self.bounce_rate, 2),
                'unsubscribe_rate': round(self.unsubscribe_rate, 2),
                'spam_rate': round(self.spam_rate, 2),
            },
            'conversion': {
                'total_conversions': self.total_conversions,
                'conversion_rate': round(self.conversion_rate, 2),
                'total_revenue': self.total_revenue,
            },
            'cost': {
                'total_cost': self.total_cost,
                'cost_per_open': round(self.cost_per_open, 4) if self.cost_per_open else 0,
                'cost_per_click': round(self.cost_per_click, 4) if self.cost_per_click else 0,
                'roi': round(self.roi, 2),
            },
            'quality': {
                'is_high_performing': self.is_high_performing,
                'needs_attention': self.needs_attention,
            },
        }


class CampaignMetricsSnapshot(Base):
    """
    Campaign Metrics Snapshot Model

    Stores point-in-time snapshots of campaign metrics for historical
    analysis and trend visualization.
    """
    __tablename__ = "campaign_metrics_snapshots"

    id = Column(Integer, primary_key=True, index=True)

    # References
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=False, index=True)
    metrics_id = Column(Integer, ForeignKey('campaign_metrics.id'), nullable=False, index=True)

    # Snapshot timing
    snapshot_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    snapshot_type = Column(String(50), default='auto', index=True)  # auto, manual, hourly, daily

    # Snapshot data (copy of key metrics at this point in time)
    total_sent = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    unique_opens = Column(Integer, default=0)
    unique_clicks = Column(Integer, default=0)
    open_rate = Column(Float, default=0.0)
    click_rate = Column(Float, default=0.0)
    total_conversions = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)

    # Relationship
    campaign = relationship("Campaign", backref="metrics_snapshots", foreign_keys=[campaign_id])

    # Indexes
    __table_args__ = (
        Index('idx_snapshot_campaign_time', 'campaign_id', 'snapshot_at'),
    )

    def __repr__(self):
        return f"<CampaignMetricsSnapshot(campaign_id={self.campaign_id}, snapshot_at={self.snapshot_at})>"
