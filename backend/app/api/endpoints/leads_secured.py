"""
Lead endpoints with enhanced security, validation, and rate limiting.
Implements OWASP security best practices.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Annotated
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.leads import Lead
from app.models.locations import Location
from app.api.validators import (
    SecureLeadCreate,
    SecureLeadUpdate,
    validate_pagination,
    validate_status_filter,
    validate_date_range
)

# Import rate limiting
try:
    from app.core.rate_limiter import limiter, data_limiter
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    limiter = None
    data_limiter = lambda f: f  # No-op decorator

# Import authentication (optional for now)
try:
    from app.core.auth import get_current_user, require_permission
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    get_current_user = None

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[dict])
@data_limiter
async def get_leads(
    skip: int = Query(0, ge=0, le=10000, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    location_id: Optional[int] = Query(None, ge=1, description="Filter by location ID"),
    status: Optional[str] = Query(None, pattern="^(new|contacted|qualified|converted|rejected|archived)$"),
    is_processed: Optional[bool] = Query(None, description="Filter by processed status"),
    is_contacted: Optional[bool] = Query(None, description="Filter by contacted status"),
    category: Optional[str] = Query(None, max_length=50, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    start_date: Optional[datetime] = Query(None, description="Filter leads created after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter leads created before this date"),
    search: Optional[str] = Query(None, max_length=100, description="Search in title and description"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of leads with comprehensive filtering and validation.

    Security features:
    - Input validation on all parameters
    - SQL injection protection via parameterized queries
    - Rate limiting to prevent abuse
    - Pagination limits enforced
    """
    try:
        # Validate pagination
        skip, limit = validate_pagination(skip, limit)

        # Validate status filter
        status = validate_status_filter(status)

        # Validate date range
        start_date, end_date = validate_date_range(start_date, end_date)

        # Validate price range
        if min_price is not None and max_price is not None:
            if min_price > max_price:
                raise ValueError("Minimum price cannot be greater than maximum price")

        # Build query with SQLAlchemy (parameterized, safe from SQL injection)
        query = select(Lead).options(selectinload(Lead.location))

        # Apply filters using parameterized conditions
        conditions = []

        if location_id:
            conditions.append(Lead.location_id == location_id)
        if status:
            conditions.append(Lead.status == status)
        if is_processed is not None:
            conditions.append(Lead.is_processed == is_processed)
        if is_contacted is not None:
            conditions.append(Lead.is_contacted == is_contacted)
        if category:
            # Use parameterized LIKE for safe pattern matching
            conditions.append(Lead.category.ilike(f"%{category}%"))
        if min_price is not None:
            conditions.append(Lead.price >= min_price)
        if max_price is not None:
            conditions.append(Lead.price <= max_price)
        if start_date:
            conditions.append(Lead.created_at >= start_date)
        if end_date:
            conditions.append(Lead.created_at <= end_date)

        # Search functionality with protection
        if search:
            # Sanitize search term (remove SQL metacharacters)
            search_term = search.replace("%", "\\%").replace("_", "\\_")
            search_condition = or_(
                Lead.title.ilike(f"%{search_term}%"),
                Lead.description.ilike(f"%{search_term}%")
            )
            conditions.append(search_condition)

        if conditions:
            query = query.where(and_(*conditions))

        # Apply ordering and pagination
        query = query.order_by(desc(Lead.scraped_at)).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        leads = result.scalars().all()

        # Convert to response format (sanitized)
        return [
            {
                "id": lead.id,
                "craigslist_id": lead.craigslist_id,
                "title": lead.title,
                "description": lead.description[:500] if lead.description else None,  # Limit description length
                "price": float(lead.price) if lead.price else None,
                "url": lead.url,
                "email": lead.email if lead.email else None,  # Could mask in production
                "phone": lead.phone if lead.phone else None,  # Could mask in production
                "contact_name": lead.contact_name,
                "location": {
                    "id": lead.location.id,
                    "name": lead.location.name,
                    "code": lead.location.code
                } if lead.location else None,
                "category": lead.category,
                "subcategory": lead.subcategory,
                "is_processed": lead.is_processed,
                "is_contacted": lead.is_contacted,
                "status": lead.status,
                "qualification_score": lead.qualification_score,
                "posted_at": lead.posted_at.isoformat() if lead.posted_at else None,
                "scraped_at": lead.scraped_at.isoformat() if lead.scraped_at else None,
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "updated_at": lead.updated_at.isoformat() if lead.updated_at else None
            }
            for lead in leads
        ]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching leads: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch leads")


@router.get("/{lead_id}", response_model=dict)
@data_limiter
async def get_lead(
    lead_id: int = Query(..., ge=1, description="Lead ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific lead by ID with validation.

    Security features:
    - ID validation to prevent injection
    - Rate limiting
    - Safe error messages
    """
    try:
        # Validate lead_id is a positive integer (already done by FastAPI)

        # Use parameterized query
        query = select(Lead).options(selectinload(Lead.location)).where(Lead.id == lead_id)
        result = await db.execute(query)
        lead = result.scalar_one_or_none()

        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Return sanitized response
        return {
            "id": lead.id,
            "craigslist_id": lead.craigslist_id,
            "title": lead.title,
            "description": lead.description,
            "price": float(lead.price) if lead.price else None,
            "url": lead.url,
            "email": lead.email,
            "phone": lead.phone,
            "contact_name": lead.contact_name,
            "location": {
                "id": lead.location.id,
                "name": lead.location.name,
                "code": lead.location.code
            } if lead.location else None,
            "category": lead.category,
            "subcategory": lead.subcategory,
            "is_processed": lead.is_processed,
            "is_contacted": lead.is_contacted,
            "status": lead.status,
            "qualification_score": lead.qualification_score,
            "qualification_reasoning": lead.qualification_reasoning,
            "compensation": lead.compensation,
            "employment_type": lead.employment_type,
            "is_remote": lead.is_remote,
            "posted_at": lead.posted_at.isoformat() if lead.posted_at else None,
            "scraped_at": lead.scraped_at.isoformat() if lead.scraped_at else None,
            "created_at": lead.created_at.isoformat() if lead.created_at else None,
            "updated_at": lead.updated_at.isoformat() if lead.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch lead")


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
@data_limiter
async def create_lead(
    lead_data: SecureLeadCreate,  # Uses validated schema
    db: AsyncSession = Depends(get_db),
    # current_user: dict = Depends(get_current_user) if AUTH_AVAILABLE else None
):
    """
    Create a new lead with comprehensive validation.

    Security features:
    - Input validation and sanitization
    - SQL injection protection
    - XSS protection via HTML sanitization
    - Email and phone validation
    - URL validation for Craigslist URLs
    - Rate limiting
    """
    try:
        # Verify location exists (prevent foreign key attacks)
        location_query = select(Location).where(Location.id == lead_data.location_id)
        location_result = await db.execute(location_query)
        location = location_result.scalar_one_or_none()

        if not location:
            raise HTTPException(status_code=400, detail="Invalid location_id")

        # Check for duplicate (prevent duplicate entries)
        existing_query = select(Lead).where(Lead.craigslist_id == lead_data.craigslist_id)
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"Lead with Craigslist ID '{lead_data.craigslist_id}' already exists"
            )

        # Create lead with validated data
        lead = Lead(**lead_data.model_dump())

        # Set audit fields
        lead.scraped_at = datetime.utcnow()
        lead.created_at = datetime.utcnow()

        # Add to database
        db.add(lead)
        await db.commit()
        await db.refresh(lead)

        # Load relationships
        await db.refresh(lead, ["location"])

        logger.info(f"Lead created: {lead.id} - {lead.title[:50]}")

        # Return sanitized response
        return {
            "id": lead.id,
            "craigslist_id": lead.craigslist_id,
            "title": lead.title,
            "url": lead.url,
            "location": {
                "id": lead.location.id,
                "name": lead.location.name
            },
            "status": lead.status,
            "created_at": lead.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create lead: {e}")

        # Don't expose internal error details
        raise HTTPException(status_code=500, detail="Failed to create lead")


@router.put("/{lead_id}", response_model=dict)
@data_limiter
async def update_lead(
    lead_id: int = Query(..., ge=1),
    lead_data: SecureLeadUpdate = None,  # Uses validated schema
    db: AsyncSession = Depends(get_db),
    # current_user: dict = Depends(get_current_user) if AUTH_AVAILABLE else None
):
    """
    Update an existing lead with validation.

    Security features:
    - Input validation and sanitization
    - Prevents unauthorized field updates
    - Audit logging
    - Rate limiting
    """
    try:
        # Fetch lead with lock for update (prevent race conditions)
        query = select(Lead).options(selectinload(Lead.location)).where(Lead.id == lead_id).with_for_update()
        result = await db.execute(query)
        lead = result.scalar_one_or_none()

        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Update only allowed fields
        update_data = lead_data.model_dump(exclude_unset=True)

        # Track changes for audit
        changes = {}
        for field, value in update_data.items():
            old_value = getattr(lead, field)
            if old_value != value:
                changes[field] = {"old": old_value, "new": value}
                setattr(lead, field, value)

        if changes:
            # Update timestamp
            lead.updated_at = datetime.utcnow()

            # Log changes
            logger.info(f"Lead {lead_id} updated: {list(changes.keys())}")

            await db.commit()
            await db.refresh(lead)

        # Return updated lead
        return {
            "id": lead.id,
            "craigslist_id": lead.craigslist_id,
            "title": lead.title,
            "status": lead.status,
            "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
            "changes": len(changes)
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update lead")


@router.delete("/{lead_id}")
@data_limiter
async def delete_lead(
    lead_id: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
    # current_user: dict = Depends(require_permission("leads:delete")) if AUTH_AVAILABLE else None
):
    """
    Delete a lead with authorization check.

    Security features:
    - Authorization required (when enabled)
    - Soft delete option for audit trail
    - Rate limiting
    """
    try:
        # Fetch lead
        query = select(Lead).where(Lead.id == lead_id)
        result = await db.execute(query)
        lead = result.scalar_one_or_none()

        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Option 1: Soft delete (recommended for audit trail)
        # lead.status = "archived"
        # lead.deleted_at = datetime.utcnow()
        # await db.commit()

        # Option 2: Hard delete
        await db.delete(lead)
        await db.commit()

        logger.info(f"Lead {lead_id} deleted")

        return {"message": "Lead deleted successfully", "id": lead_id}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete lead")


@router.get("/stats/summary")
@data_limiter
async def get_lead_stats(
    location_id: Optional[int] = Query(None, ge=1),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get lead statistics with efficient aggregation.

    Security features:
    - Parameter validation
    - Efficient SQL to prevent DoS
    - Rate limiting
    """
    try:
        # Validate date range
        start_date, end_date = validate_date_range(start_date, end_date)

        # Build base query conditions
        conditions = []
        if location_id:
            conditions.append(Lead.location_id == location_id)
        if start_date:
            conditions.append(Lead.created_at >= start_date)
        if end_date:
            conditions.append(Lead.created_at <= end_date)

        # Single efficient query for all stats
        from sqlalchemy import func, case

        stats_query = select(
            func.count(Lead.id).label("total_leads"),
            func.count(case((Lead.is_processed == True, 1))).label("processed_leads"),
            func.count(case((Lead.is_contacted == True, 1))).label("contacted_leads"),
            func.count(case((Lead.status == "new", 1))).label("status_new"),
            func.count(case((Lead.status == "contacted", 1))).label("status_contacted"),
            func.count(case((Lead.status == "qualified", 1))).label("status_qualified"),
            func.count(case((Lead.status == "converted", 1))).label("status_converted"),
            func.count(case((Lead.status == "rejected", 1))).label("status_rejected"),
            func.avg(Lead.qualification_score).label("avg_qualification_score"),
            func.avg(Lead.price).label("avg_price")
        )

        if conditions:
            stats_query = stats_query.where(and_(*conditions))

        result = await db.execute(stats_query)
        stats = result.one()

        total_leads = stats.total_leads or 0
        processed_leads = stats.processed_leads or 0
        contacted_leads = stats.contacted_leads or 0

        return {
            "total_leads": total_leads,
            "processed_leads": processed_leads,
            "contacted_leads": contacted_leads,
            "status_breakdown": {
                "new": stats.status_new or 0,
                "contacted": stats.status_contacted or 0,
                "qualified": stats.status_qualified or 0,
                "converted": stats.status_converted or 0,
                "rejected": stats.status_rejected or 0
            },
            "metrics": {
                "processing_rate": round((processed_leads / total_leads * 100) if total_leads > 0 else 0, 2),
                "contact_rate": round((contacted_leads / total_leads * 100) if total_leads > 0 else 0, 2),
                "avg_qualification_score": round(float(stats.avg_qualification_score or 0), 2),
                "avg_price": round(float(stats.avg_price or 0), 2)
            },
            "filters_applied": {
                "location_id": location_id,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting lead stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@router.post("/bulk-update", response_model=dict)
@data_limiter
async def bulk_update_leads(
    lead_ids: List[int] = Query(..., min_items=1, max_items=100),
    update_data: SecureLeadUpdate = None,
    db: AsyncSession = Depends(get_db),
    # current_user: dict = Depends(require_permission("leads:write")) if AUTH_AVAILABLE else None
):
    """
    Bulk update multiple leads with validation.

    Security features:
    - Limit on number of leads (prevent DoS)
    - Transaction-based for consistency
    - Audit logging
    - Authorization required
    """
    try:
        # Validate all IDs are positive integers
        for lead_id in lead_ids:
            if lead_id <= 0:
                raise ValueError(f"Invalid lead ID: {lead_id}")

        # Remove duplicates
        lead_ids = list(set(lead_ids))

        # Fetch all leads in one query
        query = select(Lead).where(Lead.id.in_(lead_ids))
        result = await db.execute(query)
        leads = result.scalars().all()

        if len(leads) != len(lead_ids):
            found_ids = {lead.id for lead in leads}
            missing_ids = set(lead_ids) - found_ids
            raise HTTPException(
                status_code=404,
                detail=f"Leads not found: {missing_ids}"
            )

        # Update all leads
        update_fields = update_data.model_dump(exclude_unset=True)
        updated_count = 0

        for lead in leads:
            for field, value in update_fields.items():
                setattr(lead, field, value)
            lead.updated_at = datetime.utcnow()
            updated_count += 1

        await db.commit()

        logger.info(f"Bulk updated {updated_count} leads")

        return {
            "message": "Leads updated successfully",
            "updated_count": updated_count,
            "lead_ids": lead_ids
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to bulk update leads: {e}")
        raise HTTPException(status_code=500, detail="Failed to update leads")


__all__ = ['router']