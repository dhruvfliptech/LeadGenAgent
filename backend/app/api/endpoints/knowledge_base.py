"""
Knowledge Base API Endpoints.

Provides RESTful API for managing knowledge base entries and performing semantic search.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ...core.database import get_db
from ...services.knowledge_base_service import KnowledgeBaseService
from ...schemas.knowledge_base import (
    KnowledgeBaseEntryCreate,
    KnowledgeBaseEntryUpdate,
    KnowledgeBaseEntryResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    AgentQueryRequest,
    AgentContextResponse,
    KnowledgeBaseListResponse,
    KnowledgeBaseStats,
    SearchResultItem,
    EntryTypeEnum
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge Base"])


def get_kb_service(db: Session = Depends(get_db)) -> KnowledgeBaseService:
    """Dependency to get knowledge base service"""
    return KnowledgeBaseService(db)


@router.post("/entries", response_model=KnowledgeBaseEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_entry(
    entry_data: KnowledgeBaseEntryCreate,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    Create a new knowledge base entry.

    Automatically generates vector embeddings using OpenAI for semantic search.

    **Entry Types:**
    - `company_info`: Company information, history, values
    - `service_description`: Services offered, pricing, features
    - `faq`: Frequently asked questions and answers
    - `search_rule`: Search criteria and patterns for scraping
    - `qualification_rule`: Lead qualification criteria
    - `scraping_pattern`: Web scraping patterns and selectors
    - `business_policy`: Business policies and guidelines
    - `response_guideline`: Email response guidelines
    - `customer_profile`: Ideal customer profiles
    - `industry_knowledge`: Industry-specific knowledge

    **Example:**
    ```json
    {
      "entry_type": "faq",
      "title": "What is our response time?",
      "content": "We respond to all leads within 24 hours during business days.",
      "tags": ["faq", "customer_service"],
      "category": "customer_support",
      "priority": 80
    }
    ```
    """
    try:
        entry = await kb_service.create_entry(entry_data)
        return entry
    except Exception as e:
        logger.error(f"Failed to create knowledge base entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create entry: {str(e)}"
        )


@router.get("/entries", response_model=KnowledgeBaseListResponse)
async def list_entries(
    entry_types: Optional[List[EntryTypeEnum]] = Query(None, description="Filter by entry types"),
    categories: Optional[List[str]] = Query(None, description="Filter by categories"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags (any match)"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    min_priority: Optional[int] = Query(None, ge=0, le=100, description="Minimum priority"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    List knowledge base entries with filtering and pagination.

    **Filters:**
    - `entry_types`: Filter by one or more entry types
    - `categories`: Filter by categories
    - `tags`: Filter by tags (matches if any tag is present)
    - `is_active`: Show only active/inactive entries
    - `search`: Full-text search in title and content
    - `min_priority`: Minimum priority score

    **Pagination:**
    - Results are ordered by priority (desc) and updated_at (desc)
    - Use `page` and `page_size` to navigate results
    """
    try:
        entry_type_values = [et.value for et in entry_types] if entry_types else None

        entries, total = kb_service.list_entries(
            entry_types=entry_type_values,
            categories=categories,
            tags=tags,
            is_active=is_active,
            search=search,
            min_priority=min_priority,
            page=page,
            page_size=page_size
        )

        total_pages = (total + page_size - 1) // page_size

        return KnowledgeBaseListResponse(
            entries=entries,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        logger.error(f"Failed to list entries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list entries: {str(e)}"
        )


@router.get("/entries/{entry_id}", response_model=KnowledgeBaseEntryResponse)
async def get_entry(
    entry_id: int,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    Get a single knowledge base entry by ID.

    Returns the complete entry including metadata, tags, and timestamps.
    """
    entry = kb_service.get_entry(entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entry {entry_id} not found"
        )
    return entry


@router.put("/entries/{entry_id}", response_model=KnowledgeBaseEntryResponse)
async def update_entry(
    entry_id: int,
    entry_data: KnowledgeBaseEntryUpdate,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    Update an existing knowledge base entry.

    If title or content is updated, the vector embedding will be automatically regenerated.

    **Partial Updates:**
    Only include fields you want to update. Other fields remain unchanged.

    **Example:**
    ```json
    {
      "content": "Updated: We respond within 12 hours during business days.",
      "priority": 90
    }
    ```
    """
    try:
        entry = await kb_service.update_entry(entry_id, entry_data)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entry {entry_id} not found"
            )
        return entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update entry {entry_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update entry: {str(e)}"
        )


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: int,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    Delete a knowledge base entry.

    This will also cascade delete the associated vector embedding.

    **Warning:** This is a permanent deletion and cannot be undone.
    Consider setting `is_active=false` instead for soft deletion.
    """
    success = kb_service.delete_entry(entry_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entry {entry_id} not found"
        )
    return None


@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search(
    search_request: SemanticSearchRequest,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    Perform semantic search using vector similarity.

    Uses OpenAI embeddings and pgvector to find entries semantically similar to the query.

    **How it works:**
    1. Converts query text to vector embedding using OpenAI
    2. Performs cosine similarity search in pgvector
    3. Returns entries ranked by similarity score
    4. Filters by entry type, category, tags if specified

    **Similarity Scores:**
    - 0.9-1.0: Highly relevant
    - 0.8-0.9: Very relevant
    - 0.7-0.8: Relevant
    - Below 0.7: May not be relevant (adjust min_similarity)

    **Example:**
    ```json
    {
      "query": "How do we handle urgent property inquiries?",
      "entry_types": ["faq", "business_policy"],
      "categories": ["customer_support"],
      "limit": 5,
      "min_similarity": 0.75
    }
    ```

    **Note:** Requires OPENAI_API_KEY to be configured. Falls back to text search if not available.
    """
    try:
        import time
        start_time = time.time()

        results = await kb_service.semantic_search(search_request)

        search_time = (time.time() - start_time) * 1000

        # Convert to response format
        search_results = [
            SearchResultItem(
                entry=KnowledgeBaseEntryResponse.from_orm(r["entry"]),
                similarity=r["similarity"],
                rank=r["rank"]
            )
            for r in results
        ]

        return SemanticSearchResponse(
            query=search_request.query,
            results=search_results,
            total_results=len(search_results),
            search_time_ms=search_time
        )

    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/query", response_model=AgentContextResponse)
async def query_for_agent(
    agent_request: AgentQueryRequest,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    Query knowledge base for AI agent context.

    Returns relevant entries combined into structured context for AI agents.

    **Agent Types:**
    - `email_ai_agent`: Email response generation
    - `deep_search_agent`: Web scraping configuration
    - `qualification_agent`: Lead qualification
    - `response_agent`: Auto-response rules

    **Response includes:**
    - `relevant_entries`: Ranked list of matching entries
    - `combined_context`: Pre-formatted context text for LLM prompts
    - `metadata`: Search statistics and agent context

    **Example:**
    ```json
    {
      "query": "Generate response for seller asking about our buying process",
      "agent_type": "email_ai_agent",
      "context": {
        "lead_id": 123,
        "property_type": "fixer-upper"
      },
      "entry_types": ["service_description", "business_policy"],
      "limit": 5
    }
    ```

    **Use case:**
    This endpoint is designed to be called by AI agents to retrieve relevant context
    before generating responses, making decisions, or configuring behavior.
    """
    try:
        result = await kb_service.query_for_agent(agent_request)

        # Convert to response format
        result["relevant_entries"] = [
            SearchResultItem(
                entry=KnowledgeBaseEntryResponse.from_orm(r["entry"]),
                similarity=r["similarity"],
                rank=r["rank"]
            )
            for r in result["relevant_entries"]
        ]

        return AgentContextResponse(**result)

    except Exception as e:
        logger.error(f"Agent query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent query failed: {str(e)}"
        )


@router.get("/stats", response_model=KnowledgeBaseStats)
async def get_stats(
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    Get knowledge base statistics.

    Returns:
    - Total entries and active entries
    - Distribution by entry type
    - Distribution by category
    - Total embeddings generated
    - Last updated timestamp
    - OpenAI configuration status

    **Use case:**
    Monitor knowledge base health and usage. Check if OpenAI is properly configured.
    """
    try:
        stats = kb_service.get_stats()
        return KnowledgeBaseStats(**stats)
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


# Health check endpoint
@router.get("/health")
async def health_check(
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """
    Check knowledge base system health.

    Verifies:
    - Database connectivity
    - OpenAI API configuration
    - Vector search availability
    """
    try:
        stats = kb_service.get_stats()
        return {
            "status": "healthy",
            "database": "connected",
            "openai_configured": stats.get("openai_configured", False),
            "total_entries": stats.get("total_entries", 0),
            "total_embeddings": stats.get("total_embeddings", 0)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
