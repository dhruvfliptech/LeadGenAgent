"""
Lead endpoints for managing scraped leads.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.leads import Lead
from app.models.locations import Location
from pydantic import BaseModel


class LeadCreate(BaseModel):
    craigslist_id: str
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    url: str
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_name: Optional[str] = None
    location_id: int
    category: Optional[str] = None
    subcategory: Optional[str] = None
    posted_at: Optional[datetime] = None


class LeadUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    is_processed: Optional[bool] = None
    is_contacted: Optional[bool] = None
    status: Optional[str] = None

    # AI MVP fields
    ai_analysis: Optional[str] = None
    ai_model: Optional[str] = None
    ai_cost: Optional[float] = None
    ai_request_id: Optional[int] = None
    generated_email_subject: Optional[str] = None
    generated_email_body: Optional[str] = None


class LocationInfo(BaseModel):
    id: int
    name: str
    code: str
    
    class Config:
        from_attributes = True


class LeadResponse(BaseModel):
    id: int
    craigslist_id: str
    title: str
    description: Optional[str]
    price: Optional[float]
    url: str
    email: Optional[str]
    phone: Optional[str]
    contact_name: Optional[str]
    compensation: Optional[str]
    employment_type: Optional[List[str]]
    is_remote: Optional[bool]
    reply_email: Optional[str]
    reply_phone: Optional[str]
    location: LocationInfo
    category: Optional[str]
    subcategory: Optional[str]
    source: Optional[str] = "craigslist"  # Source of the lead (craigslist, google_maps, linkedin, etc.)
    is_processed: bool
    is_contacted: bool
    status: str
    qualification_score: Optional[float]
    qualification_reasoning: Optional[str]
    posted_at: Optional[datetime]
    scraped_at: datetime
    created_at: datetime
    updated_at: datetime

    # AI MVP fields
    ai_analysis: Optional[str] = None
    ai_model: Optional[str] = None
    ai_cost: Optional[float] = None
    ai_request_id: Optional[int] = None
    generated_email_subject: Optional[str] = None
    generated_email_body: Optional[str] = None

    class Config:
        from_attributes = True


router = APIRouter()


@router.get("/", response_model=List[LeadResponse])
async def get_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    location_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    is_processed: Optional[bool] = Query(None),
    is_contacted: Optional[bool] = Query(None),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get list of leads with optional filtering."""
    query = select(Lead).options(selectinload(Lead.location))
    
    # Apply filters
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
        conditions.append(Lead.category == category)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.offset(skip).limit(limit).order_by(desc(Lead.scraped_at))
    
    result = await db.execute(query)
    leads = result.scalars().all()
    
    return leads


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific lead by ID."""
    query = select(Lead).options(selectinload(Lead.location)).where(Lead.id == lead_id)
    result = await db.execute(query)
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return lead


@router.post("/", response_model=LeadResponse)
async def create_lead(lead_data: LeadCreate, db: AsyncSession = Depends(get_db)):
    """Create a new lead."""
    try:
        # Verify location exists first
        location_query = select(Location).where(Location.id == lead_data.location_id)
        location_result = await db.execute(location_query)
        location = location_result.scalar_one_or_none()

        if not location:
            raise HTTPException(status_code=400, detail="Invalid location_id")

        # Create lead - database constraint will prevent duplicates
        lead = Lead(**lead_data.model_dump())
        db.add(lead)
        await db.commit()
        await db.refresh(lead)

        # Load the location relationship
        await db.refresh(lead, ["location"])

        return lead

    except Exception as e:
        await db.rollback()
        # Check if it's a duplicate key error
        if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=409,
                detail=f"Lead with Craigslist ID '{lead_data.craigslist_id}' already exists"
            )
        raise HTTPException(status_code=500, detail=f"Failed to create lead: {str(e)}")


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    lead_data: LeadUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing lead."""
    query = select(Lead).options(selectinload(Lead.location)).where(Lead.id == lead_id)
    result = await db.execute(query)
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Update fields
    update_data = lead_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lead, field, value)
    
    await db.commit()
    await db.refresh(lead)
    
    return lead


@router.delete("/{lead_id}")
async def delete_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a lead."""
    query = select(Lead).where(Lead.id == lead_id)
    result = await db.execute(query)
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    await db.delete(lead)
    await db.commit()
    
    return {"message": "Lead deleted successfully"}


@router.get("/stats/summary")
async def get_lead_stats(db: AsyncSession = Depends(get_db)):
    """Get lead statistics summary using efficient SQL aggregation."""
    from sqlalchemy import func, case

    # Single query to get all stats using COUNT with FILTER (more efficient)
    stats_query = select(
        func.count(Lead.id).label("total_leads"),
        func.count(case((Lead.is_processed == True, 1))).label("processed_leads"),
        func.count(case((Lead.is_contacted == True, 1))).label("contacted_leads"),
        func.count(case((Lead.status == "new", 1))).label("status_new"),
        func.count(case((Lead.status == "contacted", 1))).label("status_contacted"),
        func.count(case((Lead.status == "qualified", 1))).label("status_qualified"),
        func.count(case((Lead.status == "converted", 1))).label("status_converted"),
        func.count(case((Lead.status == "rejected", 1))).label("status_rejected"),
    )

    result = await db.execute(stats_query)
    stats = result.one()

    total_leads = stats.total_leads
    processed_leads = stats.processed_leads
    contacted_leads = stats.contacted_leads

    return {
        "total_leads": total_leads,
        "processed_leads": processed_leads,
        "contacted_leads": contacted_leads,
        "status_breakdown": {
            "new": stats.status_new,
            "contacted": stats.status_contacted,
            "qualified": stats.status_qualified,
            "converted": stats.status_converted,
            "rejected": stats.status_rejected
        },
        "processing_rate": round((processed_leads / total_leads * 100) if total_leads > 0 else 0, 2),
        "contact_rate": round((contacted_leads / total_leads * 100) if total_leads > 0 else 0, 2)
    }