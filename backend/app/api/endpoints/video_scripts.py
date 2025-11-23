"""
Video Scripts API Endpoints - Phase 4, Task 1

REST API for managing AI-generated video scripts.
Supports script generation, retrieval, section regeneration, and deletion.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
import structlog

from app.core.database import get_db
from app.models.video_scripts import VideoScript
from app.models.demo_sites import DemoSite
from app.models.leads import Lead
from app.services.video.script_generator import (
    ScriptGenerator,
    ScriptStyle,
    ScriptSection as ServiceScriptSection,
    VideoScript as ServiceVideoScript
)
from app.services.ai_mvp.ai_council import AICouncil, AICouncilConfig
from app.services.ai_mvp.ai_gym_tracker import AIGymTracker
from app.core.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter()


# Pydantic models for API requests/responses
class ScriptGenerationRequest(BaseModel):
    """Request to generate a new video script."""
    demo_site_id: int = Field(..., description="Demo site ID")
    lead_id: int = Field(..., description="Lead ID")
    style: str = Field(default="professional", description="Script style (professional, casual, technical, sales)")
    max_duration_seconds: int = Field(default=120, ge=30, le=300, description="Maximum video duration in seconds")
    include_intro: bool = Field(default=True, description="Include intro section")
    include_cta: bool = Field(default=True, description="Include call-to-action section")
    custom_instructions: Optional[str] = Field(None, description="Custom instructions for script generation")


class SectionRegenerationRequest(BaseModel):
    """Request to regenerate a specific section."""
    section_index: int = Field(..., ge=0, description="Index of section to regenerate (0-based)")
    instructions: str = Field(..., description="Instructions for regeneration")


class ScriptApprovalRequest(BaseModel):
    """Request to approve or reject a script."""
    is_approved: str = Field(..., description="Approval status (approved, rejected, needs_revision)")
    approved_by: str = Field(..., description="Name/email of approver")
    approval_notes: Optional[str] = Field(None, description="Approval notes or feedback")


class ScriptResponse(BaseModel):
    """Response containing video script data."""
    id: int
    demo_site_id: int
    lead_id: int
    script_style: str
    sections: List[dict]
    total_duration_seconds: int
    target_audience: Optional[str]
    key_messages: List[str]
    ai_generation: dict
    metadata: dict
    validation: dict
    version: int
    parent_script_id: Optional[int]
    video: dict
    usage: dict
    timestamps: dict
    flags: dict

    class Config:
        from_attributes = True


class ScriptSummaryResponse(BaseModel):
    """Brief summary of a video script."""
    id: int
    lead_id: int
    demo_site_id: int
    style: str
    duration: int
    sections_count: int
    is_approved: str
    video_status: str
    created_at: str

    class Config:
        from_attributes = True


# Helper functions
def get_ai_council() -> AICouncil:
    """Get AI Council instance."""
    config = AICouncilConfig(
        openrouter_api_key=settings.OPENROUTER_API_KEY,
        default_temperature=0.7,
        default_max_tokens=3000,
        timeout_seconds=60
    )
    gym_tracker = AIGymTracker()  # Initialize tracker
    return AICouncil(config=config, gym_tracker=gym_tracker)


def get_script_generator() -> ScriptGenerator:
    """Get ScriptGenerator instance."""
    ai_council = get_ai_council()
    return ScriptGenerator(ai_council=ai_council)


# API Endpoints
@router.post("/generate", response_model=ScriptResponse, status_code=status.HTTP_201_CREATED)
async def generate_script(
    request: ScriptGenerationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a new video script from improvement plan.

    Analyzes the demo site's improvement plan and generates a personalized
    video script tailored to the lead's industry and business.

    **Performance**: ~10-15 seconds average
    **Cost**: $0.005-$0.01 per script (AI-GYM optimized)
    """
    logger.info(
        "video_scripts.generate_requested",
        demo_site_id=request.demo_site_id,
        lead_id=request.lead_id,
        style=request.style
    )

    # Validate style
    try:
        script_style = ScriptStyle(request.style.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid script style. Must be one of: professional, casual, technical, sales"
        )

    # Fetch demo site with lead
    result = await db.execute(
        select(DemoSite)
        .options(selectinload(DemoSite.lead))
        .where(DemoSite.id == request.demo_site_id)
    )
    demo_site = result.scalar_one_or_none()

    if not demo_site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo site {request.demo_site_id} not found"
        )

    if demo_site.lead_id != request.lead_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Demo site {request.demo_site_id} does not belong to lead {request.lead_id}"
        )

    # Fetch lead
    lead_result = await db.execute(
        select(Lead).where(Lead.id == request.lead_id)
    )
    lead = lead_result.scalar_one_or_none()

    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {request.lead_id} not found"
        )

    # Extract improvement plan from demo site metadata
    improvement_plan = demo_site.build_metadata or {}
    if not improvement_plan.get("improvements"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Demo site has no improvement plan. Generate improvements first."
        )

    # Prepare lead info
    lead_info = {
        "id": lead.id,
        "company_name": lead.company_name or lead.title,
        "title": lead.title,
        "url": lead.url,
        "category": lead.category,
        "industry": lead.category,  # Use category as industry
        "value": 10000.0  # Default lead value, could be enhanced
    }

    # Generate script
    try:
        generator = get_script_generator()

        script_result: ServiceVideoScript = await generator.generate_script(
            improvement_plan=improvement_plan,
            demo_site_url=demo_site.url or demo_site.preview_url or "demo-site.vercel.app",
            lead_info=lead_info,
            style=script_style,
            max_duration_seconds=request.max_duration_seconds,
            include_intro=request.include_intro,
            include_cta=request.include_cta,
            custom_instructions=request.custom_instructions
        )

        # Validate script timing
        validation = generator.validate_script_timing(script_result)

        # Convert sections to dict for storage
        sections_dict = [section.model_dump() for section in script_result.sections]

        # Create database record
        video_script = VideoScript(
            demo_site_id=demo_site.id,
            lead_id=lead.id,
            script_style=script_result.script_style,
            sections=sections_dict,
            total_duration_seconds=script_result.total_duration_seconds,
            target_audience=script_result.target_audience,
            key_messages=script_result.key_messages,
            ai_model_used=script_result.metadata.get("ai_model"),
            ai_cost=script_result.metadata.get("ai_cost"),
            prompt_tokens=script_result.metadata.get("prompt_tokens"),
            completion_tokens=script_result.metadata.get("completion_tokens"),
            generation_time_seconds=script_result.metadata.get("generation_time_seconds"),
            metadata=script_result.metadata,
            validation_warnings=validation.get("warnings", []),
            is_approved="pending",
            version=1
        )

        db.add(video_script)
        await db.commit()
        await db.refresh(video_script)

        logger.info(
            "video_scripts.generated",
            script_id=video_script.id,
            demo_site_id=demo_site.id,
            lead_id=lead.id,
            duration=video_script.total_duration_seconds,
            cost=video_script.ai_cost
        )

        return ScriptResponse(**video_script.to_dict())

    except Exception as e:
        logger.error(
            "video_scripts.generation_failed",
            demo_site_id=request.demo_site_id,
            lead_id=request.lead_id,
            error=str(e)
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Script generation failed: {str(e)}"
        )


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get video script by ID.

    Returns complete script with all sections and metadata.
    """
    result = await db.execute(
        select(VideoScript).where(
            and_(
                VideoScript.id == script_id,
                VideoScript.is_deleted == "false"
            )
        )
    )
    script = result.scalar_one_or_none()

    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video script {script_id} not found"
        )

    # Increment view count
    script.times_viewed += 1
    from datetime import datetime
    script.last_viewed_at = datetime.utcnow()
    await db.commit()

    return ScriptResponse(**script.to_dict())


@router.get("/demo/{demo_id}", response_model=List[ScriptSummaryResponse])
async def get_scripts_for_demo(
    demo_id: int,
    include_deleted: bool = Query(False, description="Include deleted scripts"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all scripts for a specific demo site.

    Returns list of script summaries ordered by creation date (newest first).
    """
    query = select(VideoScript).where(VideoScript.demo_site_id == demo_id)

    if not include_deleted:
        query = query.where(VideoScript.is_deleted == "false")

    query = query.order_by(desc(VideoScript.created_at))

    result = await db.execute(query)
    scripts = result.scalars().all()

    return [ScriptSummaryResponse(**script.get_script_summary()) for script in scripts]


@router.put("/{script_id}/section/{section_index}", response_model=ScriptResponse)
async def regenerate_section(
    script_id: int,
    section_index: int,
    request: SectionRegenerationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Regenerate a specific section of the script.

    Useful for iterative refinement when a section needs adjustment.
    Creates a new version of the script with the regenerated section.
    """
    # Fetch original script
    result = await db.execute(
        select(VideoScript).where(
            and_(
                VideoScript.id == script_id,
                VideoScript.is_deleted == "false"
            )
        )
    )
    original_script = result.scalar_one_or_none()

    if not original_script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video script {script_id} not found"
        )

    # Validate section index
    if section_index >= len(original_script.sections):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid section index {section_index}. Script has {len(original_script.sections)} sections."
        )

    try:
        # Convert to service model
        service_script = ServiceVideoScript(
            sections=[
                ServiceScriptSection(**section)
                for section in original_script.sections
            ],
            total_duration_seconds=original_script.total_duration_seconds,
            script_style=original_script.script_style,
            target_audience=original_script.target_audience or "",
            key_messages=original_script.key_messages or [],
            metadata=original_script.metadata or {}
        )

        # Regenerate section
        generator = get_script_generator()
        new_section = await generator.regenerate_section(
            script=service_script,
            section_index=section_index,
            new_instructions=request.instructions,
            lead_value=10000.0  # Default
        )

        # Update sections
        updated_sections = [
            ServiceScriptSection(**section)
            for section in original_script.sections
        ]
        updated_sections[section_index] = new_section

        # Recalculate total duration
        new_total_duration = sum(s.duration_seconds for s in updated_sections)

        # Create new version
        new_script = VideoScript(
            demo_site_id=original_script.demo_site_id,
            lead_id=original_script.lead_id,
            script_style=original_script.script_style,
            sections=[s.model_dump() for s in updated_sections],
            total_duration_seconds=new_total_duration,
            target_audience=original_script.target_audience,
            key_messages=original_script.key_messages,
            ai_model_used=original_script.ai_model_used,
            ai_cost=original_script.ai_cost,
            metadata={
                **original_script.metadata,
                "regenerated_section": section_index,
                "regeneration_instructions": request.instructions
            },
            validation_warnings=[],
            is_approved="pending",
            version=original_script.version + 1,
            parent_script_id=original_script.id
        )

        db.add(new_script)
        await db.commit()
        await db.refresh(new_script)

        logger.info(
            "video_scripts.section_regenerated",
            original_script_id=script_id,
            new_script_id=new_script.id,
            section_index=section_index
        )

        return ScriptResponse(**new_script.to_dict())

    except Exception as e:
        logger.error(
            "video_scripts.regeneration_failed",
            script_id=script_id,
            section_index=section_index,
            error=str(e)
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Section regeneration failed: {str(e)}"
        )


@router.put("/{script_id}/approve", response_model=ScriptResponse)
async def approve_script(
    script_id: int,
    request: ScriptApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Approve or reject a video script.

    Updates the approval status and records who approved it.
    """
    result = await db.execute(
        select(VideoScript).where(
            and_(
                VideoScript.id == script_id,
                VideoScript.is_deleted == "false"
            )
        )
    )
    script = result.scalar_one_or_none()

    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video script {script_id} not found"
        )

    # Validate approval status
    if request.is_approved not in ["approved", "rejected", "needs_revision"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="is_approved must be one of: approved, rejected, needs_revision"
        )

    # Update approval
    script.is_approved = request.is_approved
    script.approved_by = request.approved_by
    from datetime import datetime
    script.approved_at = datetime.utcnow()
    script.approval_notes = request.approval_notes

    await db.commit()
    await db.refresh(script)

    logger.info(
        "video_scripts.approval_updated",
        script_id=script_id,
        status=request.is_approved,
        approved_by=request.approved_by
    )

    return ScriptResponse(**script.to_dict())


@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_script(
    script_id: int,
    hard_delete: bool = Query(False, description="Permanently delete (vs soft delete)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a video script.

    By default performs soft delete. Use hard_delete=true to permanently remove.
    """
    result = await db.execute(
        select(VideoScript).where(VideoScript.id == script_id)
    )
    script = result.scalar_one_or_none()

    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video script {script_id} not found"
        )

    if hard_delete:
        await db.delete(script)
        logger.info("video_scripts.hard_deleted", script_id=script_id)
    else:
        from datetime import datetime
        script.is_deleted = "true"
        script.deleted_at = datetime.utcnow()
        script.is_active = "inactive"
        logger.info("video_scripts.soft_deleted", script_id=script_id)

    await db.commit()

    return None


@router.get("/", response_model=List[ScriptSummaryResponse])
async def list_scripts(
    lead_id: Optional[int] = Query(None, description="Filter by lead ID"),
    style: Optional[str] = Query(None, description="Filter by script style"),
    is_approved: Optional[str] = Query(None, description="Filter by approval status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db)
):
    """
    List video scripts with optional filtering.

    Returns paginated list of script summaries.
    """
    query = select(VideoScript).where(VideoScript.is_deleted == "false")

    if lead_id:
        query = query.where(VideoScript.lead_id == lead_id)

    if style:
        query = query.where(VideoScript.script_style == style.lower())

    if is_approved:
        query = query.where(VideoScript.is_approved == is_approved)

    query = query.order_by(desc(VideoScript.created_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    scripts = result.scalars().all()

    return [ScriptSummaryResponse(**script.get_script_summary()) for script in scripts]
