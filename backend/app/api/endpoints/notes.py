"""
Notes API endpoints for managing lead notes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import List, Optional

from app.core.database import get_db
from app.models.notes import Note
from app.models.leads import Lead
from app.schemas.notes import (
    NoteCreate, NoteUpdate, NoteResponse, NoteListResponse
)


router = APIRouter()


# ============================================================================
# NOTE MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/{lead_id}/notes", response_model=NoteListResponse)
async def get_lead_notes(
    lead_id: int = Path(..., gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get all notes for a lead with pagination."""
    # Verify lead exists
    lead_check = await db.execute(
        select(Lead).where(Lead.id == lead_id)
    )
    if not lead_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lead not found")

    # Get total count
    count_query = select(func.count(Note.id)).where(Note.lead_id == lead_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Get paginated results
    query = select(Note).where(Note.lead_id == lead_id).order_by(desc(Note.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    notes = result.scalars().all()

    page = skip // limit if limit > 0 else 0

    return NoteListResponse(
        notes=notes,
        total=total,
        page=page,
        page_size=limit
    )


@router.get("/note/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific note by ID."""
    query = select(Note).where(Note.id == note_id)
    result = await db.execute(query)
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return note


@router.post("/{lead_id}/notes", response_model=NoteResponse)
async def create_note(
    lead_id: int = Path(..., gt=0),
    note_data: NoteCreate = None,
    db: AsyncSession = Depends(get_db)
):
    """Create a new note for a lead."""
    try:
        # Verify lead exists
        lead_check = await db.execute(
            select(Lead).where(Lead.id == lead_id)
        )
        if not lead_check.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Lead not found")

        # Create note
        note = Note(lead_id=lead_id, **note_data.model_dump())
        db.add(note)
        await db.commit()
        await db.refresh(note)

        return note

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create note: {str(e)}")


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int = Path(..., gt=0),
    note_data: NoteUpdate = None,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing note."""
    query = select(Note).where(Note.id == note_id)
    result = await db.execute(query)
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    try:
        # Update fields
        update_data = note_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(note, field, value)

        await db.commit()
        await db.refresh(note)

        return note

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update note: {str(e)}")


@router.delete("/{note_id}")
async def delete_note(
    note_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db)
):
    """Delete a note."""
    query = select(Note).where(Note.id == note_id)
    result = await db.execute(query)
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    try:
        await db.delete(note)
        await db.commit()

        return {"message": "Note deleted successfully"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete note: {str(e)}")
