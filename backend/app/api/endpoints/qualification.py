"""
API endpoints for lead qualification.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.leads import Lead
from app.models.qualification_criteria import QualificationCriteria
from app.services.lead_qualifier import LeadQualifier
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class QualificationCriteriaCreate(BaseModel):
    name: str
    description: Optional[str] = None
    
    # Keywords
    required_keywords: Optional[List[str]] = None
    preferred_keywords: Optional[List[str]] = None
    excluded_keywords: Optional[List[str]] = None
    
    # Compensation
    min_compensation: Optional[float] = None
    max_compensation: Optional[float] = None
    compensation_type: Optional[str] = None
    
    # Location
    preferred_locations: Optional[List] = None
    max_distance_miles: Optional[float] = None
    remote_acceptable: bool = True
    
    # Employment
    preferred_employment_types: Optional[List[str]] = None
    internship_acceptable: bool = True
    nonprofit_acceptable: bool = True
    
    # Weights
    keyword_weight: float = 0.3
    compensation_weight: float = 0.2
    location_weight: float = 0.2
    employment_type_weight: float = 0.15
    freshness_weight: float = 0.15
    
    # Thresholds
    min_score_threshold: float = 0.5
    auto_qualify_threshold: float = 0.8
    auto_reject_threshold: float = 0.2
    
    # Requirements
    max_days_old: int = 7
    require_contact_info: bool = False
    require_compensation_info: bool = False
    
    # Custom rules
    custom_rules: Optional[dict] = None


class QualificationCriteriaResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    keywords: dict
    compensation: dict
    location: dict
    employment: dict
    weights: dict
    thresholds: dict
    requirements: dict
    custom_rules: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime


class QualifyLeadsRequest(BaseModel):
    lead_ids: Optional[List[int]] = None
    criteria_id: int
    update_database: bool = True
    use_ai: bool = False


class QualificationResult(BaseModel):
    lead_id: int
    craigslist_id: str
    title: str
    score: float
    status: str
    reasoning: str
    detailed_scores: dict


@router.post("/criteria", response_model=QualificationCriteriaResponse)
async def create_qualification_criteria(
    criteria: QualificationCriteriaCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new qualification criteria."""
    # Check if name already exists
    query = select(QualificationCriteria).where(QualificationCriteria.name == criteria.name)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Criteria with this name already exists")
    
    # Create new criteria
    db_criteria = QualificationCriteria(
        name=criteria.name,
        description=criteria.description,
        required_keywords=criteria.required_keywords,
        preferred_keywords=criteria.preferred_keywords,
        excluded_keywords=criteria.excluded_keywords,
        min_compensation=criteria.min_compensation,
        max_compensation=criteria.max_compensation,
        compensation_type=criteria.compensation_type,
        preferred_locations=criteria.preferred_locations,
        max_distance_miles=criteria.max_distance_miles,
        remote_acceptable=criteria.remote_acceptable,
        preferred_employment_types=criteria.preferred_employment_types,
        internship_acceptable=criteria.internship_acceptable,
        nonprofit_acceptable=criteria.nonprofit_acceptable,
        keyword_weight=criteria.keyword_weight,
        compensation_weight=criteria.compensation_weight,
        location_weight=criteria.location_weight,
        employment_type_weight=criteria.employment_type_weight,
        freshness_weight=criteria.freshness_weight,
        min_score_threshold=criteria.min_score_threshold,
        auto_qualify_threshold=criteria.auto_qualify_threshold,
        auto_reject_threshold=criteria.auto_reject_threshold,
        max_days_old=criteria.max_days_old,
        require_contact_info=criteria.require_contact_info,
        require_compensation_info=criteria.require_compensation_info,
        custom_rules=criteria.custom_rules
    )
    
    db.add(db_criteria)
    await db.commit()
    await db.refresh(db_criteria)
    
    return db_criteria.to_dict()


@router.get("/criteria", response_model=List[QualificationCriteriaResponse])
async def get_qualification_criteria(
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all qualification criteria."""
    query = select(QualificationCriteria)
    if is_active is not None:
        query = query.where(QualificationCriteria.is_active == is_active)
    
    result = await db.execute(query)
    criteria_list = result.scalars().all()
    
    return [c.to_dict() for c in criteria_list]


@router.get("/criteria/{criteria_id}", response_model=QualificationCriteriaResponse)
async def get_qualification_criteria_by_id(
    criteria_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get specific qualification criteria."""
    query = select(QualificationCriteria).where(QualificationCriteria.id == criteria_id)
    result = await db.execute(query)
    criteria = result.scalar_one_or_none()
    
    if not criteria:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    return criteria.to_dict()


@router.put("/criteria/{criteria_id}", response_model=QualificationCriteriaResponse)
async def update_qualification_criteria(
    criteria_id: int,
    criteria_update: QualificationCriteriaCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update qualification criteria."""
    query = select(QualificationCriteria).where(QualificationCriteria.id == criteria_id)
    result = await db.execute(query)
    criteria = result.scalar_one_or_none()
    
    if not criteria:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    # Update fields
    for field, value in criteria_update.dict(exclude_unset=True).items():
        setattr(criteria, field, value)
    
    await db.commit()
    await db.refresh(criteria)
    
    return criteria.to_dict()


@router.delete("/criteria/{criteria_id}")
async def delete_qualification_criteria(
    criteria_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete qualification criteria."""
    query = select(QualificationCriteria).where(QualificationCriteria.id == criteria_id)
    result = await db.execute(query)
    criteria = result.scalar_one_or_none()
    
    if not criteria:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    await db.delete(criteria)
    await db.commit()
    
    return {"message": "Criteria deleted successfully"}


@router.post("/qualify", response_model=List[QualificationResult])
async def qualify_leads(
    request: QualifyLeadsRequest,
    db: AsyncSession = Depends(get_db)
):
    """Qualify leads based on criteria."""
    # Get criteria
    criteria_query = select(QualificationCriteria).where(
        QualificationCriteria.id == request.criteria_id
    )
    criteria_result = await db.execute(criteria_query)
    criteria = criteria_result.scalar_one_or_none()
    
    if not criteria:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    # Get leads
    if request.lead_ids:
        leads_query = select(Lead).where(Lead.id.in_(request.lead_ids))
    else:
        # Get all unqualified leads
        leads_query = select(Lead).where(Lead.has_been_qualified == False).limit(100)
    
    leads_result = await db.execute(leads_query)
    leads = leads_result.scalars().all()
    
    if not leads:
        raise HTTPException(status_code=404, detail="No leads found to qualify")
    
    # Qualify leads
    qualifier = LeadQualifier(db)
    results = await qualifier.batch_qualify_leads(
        leads,
        criteria,
        update_database=request.update_database
    )
    
    return results


@router.get("/qualify/{lead_id}", response_model=QualificationResult)
async def qualify_single_lead(
    lead_id: int,
    criteria_id: int,
    use_ai: bool = Query(False),
    update_database: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """Qualify a single lead."""
    # Get lead
    lead_query = select(Lead).where(Lead.id == lead_id)
    lead_result = await db.execute(lead_query)
    lead = lead_result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get criteria
    criteria_query = select(QualificationCriteria).where(
        QualificationCriteria.id == criteria_id
    )
    criteria_result = await db.execute(criteria_query)
    criteria = criteria_result.scalar_one_or_none()
    
    if not criteria:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    # Qualify lead
    qualifier = LeadQualifier(db)
    score, reasoning, detailed = await qualifier.qualify_lead(lead, criteria, use_ai)
    
    if update_database:
        lead.qualification_score = score
        lead.qualification_reasoning = reasoning
        lead.has_been_qualified = True
        lead.qualified_at = datetime.now()
        
        # Update status
        if score >= criteria.auto_qualify_threshold:
            lead.status = 'qualified'
        elif score <= criteria.auto_reject_threshold:
            lead.status = 'rejected'
        else:
            lead.status = 'review'
        
        await db.commit()
    
    return {
        'lead_id': lead.id,
        'craigslist_id': lead.craigslist_id,
        'title': lead.title,
        'score': score,
        'status': lead.status,
        'reasoning': reasoning,
        'detailed_scores': detailed
    }


@router.get("/stats")
async def get_qualification_stats(
    criteria_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get qualification statistics."""
    qualifier = LeadQualifier(db)
    stats = await qualifier.get_qualification_stats(criteria_id)
    return stats


@router.get("/qualified-leads")
async def get_qualified_leads(
    min_score: Optional[float] = Query(0.5),
    status: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db)
):
    """Get qualified leads sorted by score."""
    query = select(Lead).where(Lead.has_been_qualified == True)
    
    if min_score:
        query = query.where(Lead.qualification_score >= min_score)
    
    if status:
        query = query.where(Lead.status == status)
    
    query = query.order_by(Lead.qualification_score.desc())
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    leads = result.scalars().all()
    
    return [
        {
            'id': lead.id,
            'craigslist_id': lead.craigslist_id,
            'title': lead.title,
            'url': lead.url,
            'score': lead.qualification_score,
            'status': lead.status,
            'reasoning': lead.qualification_reasoning,
            'qualified_at': lead.qualified_at.isoformat() if lead.qualified_at else None,
            'location': lead.location.name if lead.location else None,
            'compensation': lead.compensation,
            'is_remote': lead.is_remote
        }
        for lead in leads
    ]