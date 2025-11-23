"""
API endpoints for response generation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.leads import Lead
from app.models.response_templates import ResponseTemplate
from app.services.response_generator import ResponseGenerator
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    subject: Optional[str] = None
    body: str
    template_type: str = "general"
    communication_method: str = "email"
    required_variables: Optional[List[str]] = None
    optional_variables: Optional[List[str]] = None
    tone: str = "professional"
    length: str = "medium"
    use_ai_enhancement: bool = True
    ai_instructions: Optional[str] = None
    variant_group: Optional[str] = None
    variant_name: Optional[str] = None


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    template_type: Optional[str] = None
    communication_method: Optional[str] = None
    required_variables: Optional[List[str]] = None
    optional_variables: Optional[List[str]] = None
    tone: Optional[str] = None
    length: Optional[str] = None
    use_ai_enhancement: Optional[bool] = None
    ai_instructions: Optional[str] = None
    is_active: Optional[bool] = None


class GenerateResponseRequest(BaseModel):
    lead_id: int
    template_id: Optional[int] = None
    use_ai: bool = True
    custom_variables: Optional[Dict[str, str]] = None


class BatchGenerateRequest(BaseModel):
    lead_ids: List[int]
    template_id: Optional[int] = None
    use_ai: bool = True
    qualification_score_min: Optional[float] = 0.5


class UserProfileUpdate(BaseModel):
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    user_profession: Optional[str] = None
    years_experience: Optional[str] = None
    relevant_skills: Optional[str] = None
    skill_list: Optional[str] = None
    portfolio_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    availability_statement: Optional[str] = None
    hourly_rate: Optional[str] = None
    salary_expectations: Optional[str] = None


# Template CRUD endpoints

@router.post("/templates", response_model=Dict)
async def create_template(
    template: TemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new response template."""
    # Check if name already exists
    query = select(ResponseTemplate).where(ResponseTemplate.name == template.name)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Template with this name already exists")
    
    db_template = ResponseTemplate(
        name=template.name,
        description=template.description,
        subject=template.subject,
        body=template.body,
        template_type=template.template_type,
        communication_method=template.communication_method,
        required_variables=template.required_variables,
        optional_variables=template.optional_variables,
        tone=template.tone,
        length=template.length,
        use_ai_enhancement=template.use_ai_enhancement,
        ai_instructions=template.ai_instructions,
        variant_group=template.variant_group,
        variant_name=template.variant_name
    )
    
    db.add(db_template)
    await db.commit()
    await db.refresh(db_template)
    
    return db_template.to_dict()


@router.get("/templates", response_model=List[Dict])
async def get_templates(
    template_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    variant_group: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all response templates."""
    query = select(ResponseTemplate)
    
    if template_type:
        query = query.where(ResponseTemplate.template_type == template_type)
    if is_active is not None:
        query = query.where(ResponseTemplate.is_active == is_active)
    if variant_group:
        query = query.where(ResponseTemplate.variant_group == variant_group)
    
    query = query.order_by(ResponseTemplate.success_rate.desc().nullsfirst())
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return [t.to_dict() for t in templates]


@router.get("/templates/{template_id}", response_model=Dict)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific template."""
    query = select(ResponseTemplate).where(ResponseTemplate.id == template_id)
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template.to_dict()


@router.put("/templates/{template_id}", response_model=Dict)
async def update_template(
    template_id: int,
    template_update: TemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a template."""
    query = select(ResponseTemplate).where(ResponseTemplate.id == template_id)
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for field, value in template_update.dict(exclude_unset=True).items():
        setattr(template, field, value)
    
    await db.commit()
    await db.refresh(template)
    
    return template.to_dict()


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a template."""
    query = select(ResponseTemplate).where(ResponseTemplate.id == template_id)
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    await db.delete(template)
    await db.commit()
    
    return {"message": "Template deleted successfully"}


# Response generation endpoints

@router.post("/generate")
async def generate_response(
    request: GenerateResponseRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate a personalized response for a lead."""
    # Get lead
    lead_query = select(Lead).where(Lead.id == request.lead_id)
    lead_result = await db.execute(lead_query)
    lead = lead_result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get template if specified
    template = None
    if request.template_id:
        template_query = select(ResponseTemplate).where(
            ResponseTemplate.id == request.template_id
        )
        template_result = await db.execute(template_query)
        template = template_result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
    
    # Generate response
    generator = ResponseGenerator(db)
    await generator.load_user_profile()
    
    try:
        subject, body, metadata = await generator.generate_response(
            lead,
            template,
            use_ai=request.use_ai,
            custom_variables=request.custom_variables
        )
        
        # Save to lead's generated responses
        if not lead.generated_responses:
            lead.generated_responses = []
        
        response_data = {
            'subject': subject,
            'body': body,
            'metadata': metadata,
            'generated_at': datetime.now().isoformat()
        }
        
        lead.generated_responses.append(response_data)
        await db.commit()
        
        return {
            'lead_id': lead.id,
            'craigslist_id': lead.craigslist_id,
            'lead_title': lead.title,
            'response': {
                'subject': subject,
                'body': body
            },
            'metadata': metadata
        }
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/batch")
async def generate_batch_responses(
    request: BatchGenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate responses for multiple leads."""
    # Get leads
    query = select(Lead).where(Lead.id.in_(request.lead_ids))
    
    # Filter by qualification score if specified
    if request.qualification_score_min:
        query = query.where(Lead.qualification_score >= request.qualification_score_min)
    
    result = await db.execute(query)
    leads = result.scalars().all()
    
    if not leads:
        raise HTTPException(status_code=404, detail="No leads found")
    
    # Get template if specified
    template = None
    if request.template_id:
        template_query = select(ResponseTemplate).where(
            ResponseTemplate.id == request.template_id
        )
        template_result = await db.execute(template_query)
        template = template_result.scalar_one_or_none()
    
    # Generate responses
    generator = ResponseGenerator(db)
    await generator.load_user_profile()
    
    results = await generator.batch_generate_responses(
        leads,
        template,
        use_ai=request.use_ai
    )
    
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    return {
        'total_processed': len(results),
        'successful': len(successful),
        'failed': len(failed),
        'results': results
    }


@router.post("/templates/{template_id}/test")
async def test_template(
    template_id: int,
    lead_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Test a template with sample data."""
    # Get template
    template_query = select(ResponseTemplate).where(ResponseTemplate.id == template_id)
    template_result = await db.execute(template_query)
    template = template_result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Get lead if specified
    sample_lead = None
    if lead_id:
        lead_query = select(Lead).where(Lead.id == lead_id)
        lead_result = await db.execute(lead_query)
        sample_lead = lead_result.scalar_one_or_none()
    
    # Test template
    generator = ResponseGenerator(db)
    await generator.load_user_profile()
    
    result = await generator.test_template(template, sample_lead)
    return result


@router.get("/user-profile")
async def get_user_profile(db: AsyncSession = Depends(get_db)):
    """Get the current user profile used for response generation."""
    generator = ResponseGenerator(db)
    profile = await generator.load_user_profile()
    return profile


@router.put("/user-profile")
async def update_user_profile(
    profile_update: UserProfileUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update the user profile (in production, this would save to database)."""
    # In production, this would save to database
    # For now, just return the update
    return {
        "message": "Profile update received",
        "updated_fields": list(profile_update.dict(exclude_unset=True).keys())
    }


@router.get("/leads/{lead_id}/responses")
async def get_lead_responses(
    lead_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all generated responses for a lead."""
    query = select(Lead).where(Lead.id == lead_id)
    result = await db.execute(query)
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {
        'lead_id': lead.id,
        'craigslist_id': lead.craigslist_id,
        'lead_title': lead.title,
        'responses': lead.generated_responses or [],
        'total_responses': len(lead.generated_responses) if lead.generated_responses else 0
    }