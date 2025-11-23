"""
Tags API Schemas.

Pydantic models for request/response validation in tag endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TagCreate(BaseModel):
    """Schema for creating a new tag."""
    name: str = Field(..., min_length=1, max_length=255, description="Tag name")
    color: str = Field(default="#808080", pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", description="Hex color code")
    category: Optional[str] = Field(None, max_length=100, description="Tag category (e.g., priority, status)")


class TagUpdate(BaseModel):
    """Schema for updating an existing tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = Field(None, pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    category: Optional[str] = Field(None, max_length=100)


class TagResponse(BaseModel):
    """Schema for tag responses."""
    id: int
    name: str
    color: str
    category: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class LeadTagResponse(BaseModel):
    """Schema for lead-tag relationship responses."""
    lead_id: int
    tag_id: int
    tag: Optional[TagResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TagListResponse(BaseModel):
    """Schema for tag list response."""
    tags: List[TagResponse]
    total: int
    page: int
    page_size: int


class AddTagRequest(BaseModel):
    """Schema for adding a tag to a lead."""
    tag_id: int = Field(..., description="Tag ID to add to lead")


class AddTagByNameRequest(BaseModel):
    """Schema for adding a tag to a lead by name."""
    name: str = Field(..., min_length=1, max_length=255, description="Tag name to add to lead")
    color: str = Field(default="#808080", pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", description="Hex color code (used if tag doesn't exist)")
    category: Optional[str] = Field(None, max_length=100, description="Tag category (used if tag doesn't exist)")
