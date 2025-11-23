"""
Pydantic schemas for Knowledge Base API endpoints.

These schemas define the request/response structures for the knowledge base system.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EntryTypeEnum(str, Enum):
    """Valid knowledge base entry types"""
    COMPANY_INFO = "company_info"
    SERVICE_DESCRIPTION = "service_description"
    FAQ = "faq"
    SEARCH_RULE = "search_rule"
    QUALIFICATION_RULE = "qualification_rule"
    SCRAPING_PATTERN = "scraping_pattern"
    BUSINESS_POLICY = "business_policy"
    RESPONSE_GUIDELINE = "response_guideline"
    CUSTOMER_PROFILE = "customer_profile"
    INDUSTRY_KNOWLEDGE = "industry_knowledge"


# Request Schemas

class KnowledgeBaseEntryCreate(BaseModel):
    """Schema for creating a new knowledge base entry"""
    entry_type: EntryTypeEnum = Field(..., description="Type of knowledge entry")
    title: str = Field(..., min_length=1, max_length=255, description="Entry title")
    content: str = Field(..., min_length=1, description="Main content of the entry")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorization")
    category: Optional[str] = Field(None, max_length=100, description="Category classification")
    priority: int = Field(default=0, ge=0, le=100, description="Priority for search results (0-100)")
    is_active: bool = Field(default=True, description="Whether entry is active")

    @validator("tags")
    def validate_tags(cls, v):
        """Ensure tags are unique and not too long"""
        if v:
            # Remove duplicates
            v = list(set(v))
            # Limit tag length
            v = [tag[:100] for tag in v]
        return v

    class Config:
        schema_extra = {
            "example": {
                "entry_type": "faq",
                "title": "What is our response time?",
                "content": "We respond to all leads within 24 hours during business days. For urgent inquiries, we provide same-day responses.",
                "metadata": {
                    "question": "What is your response time?",
                    "related_topics": ["customer_service", "response_time"]
                },
                "tags": ["faq", "customer_service", "timing"],
                "category": "customer_support",
                "priority": 80,
                "is_active": True
            }
        }


class KnowledgeBaseEntryUpdate(BaseModel):
    """Schema for updating an existing knowledge base entry"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = Field(None, max_length=100)
    priority: Optional[int] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None

    @validator("tags")
    def validate_tags(cls, v):
        if v:
            v = list(set(v))
            v = [tag[:100] for tag in v]
        return v

    class Config:
        schema_extra = {
            "example": {
                "content": "Updated: We respond to all leads within 12 hours during business days.",
                "priority": 90
            }
        }


class SemanticSearchRequest(BaseModel):
    """Schema for semantic search queries"""
    query: str = Field(..., min_length=1, description="Search query text")
    entry_types: Optional[List[EntryTypeEnum]] = Field(None, description="Filter by entry types")
    categories: Optional[List[str]] = Field(None, description="Filter by categories")
    tags: Optional[List[str]] = Field(None, description="Filter by tags (any match)")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return")
    min_similarity: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    only_active: bool = Field(default=True, description="Only return active entries")

    class Config:
        schema_extra = {
            "example": {
                "query": "How do we handle urgent property inquiries?",
                "entry_types": ["faq", "business_policy"],
                "categories": ["customer_support"],
                "limit": 5,
                "min_similarity": 0.75,
                "only_active": True
            }
        }


class AgentQueryRequest(BaseModel):
    """Schema for AI agent context queries"""
    query: str = Field(..., min_length=1, description="Agent's query for context")
    agent_type: str = Field(..., description="Type of agent making the query")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    entry_types: Optional[List[EntryTypeEnum]] = Field(None, description="Preferred entry types")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum results")

    class Config:
        schema_extra = {
            "example": {
                "query": "Generate response for a seller asking about our buying process",
                "agent_type": "email_ai_agent",
                "context": {
                    "lead_id": 123,
                    "property_type": "fixer-upper",
                    "price_range": "100k-200k"
                },
                "entry_types": ["service_description", "business_policy", "response_guideline"],
                "limit": 5
            }
        }


# Response Schemas

class KnowledgeBaseEntryResponse(BaseModel):
    """Schema for knowledge base entry responses"""
    id: int
    entry_type: str
    title: str
    content: str
    metadata: Dict[str, Any]
    tags: List[str]
    category: Optional[str]
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class SearchResultItem(BaseModel):
    """Schema for individual search result with similarity score"""
    entry: KnowledgeBaseEntryResponse
    similarity: float = Field(..., description="Similarity score (0-1)")
    rank: int = Field(..., description="Result rank position")

    class Config:
        schema_extra = {
            "example": {
                "entry": {
                    "id": 1,
                    "entry_type": "faq",
                    "title": "Response time policy",
                    "content": "We respond within 24 hours...",
                    "metadata": {},
                    "tags": ["faq"],
                    "category": "customer_support",
                    "priority": 80,
                    "is_active": True,
                    "created_at": "2024-11-05T10:00:00",
                    "updated_at": "2024-11-05T10:00:00"
                },
                "similarity": 0.92,
                "rank": 1
            }
        }


class SemanticSearchResponse(BaseModel):
    """Schema for semantic search results"""
    query: str
    results: List[SearchResultItem]
    total_results: int
    search_time_ms: float

    class Config:
        schema_extra = {
            "example": {
                "query": "How do we handle urgent inquiries?",
                "results": [],
                "total_results": 5,
                "search_time_ms": 45.2
            }
        }


class AgentContextResponse(BaseModel):
    """Schema for AI agent context responses"""
    query: str
    agent_type: str
    relevant_entries: List[SearchResultItem]
    combined_context: str = Field(..., description="Aggregated context for the agent")
    metadata: Dict[str, Any] = Field(..., description="Additional context metadata")

    class Config:
        schema_extra = {
            "example": {
                "query": "Generate email response",
                "agent_type": "email_ai_agent",
                "relevant_entries": [],
                "combined_context": "Based on our policies, we respond within 24 hours...",
                "metadata": {
                    "total_entries_found": 3,
                    "average_similarity": 0.85,
                    "search_time_ms": 32.1
                }
            }
        }


class KnowledgeBaseListResponse(BaseModel):
    """Schema for paginated list of knowledge base entries"""
    entries: List[KnowledgeBaseEntryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class KnowledgeBaseStats(BaseModel):
    """Schema for knowledge base statistics"""
    total_entries: int
    active_entries: int
    entries_by_type: Dict[str, int]
    entries_by_category: Dict[str, int]
    total_embeddings: int
    last_updated: Optional[datetime]

    class Config:
        schema_extra = {
            "example": {
                "total_entries": 150,
                "active_entries": 142,
                "entries_by_type": {
                    "faq": 45,
                    "service_description": 20,
                    "qualification_rule": 15
                },
                "entries_by_category": {
                    "customer_support": 60,
                    "sales": 40,
                    "technical": 50
                },
                "total_embeddings": 142,
                "last_updated": "2024-11-05T10:00:00"
            }
        }


# Filter Schemas

class KnowledgeBaseFilters(BaseModel):
    """Schema for filtering knowledge base queries"""
    entry_types: Optional[List[EntryTypeEnum]] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = True
    search: Optional[str] = None
    min_priority: Optional[int] = Field(None, ge=0, le=100)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    class Config:
        schema_extra = {
            "example": {
                "entry_types": ["faq", "service_description"],
                "categories": ["customer_support"],
                "is_active": True,
                "search": "response time",
                "page": 1,
                "page_size": 20
            }
        }
