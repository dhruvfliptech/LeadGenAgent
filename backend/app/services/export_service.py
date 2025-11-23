"""
Export service for data export and analytics.
"""

import csv
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from io import StringIO, BytesIO
from pathlib import Path
import zipfile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import and_, or_, func, select

from app.core.database import get_db
from app.models.leads import Lead
from app.models.locations import Location
from app.core.config import settings


logger = logging.getLogger(__name__)


class DataFilter:
    """
    Handles data filtering for exports.

    Note: This class should be used within async contexts with AsyncSession.
    It's not a singleton - instantiate it with a database session when needed.
    """

    def __init__(self, db: AsyncSession):
        """Initialize with an async database session."""
        self.db = db
    
    def apply_lead_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to lead query."""
        try:
            # Date range filters
            if filters.get("date_from"):
                query = query.filter(Lead.scraped_at >= filters["date_from"])
            
            if filters.get("date_to"):
                query = query.filter(Lead.scraped_at <= filters["date_to"])
            
            # Status filters
            if filters.get("status"):
                if isinstance(filters["status"], list):
                    query = query.filter(Lead.status.in_(filters["status"]))
                else:
                    query = query.filter(Lead.status == filters["status"])
            
            # Location filters
            if filters.get("location_ids"):
                query = query.filter(Lead.location_id.in_(filters["location_ids"]))
            
            if filters.get("location_names"):
                query = query.join(Location).filter(
                    Location.name.in_(filters["location_names"])
                )
            
            # Category filters
            if filters.get("categories"):
                query = query.filter(Lead.category.in_(filters["categories"]))
            
            # Price range filters
            if filters.get("min_price") is not None:
                query = query.filter(Lead.price >= filters["min_price"])
            
            if filters.get("max_price") is not None:
                query = query.filter(Lead.price <= filters["max_price"])
            
            # Contact info filters
            if filters.get("has_email") is True:
                query = query.filter(Lead.email.isnot(None))
            elif filters.get("has_email") is False:
                query = query.filter(Lead.email.is_(None))
            
            if filters.get("has_phone") is True:
                query = query.filter(Lead.phone.isnot(None))
            elif filters.get("has_phone") is False:
                query = query.filter(Lead.phone.is_(None))
            
            # Keyword filters
            if filters.get("keywords"):
                keyword_conditions = []
                for keyword in filters["keywords"]:
                    keyword_conditions.append(
                        or_(
                            Lead.title.ilike(f"%{keyword}%"),
                            Lead.description.ilike(f"%{keyword}%")
                        )
                    )
                query = query.filter(or_(*keyword_conditions))
            
            # Exclude keywords
            if filters.get("exclude_keywords"):
                for keyword in filters["exclude_keywords"]:
                    query = query.filter(
                        and_(
                            ~Lead.title.ilike(f"%{keyword}%"),
                            ~Lead.description.ilike(f"%{keyword}%")
                        )
                    )
            
            # Limit
            if filters.get("limit"):
                query = query.limit(filters["limit"])
            
            # Order by
            order_by = filters.get("order_by", "scraped_at")
            order_desc = filters.get("order_desc", True)
            
            if hasattr(Lead, order_by):
                if order_desc:
                    query = query.order_by(getattr(Lead, order_by).desc())
                else:
                    query = query.order_by(getattr(Lead, order_by))
            
            return query
            
        except Exception as e:
            logger.error(f"Failed to apply lead filters: {e}")
            return query


class CSVExporter:
    """Handles CSV export functionality."""
    
    def export_leads(self, leads: List[Lead], include_contact_info: bool = True) -> str:
        """Export leads to CSV format."""
        try:
            output = StringIO()
            
            # Define CSV columns
            columns = [
                'id', 'craigslist_id', 'title', 'description', 'category', 
                'subcategory', 'price', 'url', 'location', 'status',
                'posted_at', 'scraped_at'
            ]
            
            if include_contact_info:
                columns.extend(['email', 'phone', 'contact_name'])
            
            writer = csv.DictWriter(output, fieldnames=columns)
            writer.writeheader()
            
            for lead in leads:
                row = {
                    'id': lead.id,
                    'craigslist_id': lead.craigslist_id,
                    'title': lead.title or '',
                    'description': (lead.description or '')[:1000],  # Limit description length
                    'category': lead.category or '',
                    'subcategory': lead.subcategory or '',
                    'price': lead.price,
                    'url': lead.url,
                    'location': lead.location.name if lead.location else '',
                    'status': lead.status,
                    'posted_at': lead.posted_at.isoformat() if lead.posted_at else '',
                    'scraped_at': lead.scraped_at.isoformat() if lead.scraped_at else ''
                }
                
                if include_contact_info:
                    row.update({
                        'email': lead.email or '',
                        'phone': lead.phone or '',
                        'contact_name': lead.contact_name or ''
                    })
                
                writer.writerow(row)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            raise
    
    def export_analytics_csv(self, analytics_data: Dict[str, Any]) -> str:
        """Export analytics data to CSV."""
        try:
            output = StringIO()
            
            # Create a flattened view of analytics data
            rows = []
            
            for category, data in analytics_data.items():
                if isinstance(data, dict):
                    for key, value in data.items():
                        rows.append({
                            'category': category,
                            'metric': key,
                            'value': value,
                            'exported_at': datetime.utcnow().isoformat()
                        })
                elif isinstance(data, (list, tuple)):
                    for i, item in enumerate(data):
                        rows.append({
                            'category': category,
                            'metric': f'item_{i}',
                            'value': str(item),
                            'exported_at': datetime.utcnow().isoformat()
                        })
                else:
                    rows.append({
                        'category': category,
                        'metric': 'value',
                        'value': str(data),
                        'exported_at': datetime.utcnow().isoformat()
                    })
            
            if rows:
                writer = csv.DictWriter(output, fieldnames=['category', 'metric', 'value', 'exported_at'])
                writer.writeheader()
                writer.writerows(rows)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Analytics CSV export failed: {e}")
            raise


class ExcelExporter:
    """Handles Excel export functionality."""
    
    def export_leads_excel(self, leads: List[Lead], include_contact_info: bool = True) -> bytes:
        """Export leads to Excel format."""
        try:
            # Prepare data for DataFrame
            data = []
            
            for lead in leads:
                row = {
                    'ID': lead.id,
                    'Craigslist ID': lead.craigslist_id,
                    'Title': lead.title or '',
                    'Description': (lead.description or '')[:1000],
                    'Category': lead.category or '',
                    'Subcategory': lead.subcategory or '',
                    'Price': lead.price,
                    'URL': lead.url,
                    'Location': lead.location.name if lead.location else '',
                    'Status': lead.status,
                    'Posted At': lead.posted_at,
                    'Scraped At': lead.scraped_at
                }
                
                if include_contact_info:
                    row.update({
                        'Email': lead.email or '',
                        'Phone': lead.phone or '',
                        'Contact Name': lead.contact_name or ''
                    })
                
                data.append(row)
            
            # Create DataFrame
            df = pd.DataFrame(data)
            
            # Export to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Leads', index=False)
                
                # Add formatting
                worksheet = writer.sheets['Leads']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_name = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_name].width = adjusted_width
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            raise
    
    def export_multi_sheet_excel(self, data_sheets: Dict[str, List[Dict]]) -> bytes:
        """Export multiple data sets to different Excel sheets."""
        try:
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for sheet_name, data in data_sheets.items():
                    if data:
                        df = pd.DataFrame(data)
                        df.to_excel(writer, sheet_name=sheet_name[:31], index=False)  # Sheet name max 31 chars
                        
                        # Format sheet
                        worksheet = writer.sheets[sheet_name[:31]]
                        for column in worksheet.columns:
                            max_length = 0
                            column_name = column[0].column_letter
                            for cell in column:
                                try:
                                    if len(str(cell.value)) > max_length:
                                        max_length = len(str(cell.value))
                                except:
                                    pass
                            adjusted_width = min(max_length + 2, 50)
                            worksheet.column_dimensions[column_name].width = adjusted_width
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Multi-sheet Excel export failed: {e}")
            raise


class JSONExporter:
    """Handles JSON export functionality."""
    
    def export_leads_json(self, leads: List[Lead], include_contact_info: bool = True) -> str:
        """Export leads to JSON format."""
        try:
            data = []
            
            for lead in leads:
                lead_data = {
                    'id': lead.id,
                    'craigslist_id': lead.craigslist_id,
                    'title': lead.title,
                    'description': lead.description,
                    'category': lead.category,
                    'subcategory': lead.subcategory,
                    'price': float(lead.price) if lead.price else None,
                    'url': lead.url,
                    'location': {
                        'id': lead.location.id,
                        'name': lead.location.name,
                        'url_name': lead.location.url_name
                    } if lead.location else None,
                    'status': lead.status,
                    'is_processed': lead.is_processed,
                    'is_contacted': lead.is_contacted,
                    'posted_at': lead.posted_at.isoformat() if lead.posted_at else None,
                    'scraped_at': lead.scraped_at.isoformat() if lead.scraped_at else None,
                    'created_at': lead.created_at.isoformat() if lead.created_at else None,
                    'updated_at': lead.updated_at.isoformat() if lead.updated_at else None
                }
                
                if include_contact_info:
                    lead_data.update({
                        'email': lead.email,
                        'phone': lead.phone,
                        'contact_name': lead.contact_name
                    })
                
                data.append(lead_data)
            
            return json.dumps({
                'leads': data,
                'count': len(data),
                'exported_at': datetime.utcnow().isoformat(),
                'export_type': 'leads'
            }, indent=2)
            
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            raise
    
    def export_analytics_json(self, analytics_data: Dict[str, Any]) -> str:
        """Export analytics data to JSON."""
        try:
            export_data = {
                'analytics': analytics_data,
                'exported_at': datetime.utcnow().isoformat(),
                'export_type': 'analytics'
            }
            
            return json.dumps(export_data, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Analytics JSON export failed: {e}")
            raise


class AnalyticsAggregator:
    """Aggregates analytics data for export."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_lead_analytics(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get comprehensive lead analytics."""
        try:
            filters = filters or {}

            # Base query conditions
            conditions = []
            if filters.get("date_from"):
                conditions.append(Lead.scraped_at >= filters["date_from"])
            if filters.get("date_to"):
                conditions.append(Lead.scraped_at <= filters["date_to"])

            # Total counts
            total_query = select(func.count(Lead.id))
            if conditions:
                total_query = total_query.where(and_(*conditions))
            result = await self.db.execute(total_query)
            total_leads = result.scalar() or 0

            # Status breakdown
            status_query = select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
            if conditions:
                status_query = status_query.where(and_(*conditions))
            result = await self.db.execute(status_query)
            status_breakdown = dict(result.all())

            # Category breakdown
            category_query = select(Lead.category, func.count(Lead.id)).where(
                Lead.category.isnot(None)
            ).group_by(Lead.category)
            if conditions:
                category_query = category_query.where(and_(*conditions))
            result = await self.db.execute(category_query)
            category_breakdown = dict(result.all())

            # Location breakdown
            location_query = select(Location.name, func.count(Lead.id)).join(
                Lead, Lead.location_id == Location.id
            ).group_by(Location.name)
            if conditions:
                location_query = location_query.where(and_(*conditions))
            result = await self.db.execute(location_query)
            location_breakdown = dict(result.all())

            # Contact info stats
            email_query = select(func.count(Lead.id)).where(Lead.email.isnot(None))
            phone_query = select(func.count(Lead.id)).where(Lead.phone.isnot(None))
            both_query = select(func.count(Lead.id)).where(
                and_(Lead.email.isnot(None), Lead.phone.isnot(None))
            )

            if conditions:
                email_query = email_query.where(and_(*conditions))
                phone_query = phone_query.where(and_(*conditions))
                both_query = both_query.where(and_(*conditions))

            result = await self.db.execute(email_query)
            leads_with_email = result.scalar() or 0
            result = await self.db.execute(phone_query)
            leads_with_phone = result.scalar() or 0
            result = await self.db.execute(both_query)
            leads_with_both = result.scalar() or 0

            # Price statistics
            price_stats_query = select(
                func.min(Lead.price),
                func.max(Lead.price),
                func.avg(Lead.price),
                func.count(Lead.price)
            ).where(Lead.price.isnot(None))

            if conditions:
                price_stats_query = price_stats_query.where(and_(*conditions))

            result = await self.db.execute(price_stats_query)
            price_stats_row = result.first()
            min_price, max_price, avg_price, price_count = price_stats_row if price_stats_row else (None, None, None, 0)
            
            return {
                'overview': {
                    'total_leads': total_leads,
                    'leads_with_email': leads_with_email,
                    'leads_with_phone': leads_with_phone,
                    'leads_with_both_contacts': leads_with_both,
                    'contact_rate': (leads_with_email / total_leads * 100) if total_leads > 0 else 0
                },
                'status_breakdown': status_breakdown,
                'category_breakdown': category_breakdown,
                'location_breakdown': location_breakdown,
                'price_statistics': {
                    'min_price': float(min_price) if min_price else None,
                    'max_price': float(max_price) if max_price else None,
                    'avg_price': float(avg_price) if avg_price else None,
                    'leads_with_price': price_count
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get lead analytics: {e}")
            return {}
    
    async def get_performance_analytics(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get system performance analytics (simplified for MVP)."""
        try:
            filters = filters or {}
            cutoff_date = datetime.utcnow() - timedelta(days=filters.get("days", 30))

            # Scraping performance
            recent_leads_query = select(func.count(Lead.id)).where(
                Lead.scraped_at >= cutoff_date
            )
            result = await self.db.execute(recent_leads_query)
            recent_leads = result.scalar() or 0

            # MVP: Simplified analytics - only lead scraping stats
            # Complex analytics (auto-responses, rules, schedules) commented out for MVP
            # These require additional models that may not be implemented yet

            return {
                'scraping': {
                    'leads_scraped': recent_leads,
                    'daily_average': recent_leads / filters.get("days", 30) if recent_leads > 0 else 0
                },
                # 'auto_responses': {
                #     'total_created': 0,
                #     'total_sent': 0,
                #     'send_rate': 0
                # },
                # 'rule_engine': {
                #     'total_executions': 0,
                #     'total_matches': 0,
                #     'match_rate': 0
                # },
                # 'scheduler': {
                #     'total_executions': 0,
                #     'successful_executions': 0,
                #     'success_rate': 0
                # },
                'period_days': filters.get("days", 30),
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get performance analytics: {e}")
            return {}


class ExportService:
    """
    Main export service.

    IMPORTANT: Do NOT instantiate as a singleton. Create per-request with a database session.
    Usage:
        export_service = ExportService(db)
        result = await export_service.create_export(...)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize export service with a database session.

        Args:
            db: AsyncSession - Database session for this request
        """
        self.db = db
        self.data_filter = DataFilter(db)
        self.csv_exporter = CSVExporter()
        self.excel_exporter = ExcelExporter()
        self.json_exporter = JSONExporter()
        self.analytics_aggregator = AnalyticsAggregator(db)

        # Ensure export directory exists
        self.export_dir = Path(settings.EXPORT_DIRECTORY)
        self.export_dir.mkdir(exist_ok=True)
    
    async def create_export(
        self,
        export_type: str = "csv",
        data_type: str = "leads",
        filters: Optional[Dict[str, Any]] = None,
        include_contact_info: bool = True,
        scheduled: bool = False
    ) -> Dict[str, Any]:
        """Create a data export."""
        try:
            filters = filters or {}
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            logger.info(f"Creating {export_type} export for {data_type}")
            
            if data_type == "leads":
                return await self._export_leads(
                    export_type, filters, include_contact_info, timestamp, scheduled
                )
            elif data_type == "analytics":
                return await self._export_analytics(
                    export_type, filters, timestamp, scheduled
                )
            elif data_type == "comprehensive":
                return await self._export_comprehensive(
                    export_type, filters, include_contact_info, timestamp, scheduled
                )
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
                
        except Exception as e:
            logger.error(f"Export creation failed: {e}")
            raise
    
    async def _export_leads(
        self,
        export_type: str,
        filters: Dict[str, Any],
        include_contact_info: bool,
        timestamp: str,
        scheduled: bool
    ) -> Dict[str, Any]:
        """Export leads data."""
        try:
            # Get filtered leads using async query
            query = select(Lead).options(selectinload(Lead.location))
            query = self.data_filter.apply_lead_filters(query, filters)
            result = await self.db.execute(query)
            leads = result.scalars().all()
            
            logger.info(f"Exporting {len(leads)} leads")
            
            # Generate export based on type
            if export_type == "csv":
                content = self.csv_exporter.export_leads(leads, include_contact_info)
                filename = f"leads_export_{timestamp}.csv"
                content_type = "text/csv"
                
            elif export_type == "excel":
                content = self.excel_exporter.export_leads_excel(leads, include_contact_info)
                filename = f"leads_export_{timestamp}.xlsx"
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                
            elif export_type == "json":
                content = self.json_exporter.export_leads_json(leads, include_contact_info)
                filename = f"leads_export_{timestamp}.json"
                content_type = "application/json"
                
            else:
                raise ValueError(f"Unsupported export type: {export_type}")
            
            # Save to file if scheduled
            file_path = None
            if scheduled:
                file_path = self.export_dir / filename
                if isinstance(content, str):
                    file_path.write_text(content)
                else:
                    file_path.write_bytes(content)
            
            return {
                'export_type': export_type,
                'data_type': 'leads',
                'filename': filename,
                'file_path': str(file_path) if file_path else None,
                'content': content if not scheduled else None,
                'content_type': content_type,
                'record_count': len(leads),
                'file_size_bytes': len(content) if isinstance(content, str) else len(content),
                'filters_applied': filters,
                'include_contact_info': include_contact_info,
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Lead export failed: {e}")
            raise
    
    async def _export_analytics(
        self,
        export_type: str,
        filters: Dict[str, Any],
        timestamp: str,
        scheduled: bool
    ) -> Dict[str, Any]:
        """Export analytics data."""
        try:
            # Get analytics data (using await for async methods)
            lead_analytics = await self.analytics_aggregator.get_lead_analytics(filters)
            performance_analytics = await self.analytics_aggregator.get_performance_analytics(filters)
            
            analytics_data = {
                'lead_analytics': lead_analytics,
                'performance_analytics': performance_analytics
            }
            
            logger.info("Exporting analytics data")
            
            # Generate export based on type
            if export_type == "csv":
                content = self.csv_exporter.export_analytics_csv(analytics_data)
                filename = f"analytics_export_{timestamp}.csv"
                content_type = "text/csv"
                
            elif export_type == "excel":
                # Convert analytics to sheets
                data_sheets = {
                    'Lead Analytics': self._flatten_analytics_for_excel(lead_analytics),
                    'Performance': self._flatten_analytics_for_excel(performance_analytics)
                }
                content = self.excel_exporter.export_multi_sheet_excel(data_sheets)
                filename = f"analytics_export_{timestamp}.xlsx"
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                
            elif export_type == "json":
                content = self.json_exporter.export_analytics_json(analytics_data)
                filename = f"analytics_export_{timestamp}.json"
                content_type = "application/json"
                
            else:
                raise ValueError(f"Unsupported export type: {export_type}")
            
            # Save to file if scheduled
            file_path = None
            if scheduled:
                file_path = self.export_dir / filename
                if isinstance(content, str):
                    file_path.write_text(content)
                else:
                    file_path.write_bytes(content)
            
            return {
                'export_type': export_type,
                'data_type': 'analytics',
                'filename': filename,
                'file_path': str(file_path) if file_path else None,
                'content': content if not scheduled else None,
                'content_type': content_type,
                'file_size_bytes': len(content) if isinstance(content, str) else len(content),
                'filters_applied': filters,
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Analytics export failed: {e}")
            raise
    
    async def _export_comprehensive(
        self,
        export_type: str,
        filters: Dict[str, Any],
        include_contact_info: bool,
        timestamp: str,
        scheduled: bool
    ) -> Dict[str, Any]:
        """Export comprehensive data package."""
        try:
            logger.info("Creating comprehensive export package")
            
            # Create individual exports
            leads_export = await self._export_leads(
                export_type, filters, include_contact_info, timestamp, False
            )
            
            analytics_export = await self._export_analytics(
                export_type, filters, timestamp, False
            )
            
            # Create ZIP package
            zip_filename = f"comprehensive_export_{timestamp}.zip"
            zip_path = self.export_dir / zip_filename if scheduled else None
            
            if scheduled:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Add leads export
                    leads_filename = f"leads.{export_type}"
                    if isinstance(leads_export['content'], str):
                        zip_file.writestr(leads_filename, leads_export['content'])
                    else:
                        zip_file.writestr(leads_filename, leads_export['content'])
                    
                    # Add analytics export
                    analytics_filename = f"analytics.{export_type}"
                    if isinstance(analytics_export['content'], str):
                        zip_file.writestr(analytics_filename, analytics_export['content'])
                    else:
                        zip_file.writestr(analytics_filename, analytics_export['content'])
                    
                    # Add metadata
                    metadata = {
                        'export_info': {
                            'created_at': datetime.utcnow().isoformat(),
                            'export_type': export_type,
                            'filters_applied': filters,
                            'include_contact_info': include_contact_info,
                            'lead_count': leads_export['record_count']
                        }
                    }
                    zip_file.writestr('metadata.json', json.dumps(metadata, indent=2))
                
                file_size = zip_path.stat().st_size
            else:
                file_size = (
                    leads_export['file_size_bytes'] + 
                    analytics_export['file_size_bytes']
                )
            
            return {
                'export_type': export_type,
                'data_type': 'comprehensive',
                'filename': zip_filename,
                'file_path': str(zip_path) if zip_path else None,
                'content': {
                    'leads': leads_export['content'],
                    'analytics': analytics_export['content']
                } if not scheduled else None,
                'content_type': 'application/zip',
                'record_count': leads_export['record_count'],
                'file_size_bytes': file_size,
                'components': [
                    {'type': 'leads', 'count': leads_export['record_count']},
                    {'type': 'analytics', 'sections': 2}
                ],
                'filters_applied': filters,
                'include_contact_info': include_contact_info,
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Comprehensive export failed: {e}")
            raise
    
    def _flatten_analytics_for_excel(self, analytics_data: Dict[str, Any]) -> List[Dict]:
        """Flatten nested analytics data for Excel export."""
        try:
            flattened = []
            
            def flatten_dict(data, prefix=""):
                for key, value in data.items():
                    if isinstance(value, dict):
                        flatten_dict(value, f"{prefix}{key}_" if prefix else f"{key}_")
                    else:
                        flattened.append({
                            'Metric': f"{prefix}{key}".replace("_", " ").title(),
                            'Value': value
                        })
            
            flatten_dict(analytics_data)
            return flattened
            
        except Exception as e:
            logger.error(f"Failed to flatten analytics data: {e}")
            return []
    
    def get_export_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get export history (would need to implement export tracking table)."""
        try:
            # This would query an export_history table if implemented
            # For now, return file system based history
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            exports = []
            
            if self.export_dir.exists():
                for file_path in self.export_dir.glob("*_export_*.{csv,xlsx,json,zip}"):
                    try:
                        stat = file_path.stat()
                        created_at = datetime.fromtimestamp(stat.st_ctime)
                        
                        if created_at >= cutoff_date:
                            exports.append({
                                'filename': file_path.name,
                                'file_path': str(file_path),
                                'file_size_bytes': stat.st_size,
                                'created_at': created_at.isoformat()
                            })
                    except Exception as e:
                        logger.error(f"Failed to process export file {file_path}: {e}")
                        continue
            
            # Sort by creation date, newest first
            exports.sort(key=lambda x: x['created_at'], reverse=True)
            return exports
            
        except Exception as e:
            logger.error(f"Failed to get export history: {e}")
            return []
    
    def cleanup_old_exports(self, days: int = 30) -> int:
        """Clean up old export files."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted_count = 0
            
            if self.export_dir.exists():
                for file_path in self.export_dir.glob("*_export_*.*"):
                    try:
                        stat = file_path.stat()
                        created_at = datetime.fromtimestamp(stat.st_ctime)
                        
                        if created_at < cutoff_date:
                            file_path.unlink()
                            deleted_count += 1
                            logger.info(f"Deleted old export: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Failed to delete export file {file_path}: {e}")
                        continue
            
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old exports: {e}")
            return 0


# NOTE: Do NOT create a global singleton instance!
# ExportService must be instantiated per-request with a database session:
#
# Usage in endpoints:
#   from app.core.database import get_db
#
#   @router.post("/exports")
#   async def create_export(db: AsyncSession = Depends(get_db)):
#       export_service = ExportService(db)
#       result = await export_service.create_export(...)
#       return result