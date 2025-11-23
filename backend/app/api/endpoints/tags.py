"""
Tags API endpoints for managing lead tags.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.core.database import get_db
from app.models.tags import Tag, LeadTag
from app.models.leads import Lead
from app.schemas.tags import (
    TagCreate, TagUpdate, TagResponse, LeadTagResponse,
    AddTagRequest, AddTagByNameRequest, TagListResponse
)


router = APIRouter()


# ============================================================================
# TAG MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/", response_model=TagListResponse)
async def get_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all tags with optional filtering and search."""
    query = select(Tag)

    # Apply filters
    conditions = []
    if category:
        conditions.append(Tag.category == category)
    if search:
        conditions.append(Tag.name.ilike(f"%{search}%"))

    if conditions:
        query = query.where(and_(*conditions))

    # Get total count
    count_query = select(func.count(Tag.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Get paginated results
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    tags = result.scalars().all()

    page = skip // limit if limit > 0 else 0

    return TagListResponse(
        tags=tags,
        total=total,
        page=page,
        page_size=limit
    )


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific tag by ID."""
    query = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(query)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    return tag


@router.post("/", response_model=TagResponse)
async def create_tag(
    tag_data: TagCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new tag."""
    try:
        # Check if tag with same name already exists
        existing = await db.execute(
            select(Tag).where(Tag.name.ilike(tag_data.name))
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"Tag with name '{tag_data.name}' already exists"
            )

        tag = Tag(**tag_data.model_dump())
        db.add(tag)
        await db.commit()
        await db.refresh(tag)

        return tag

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create tag: {str(e)}")


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int = Path(..., gt=0),
    tag_data: TagUpdate = None,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing tag."""
    query = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(query)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    try:
        # Update fields
        update_data = tag_data.model_dump(exclude_unset=True)

        # Check if updating name to one that already exists
        if "name" in update_data and update_data["name"]:
            existing = await db.execute(
                select(Tag).where(
                    and_(
                        Tag.name.ilike(update_data["name"]),
                        Tag.id != tag_id
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=409,
                    detail=f"Tag with name '{update_data['name']}' already exists"
                )

        for field, value in update_data.items():
            setattr(tag, field, value)

        await db.commit()
        await db.refresh(tag)

        return tag

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update tag: {str(e)}")


@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db)
):
    """Delete a tag."""
    query = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(query)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    try:
        # Delete all lead-tag relationships first
        await db.execute(
            delete(LeadTag).where(LeadTag.tag_id == tag_id)
        )

        # Delete the tag
        await db.delete(tag)
        await db.commit()

        return {"message": "Tag deleted successfully"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete tag: {str(e)}")


# ============================================================================
# LEAD TAG ASSOCIATION ENDPOINTS
# ============================================================================

@router.get("/{lead_id}/tags", response_model=List[LeadTagResponse])
async def get_lead_tags(
    lead_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db)
):
    """Get all tags associated with a lead."""
    # Verify lead exists
    lead_check = await db.execute(
        select(Lead).where(Lead.id == lead_id)
    )
    if not lead_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lead not found")

    # Get tags
    query = select(LeadTag).options(selectinload(LeadTag.tag)).where(LeadTag.lead_id == lead_id)
    result = await db.execute(query)
    lead_tags = result.scalars().all()

    return lead_tags


@router.post("/{lead_id}/tags", response_model=LeadTagResponse)
async def add_tag_to_lead(
    lead_id: int = Path(..., gt=0),
    tag_request: AddTagRequest = None,
    db: AsyncSession = Depends(get_db)
):
    """Add a tag to a lead."""
    try:
        # Verify lead exists
        lead_check = await db.execute(
            select(Lead).where(Lead.id == lead_id)
        )
        if not lead_check.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Lead not found")

        # Verify tag exists
        tag_check = await db.execute(
            select(Tag).where(Tag.id == tag_request.tag_id)
        )
        if not tag_check.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Tag not found")

        # Check if association already exists
        existing = await db.execute(
            select(LeadTag).where(
                and_(
                    LeadTag.lead_id == lead_id,
                    LeadTag.tag_id == tag_request.tag_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="This tag is already associated with this lead"
            )

        # Create association
        lead_tag = LeadTag(lead_id=lead_id, tag_id=tag_request.tag_id)
        db.add(lead_tag)
        await db.commit()
        await db.refresh(lead_tag, ["tag"])

        return lead_tag

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add tag to lead: {str(e)}")


@router.post("/{lead_id}/tags/by-name", response_model=LeadTagResponse)
async def add_tag_to_lead_by_name(
    lead_id: int = Path(..., gt=0),
    tag_request: AddTagByNameRequest = None,
    db: AsyncSession = Depends(get_db)
):
    """Add a tag to a lead by tag name (creates tag if it doesn't exist)."""
    try:
        # Verify lead exists
        lead_check = await db.execute(
            select(Lead).where(Lead.id == lead_id)
        )
        if not lead_check.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Lead not found")

        # Find or create tag
        tag_query = await db.execute(
            select(Tag).where(Tag.name.ilike(tag_request.name))
        )
        tag = tag_query.scalar_one_or_none()

        if not tag:
            tag = Tag(
                name=tag_request.name,
                color=tag_request.color,
                category=tag_request.category
            )
            db.add(tag)
            await db.flush()

        # Check if association already exists
        existing = await db.execute(
            select(LeadTag).where(
                and_(
                    LeadTag.lead_id == lead_id,
                    LeadTag.tag_id == tag.id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="This tag is already associated with this lead"
            )

        # Create association
        lead_tag = LeadTag(lead_id=lead_id, tag_id=tag.id)
        db.add(lead_tag)
        await db.commit()
        await db.refresh(lead_tag, ["tag"])

        return lead_tag

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add tag to lead: {str(e)}")


@router.delete("/{lead_id}/tags/{tag_id}")
async def remove_tag_from_lead(
    lead_id: int = Path(..., gt=0),
    tag_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db)
):
    """Remove a tag from a lead."""
    try:
        # Find the association
        query = select(LeadTag).where(
            and_(
                LeadTag.lead_id == lead_id,
                LeadTag.tag_id == tag_id
            )
        )
        result = await db.execute(query)
        lead_tag = result.scalar_one_or_none()

        if not lead_tag:
            raise HTTPException(status_code=404, detail="Lead tag association not found")

        await db.delete(lead_tag)
        await db.commit()

        return {"message": "Tag removed from lead successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to remove tag from lead: {str(e)}")
