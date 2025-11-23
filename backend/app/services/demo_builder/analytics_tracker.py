"""
Analytics Tracker for Demo Sites

This service tracks page views, engagement metrics, and conversions
for demo sites in a privacy-friendly way.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy import func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.demo_sites import DemoSite, DemoSiteAnalytics

logger = logging.getLogger(__name__)


class AnalyticsTracker:
    """
    Analytics tracking and reporting service.

    Tracks:
    - Page views and unique visitors
    - Time on page and bounce rate
    - CTA clicks and conversions
    """

    def __init__(self, db: AsyncSession):
        """Initialize analytics tracker with database session."""
        self.db = db

    async def track_event(
        self,
        demo_site_id: int,
        event_type: str,
        visitor_id: str,
        event_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track an analytics event.

        Args:
            demo_site_id: ID of the demo site
            event_type: Type of event (page_view, cta_click, conversion, etc.)
            visitor_id: Anonymous visitor identifier
            event_data: Additional event data

        Returns:
            True if tracking succeeded
        """
        try:
            today = date.today()

            # Get or create today's analytics record
            analytics = await self._get_or_create_analytics(demo_site_id, today)

            # Update based on event type
            if event_type == 'page_view':
                await self._track_page_view(analytics, visitor_id, event_data)

            elif event_type == 'cta_click':
                await self._track_cta_click(analytics, visitor_id, event_data)

            elif event_type == 'conversion':
                await self._track_conversion(analytics, visitor_id, event_data)

            elif event_type == 'time_on_page':
                await self._track_time_on_page(analytics, visitor_id, event_data)

            else:
                logger.warning(f"Unknown event type: {event_type}")

            # Save analytics
            await self.db.commit()

            # Update demo site totals
            await self._update_demo_site_totals(demo_site_id)

            return True

        except Exception as e:
            logger.error(f"Event tracking failed: {str(e)}")
            await self.db.rollback()
            return False

    async def _get_or_create_analytics(
        self,
        demo_site_id: int,
        date_: date
    ) -> DemoSiteAnalytics:
        """Get or create analytics record for a specific date."""
        # Try to find existing record
        result = await self.db.execute(
            self.db.query(DemoSiteAnalytics).filter(
                and_(
                    DemoSiteAnalytics.demo_site_id == demo_site_id,
                    DemoSiteAnalytics.date == date_
                )
            )
        )
        analytics = result.scalar_one_or_none()

        if not analytics:
            # Create new record
            analytics = DemoSiteAnalytics(
                demo_site_id=demo_site_id,
                date=date_,
                analytics_data={
                    'visitors': [],
                    'referrers': {},
                    'devices': {},
                    'time_samples': []
                }
            )
            self.db.add(analytics)
            await self.db.flush()

        return analytics

    async def _track_page_view(
        self,
        analytics: DemoSiteAnalytics,
        visitor_id: str,
        event_data: Optional[Dict[str, Any]]
    ):
        """Track a page view event."""
        # Increment page views
        analytics.page_views += 1

        # Track unique visitors
        analytics_data = analytics.analytics_data or {}
        visitors = analytics_data.get('visitors', [])

        if visitor_id not in visitors:
            visitors.append(visitor_id)
            analytics.unique_visitors = len(visitors)
            analytics_data['visitors'] = visitors

        # Track referrer
        if event_data and 'referrer' in event_data:
            referrer = event_data['referrer'] or 'direct'
            referrers = analytics_data.get('referrers', {})
            referrers[referrer] = referrers.get(referrer, 0) + 1
            analytics_data['referrers'] = referrers

        # Track device info
        if event_data and 'screen' in event_data:
            screen = event_data['screen']
            devices = analytics_data.get('devices', {})
            device_type = self._classify_device(screen)
            devices[device_type] = devices.get(device_type, 0) + 1
            analytics_data['devices'] = devices

        analytics.analytics_data = analytics_data

    async def _track_cta_click(
        self,
        analytics: DemoSiteAnalytics,
        visitor_id: str,
        event_data: Optional[Dict[str, Any]]
    ):
        """Track a CTA click event."""
        analytics.cta_clicks += 1

        # Store click details
        analytics_data = analytics.analytics_data or {}
        clicks = analytics_data.get('cta_details', [])
        clicks.append({
            'visitor_id': visitor_id,
            'timestamp': datetime.utcnow().isoformat(),
            'element': event_data.get('element') if event_data else None,
            'text': event_data.get('text') if event_data else None
        })
        analytics_data['cta_details'] = clicks[-100:]  # Keep last 100
        analytics.analytics_data = analytics_data

    async def _track_conversion(
        self,
        analytics: DemoSiteAnalytics,
        visitor_id: str,
        event_data: Optional[Dict[str, Any]]
    ):
        """Track a conversion event."""
        analytics.conversions += 1

        # Calculate conversion rate
        if analytics.unique_visitors > 0:
            analytics.conversion_rate = (analytics.conversions / analytics.unique_visitors) * 100

        # Store conversion details
        analytics_data = analytics.analytics_data or {}
        conversions = analytics_data.get('conversion_details', [])
        conversions.append({
            'visitor_id': visitor_id,
            'timestamp': datetime.utcnow().isoformat(),
            'type': event_data.get('type') if event_data else 'unknown'
        })
        analytics_data['conversion_details'] = conversions[-100:]
        analytics.analytics_data = analytics_data

    async def _track_time_on_page(
        self,
        analytics: DemoSiteAnalytics,
        visitor_id: str,
        event_data: Optional[Dict[str, Any]]
    ):
        """Track time spent on page."""
        if not event_data or 'time_seconds' not in event_data:
            return

        time_seconds = event_data['time_seconds']

        # Store time sample
        analytics_data = analytics.analytics_data or {}
        time_samples = analytics_data.get('time_samples', [])
        time_samples.append(time_seconds)

        # Calculate average (use last 1000 samples)
        time_samples = time_samples[-1000:]
        analytics.avg_time_on_page = sum(time_samples) / len(time_samples)

        # Calculate bounce rate (visitors with <5 seconds)
        short_visits = sum(1 for t in time_samples if t < 5)
        if len(time_samples) > 0:
            analytics.bounce_rate = (short_visits / len(time_samples)) * 100

        analytics_data['time_samples'] = time_samples
        analytics.analytics_data = analytics_data

    async def _update_demo_site_totals(self, demo_site_id: int):
        """Update the summary totals on the demo site."""
        try:
            # Get demo site
            result = await self.db.execute(
                self.db.query(DemoSite).filter(DemoSite.id == demo_site_id)
            )
            demo_site = result.scalar_one_or_none()

            if not demo_site:
                return

            # Calculate totals from all analytics records
            result = await self.db.execute(
                self.db.query(
                    func.sum(DemoSiteAnalytics.page_views).label('total_views'),
                    func.sum(DemoSiteAnalytics.conversions).label('total_conversions')
                ).filter(DemoSiteAnalytics.demo_site_id == demo_site_id)
            )
            totals = result.first()

            demo_site.page_views = totals.total_views or 0
            demo_site.total_conversions = totals.total_conversions or 0
            demo_site.last_accessed_at = datetime.utcnow()

            await self.db.commit()

        except Exception as e:
            logger.error(f"Failed to update demo site totals: {str(e)}")

    def _classify_device(self, screen: str) -> str:
        """Classify device type based on screen resolution."""
        try:
            width = int(screen.split('x')[0])

            if width < 768:
                return 'mobile'
            elif width < 1024:
                return 'tablet'
            else:
                return 'desktop'

        except:
            return 'unknown'

    async def get_analytics_summary(
        self,
        demo_site_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get analytics summary for a date range.

        Args:
            demo_site_id: ID of the demo site
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: today)

        Returns:
            Summary dict with aggregated metrics
        """
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()

            # Query analytics records
            result = await self.db.execute(
                self.db.query(DemoSiteAnalytics).filter(
                    and_(
                        DemoSiteAnalytics.demo_site_id == demo_site_id,
                        DemoSiteAnalytics.date >= start_date,
                        DemoSiteAnalytics.date <= end_date
                    )
                ).order_by(DemoSiteAnalytics.date)
            )
            records = result.scalars().all()

            # Aggregate metrics
            total_views = sum(r.page_views for r in records)
            total_unique = sum(r.unique_visitors for r in records)
            total_clicks = sum(r.cta_clicks for r in records)
            total_conversions = sum(r.conversions for r in records)

            # Calculate averages
            avg_time = (
                sum(r.avg_time_on_page for r in records) / len(records)
                if records else 0
            )
            avg_bounce = (
                sum(r.bounce_rate for r in records) / len(records)
                if records else 0
            )
            overall_conversion_rate = (
                (total_conversions / total_unique * 100)
                if total_unique > 0 else 0
            )

            return {
                'demo_site_id': demo_site_id,
                'total_page_views': total_views,
                'total_unique_visitors': total_unique,
                'total_cta_clicks': total_clicks,
                'total_conversions': total_conversions,
                'overall_conversion_rate': round(overall_conversion_rate, 2),
                'avg_time_on_page': round(avg_time, 1),
                'avg_bounce_rate': round(avg_bounce, 1),
                'date_range': {
                    'start': start_date,
                    'end': end_date
                },
                'daily_data': [r.to_dict() for r in records]
            }

        except Exception as e:
            logger.error(f"Failed to get analytics summary: {str(e)}")
            raise

    async def get_analytics_timeline(
        self,
        demo_site_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get daily analytics for the past N days.

        Args:
            demo_site_id: ID of the demo site
            days: Number of days to retrieve

        Returns:
            List of daily analytics dicts
        """
        try:
            start_date = date.today() - timedelta(days=days)
            end_date = date.today()

            result = await self.db.execute(
                self.db.query(DemoSiteAnalytics).filter(
                    and_(
                        DemoSiteAnalytics.demo_site_id == demo_site_id,
                        DemoSiteAnalytics.date >= start_date,
                        DemoSiteAnalytics.date <= end_date
                    )
                ).order_by(DemoSiteAnalytics.date)
            )
            records = result.scalars().all()

            return [r.to_dict() for r in records]

        except Exception as e:
            logger.error(f"Failed to get analytics timeline: {str(e)}")
            return []
