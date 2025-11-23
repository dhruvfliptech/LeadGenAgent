"""
Notes API Schemas.

Pydantic models for request/response validation in note endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class NoteCreate(BaseModel):
    """Schema for creating a new note."""
    content: str = Field(..., min_length=1, description="Note content")
    author_id: Optional[str] = Field(None, max_length=255, description="User ID or email of note author")


class NoteUpdate(BaseModel):
    """Schema for updating an existing note."""
    content: Optional[str] = Field(None, min_length=1, description="Note content")
    author_id: Optional[str] = Field(None, max_length=255, description="User ID or email of note author")


class NoteResponse(BaseModel):
    """Schema for note responses."""
    id: int
    lead_id: int
    content: str
    author_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NoteListResponse(BaseModel):
    """Schema for notes list response."""
    notes: List[NoteResponse]
    total: int
    page: int
    page_size: int
