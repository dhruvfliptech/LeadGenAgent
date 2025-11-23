"""
API endpoints for data export and analytics.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func, text
from datetime import datetime
from io import BytesIO

from app.core.database import get_db
from app.services.export_service import ExportService, AnalyticsAggregator
from pydantic import BaseModel


router = APIRouter()


# Pydantic models
class ExportRequest(BaseModel):
    export_type: str = "csv"  # csv, excel, json
    data_type: str = "leads"  # leads, analytics, comprehensive
    filters: Optional[Dict[str, Any]] = None
    include_contact_info: bool = True
    scheduled: bool = False


class ExportResponse(BaseModel):
    export_type: str
    data_type: str
    filename: str
    file_path: Optional[str]
    content_type: str
    record_count: int
    file_size_bytes: int
    filters_applied: Optional[Dict[str, Any]]
    include_contact_info: Optional[bool]
    created_at: str


class AnalyticsRequest(BaseModel):
    filters: Optional[Dict[str, Any]] = None
    include_performance: bool = True
    days: int = 30


# Export endpoints
@router.post("/create", response_model=ExportResponse)
async def create_export(
    export_request: ExportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new data export."""
    try:
        # Validate export type
        valid_export_types = ["csv", "excel", "json"]
        if export_request.export_type not in valid_export_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid export type. Must be one of: {valid_export_types}"
            )

        # Validate data type
        valid_data_types = ["leads", "analytics", "comprehensive"]
        if export_request.data_type not in valid_data_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid data type. Must be one of: {valid_data_types}"
            )

        # Instantiate service per request
        export_service = ExportService(db)
        result = await export_service.create_export(
            export_type=export_request.export_type,
            data_type=export_request.data_type,
            filters=export_request.filters,
            include_contact_info=export_request.include_contact_info,
            scheduled=export_request.scheduled
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download")
async def download_export(
    export_request: ExportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create and download an export immediately."""
    try:
        # Instantiate service per request
        export_service = ExportService(db)
        result = await export_service.create_export(
            export_type=export_request.export_type,
            data_type=export_request.data_type,
            filters=export_request.filters,
            include_contact_info=export_request.include_contact_info,
            scheduled=False
        )
        
        content = result["content"]
        filename = result["filename"]
        content_type = result["content_type"]
        
        if isinstance(content, str):
            # Text content (CSV, JSON)
            return Response(
                content=content,
                media_type=content_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # Binary content (Excel, ZIP)
            return StreamingResponse(
                BytesIO(content),
                media_type=content_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leads/csv")
async def export_leads_csv(
    include_contact_info: bool = Query(True),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    status: Optional[List[str]] = Query(None),
    location_ids: Optional[List[int]] = Query(None),
    categories: Optional[List[str]] = Query(None),
    has_email: Optional[bool] = Query(None),
    has_phone: Optional[bool] = Query(None),
    keywords: Optional[List[str]] = Query(None),
    exclude_keywords: Optional[List[str]] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    limit: Optional[int] = Query(None, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Export leads to CSV with filtering."""
    try:
        filters = {}
        
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        if status:
            filters["status"] = status
        if location_ids:
            filters["location_ids"] = location_ids
        if categories:
            filters["categories"] = categories
        if has_email is not None:
            filters["has_email"] = has_email
        if has_phone is not None:
            filters["has_phone"] = has_phone
        if keywords:
            filters["keywords"] = keywords
        if exclude_keywords:
            filters["exclude_keywords"] = exclude_keywords
        if min_price is not None:
            filters["min_price"] = min_price
        if max_price is not None:
            filters["max_price"] = max_price
        if limit:
            filters["limit"] = limit

        # Instantiate service per request
        export_service = ExportService(db)
        result = await export_service.create_export(
            export_type="csv",
            data_type="leads",
            filters=filters,
            include_contact_info=include_contact_info,
            scheduled=False
        )
        
        return Response(
            content=result["content"],
            media_type=result["content_type"],
            headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leads/excel")
async def export_leads_excel(
    include_contact_info: bool = Query(True),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    status: Optional[List[str]] = Query(None),
    location_ids: Optional[List[int]] = Query(None),
    categories: Optional[List[str]] = Query(None),
    limit: Optional[int] = Query(None, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Export leads to Excel with filtering."""
    try:
        filters = {}
        
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        if status:
            filters["status"] = status
        if location_ids:
            filters["location_ids"] = location_ids
        if categories:
            filters["categories"] = categories
        if limit:
            filters["limit"] = limit

        # Instantiate service per request
        export_service = ExportService(db)
        result = await export_service.create_export(
            export_type="excel",
            data_type="leads",
            filters=filters,
            include_contact_info=include_contact_info,
            scheduled=False
        )
        
        return StreamingResponse(
            BytesIO(result["content"]),
            media_type=result["content_type"],
            headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/json")
async def export_analytics_json(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Export analytics to JSON."""
    try:
        filters = {"days": days}

        # Instantiate service per request
        export_service = ExportService(db)
        result = await export_service.create_export(
            export_type="json",
            data_type="analytics",
            filters=filters,
            scheduled=False
        )
        
        return Response(
            content=result["content"],
            media_type=result["content_type"],
            headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comprehensive/zip")
async def export_comprehensive_zip(
    export_type: str = Query("json", regex="^(csv|excel|json)$"),
    include_contact_info: bool = Query(True),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Export comprehensive data package as ZIP."""
    try:
        filters = {"days": days}

        # Instantiate service per request
        export_service = ExportService(db)
        result = await export_service.create_export(
            export_type=export_type,
            data_type="comprehensive",
            filters=filters,
            include_contact_info=include_contact_info,
            scheduled=False
        )
        
        content = result["content"]
        
        # For comprehensive exports, content is a dict with multiple files
        if isinstance(content, dict):
            # Create ZIP in memory
            import zipfile
            from io import BytesIO
            
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_type, file_content in content.items():
                    filename = f"{file_type}.{export_type}"
                    if isinstance(file_content, str):
                        zip_file.writestr(filename, file_content)
                    else:
                        zip_file.writestr(filename, file_content)
            
            zip_content = zip_buffer.getvalue()
            zip_buffer.close()
            
            return StreamingResponse(
                BytesIO(zip_content),
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
            )
        else:
            return StreamingResponse(
                BytesIO(content),
                media_type=result["content_type"],
                headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analytics endpoints
@router.post("/analytics/generate")
async def generate_analytics(
    analytics_request: AnalyticsRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate analytics data."""
    try:
        aggregator = AnalyticsAggregator(db)

        # Get lead analytics (using await for async methods)
        lead_analytics = await aggregator.get_lead_analytics(analytics_request.filters)
        
        result = {"lead_analytics": lead_analytics}
        
        # Add performance analytics if requested
        if analytics_request.include_performance:
            performance_analytics = await aggregator.get_performance_analytics(
                analytics_request.filters
            )
            result["performance_analytics"] = performance_analytics
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/leads")
async def get_lead_analytics(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    location_ids: Optional[List[int]] = Query(None),
    categories: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get lead analytics with filtering."""
    try:
        filters = {}
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        if location_ids:
            filters["location_ids"] = location_ids
        if categories:
            filters["categories"] = categories

        aggregator = AnalyticsAggregator(db)
        analytics = await aggregator.get_lead_analytics(filters)
        
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/performance")
async def get_performance_analytics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get system performance analytics."""
    try:
        filters = {"days": days}

        aggregator = AnalyticsAggregator(db)
        analytics = await aggregator.get_performance_analytics(filters)
        
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Export history endpoints
@router.get("/history")
async def get_export_history(
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
):
    """Get export history."""
    try:
        # Instantiate service per request
        export_service = ExportService(db)
        history = export_service.get_export_history(days)
        return {"exports": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/cleanup")
async def cleanup_old_exports(
    days: int = Query(30, ge=7),
    db: AsyncSession = Depends(get_db)
):
    """Clean up old export files."""
    try:
        # Instantiate service per request
        export_service = ExportService(db)
        deleted_count = export_service.cleanup_old_exports(days)
        return {
            "message": f"Cleaned up {deleted_count} old export files",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Configuration endpoints
@router.get("/config/export-types")
async def get_export_types():
    """Get available export types."""
    return {
        "export_types": [
            {"value": "csv", "label": "CSV", "description": "Comma-separated values"},
            {"value": "excel", "label": "Excel", "description": "Microsoft Excel spreadsheet"},
            {"value": "json", "label": "JSON", "description": "JavaScript Object Notation"}
        ]
    }


@router.get("/config/data-types")
async def get_data_types():
    """Get available data types for export."""
    return {
        "data_types": [
            {"value": "leads", "label": "Leads", "description": "Lead data with filtering options"},
            {"value": "analytics", "label": "Analytics", "description": "System analytics and performance data"},
            {"value": "comprehensive", "label": "Comprehensive", "description": "Complete data package with leads and analytics"}
        ]
    }


@router.get("/config/filters")
async def get_available_filters():
    """Get available filters for data export."""
    return {
        "filters": {
            "date": {
                "date_from": {"type": "datetime", "description": "Start date for filtering"},
                "date_to": {"type": "datetime", "description": "End date for filtering"}
            },
            "lead_status": {
                "status": {
                    "type": "array",
                    "description": "Lead status values",
                    "options": ["new", "contacted", "qualified", "converted", "rejected"]
                }
            },
            "location": {
                "location_ids": {"type": "array", "description": "Location IDs to include"},
                "location_names": {"type": "array", "description": "Location names to include"}
            },
            "category": {
                "categories": {"type": "array", "description": "Categories to include"}
            },
            "price": {
                "min_price": {"type": "number", "description": "Minimum price filter"},
                "max_price": {"type": "number", "description": "Maximum price filter"}
            },
            "contact": {
                "has_email": {"type": "boolean", "description": "Filter by email availability"},
                "has_phone": {"type": "boolean", "description": "Filter by phone availability"}
            },
            "keywords": {
                "keywords": {"type": "array", "description": "Keywords to search for"},
                "exclude_keywords": {"type": "array", "description": "Keywords to exclude"}
            },
            "limit": {
                "limit": {"type": "number", "description": "Maximum number of records"}
            }
        }
    }


# Statistics endpoints
@router.get("/stats/exportable-data")
async def get_exportable_data_stats(db: AsyncSession = Depends(get_db)):
    """Get statistics about exportable data (simplified for MVP)."""
    try:
        from app.models.leads import Lead
        from datetime import timedelta

        # Lead statistics
        total_query = select(func.count(Lead.id))
        result = await db.execute(total_query)
        total_leads = result.scalar() or 0

        email_query = select(func.count(Lead.id)).where(Lead.email.isnot(None))
        result = await db.execute(email_query)
        leads_with_email = result.scalar() or 0

        phone_query = select(func.count(Lead.id)).where(Lead.phone.isnot(None))
        result = await db.execute(phone_query)
        leads_with_phone = result.scalar() or 0

        both_query = select(func.count(Lead.id)).where(
            and_(Lead.email.isnot(None), Lead.phone.isnot(None))
        )
        result = await db.execute(both_query)
        leads_with_both = result.scalar() or 0

        # Recent activity (last 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        recent_query = select(func.count(Lead.id)).where(Lead.scraped_at >= cutoff_date)
        result = await db.execute(recent_query)
        recent_leads = result.scalar() or 0

        # Calculate estimated export sizes (rough estimates)
        avg_lead_size_bytes = 500  # Estimated average lead record size
        estimated_csv_size = total_leads * avg_lead_size_bytes
        estimated_json_size = int(total_leads * avg_lead_size_bytes * 1.5)  # JSON is larger
        estimated_excel_size = total_leads * avg_lead_size_bytes * 2  # Excel is largest

        return {
            "total_leads": total_leads,
            "leads_with_contact_info": {
                "email": leads_with_email,
                "phone": leads_with_phone,
                "both": leads_with_both
            },
            "recent_activity_30_days": {
                "leads": recent_leads,
                # MVP: Other stats commented out (require additional models)
                # "auto_responses": 0,
                # "rule_executions": 0,
                # "schedule_executions": 0
            },
            "estimated_export_sizes": {
                "csv_bytes": estimated_csv_size,
                "json_bytes": estimated_json_size,
                "excel_bytes": estimated_excel_size
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))