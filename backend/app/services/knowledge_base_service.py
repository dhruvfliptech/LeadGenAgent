"""
Knowledge Base Service with Semantic Search.

This service provides semantic search capabilities using OpenAI embeddings
and pgvector for efficient similarity matching.

Powers:
- Email AI Agent (context retrieval)
- Deep Search Agent (scraping rules)
- Lead Qualification (company info, ICP)
- Auto-Response Rules (policies, FAQs)
"""

import os
import time
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
import logging

from ..models.knowledge_base import KnowledgeBaseEntry, EntryType  # KnowledgeBaseEmbedding removed - pgvector not available
from ..schemas.knowledge_base import (
    KnowledgeBaseEntryCreate,
    KnowledgeBaseEntryUpdate,
    SemanticSearchRequest,
    AgentQueryRequest,
    SearchResultItem,
    KnowledgeBaseEntryResponse
)
from .openrouter_client import get_openrouter_client

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """Service for managing knowledge base entries and semantic search"""

    def __init__(self, db: Session):
        """
        Initialize the knowledge base service.

        Args:
            db: Database session
        """
        self.db = db

        # Use OpenRouter client for AI operations (embeddings, etc.)
        self._ai_client = get_openrouter_client()
        logger.info("Knowledge Base Service initialized with OpenRouter AI client")

    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using OpenRouter API.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding (1536 dimensions), or None if failed
        """
        try:
            # Truncate text to avoid token limits (8191 tokens for ada-002)
            max_chars = 8000 * 4  # Rough estimate: 1 token ≈ 4 chars
            if len(text) > max_chars:
                text = text[:max_chars]
                logger.warning(f"Text truncated to {max_chars} characters for embedding")

            embedding = await self._ai_client.generate_embedding(text)
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    async def create_entry(self, entry_data: KnowledgeBaseEntryCreate) -> KnowledgeBaseEntry:
        """
        Create a new knowledge base entry with automatic embedding generation.

        Args:
            entry_data: Entry creation data

        Returns:
            Created knowledge base entry
        """
        # Create the entry
        entry = KnowledgeBaseEntry(
            entry_type=entry_data.entry_type.value,
            title=entry_data.title,
            content=entry_data.content,
            metadata_json=entry_data.metadata or {},
            tags=entry_data.tags or [],
            category=entry_data.category,
            priority=entry_data.priority,
            is_active=entry_data.is_active
        )

        self.db.add(entry)
        self.db.flush()  # Get the entry ID

        # Generate and store embedding
        embedding_text = f"{entry_data.title}\n\n{entry_data.content}"
        embedding_vector = await self._generate_embedding(embedding_text)

        if embedding_vector:
            embedding = KnowledgeBaseEmbedding(
                entry_id=entry.id,
                embedding=embedding_vector,
                model="text-embedding-ada-002"
            )
            self.db.add(embedding)

        self.db.commit()
        self.db.refresh(entry)

        logger.info(f"Created knowledge base entry: {entry.id} - {entry.title}")
        return entry

    def get_entry(self, entry_id: int) -> Optional[KnowledgeBaseEntry]:
        """Get a single entry by ID"""
        return self.db.query(KnowledgeBaseEntry).filter(
            KnowledgeBaseEntry.id == entry_id
        ).first()

    async def update_entry(self, entry_id: int, entry_data: KnowledgeBaseEntryUpdate) -> Optional[KnowledgeBaseEntry]:
        """
        Update an existing knowledge base entry.
        Regenerates embedding if title or content changed.

        Args:
            entry_id: Entry ID to update
            entry_data: Update data

        Returns:
            Updated entry or None if not found
        """
        entry = self.get_entry(entry_id)
        if not entry:
            return None

        # Track if we need to regenerate embedding
        regenerate_embedding = False

        # Update fields
        update_data = entry_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field in ["title", "content"] and value != getattr(entry, field):
                regenerate_embedding = True
            setattr(entry, field, value)

        # Regenerate embedding if needed
        if regenerate_embedding:
            # Delete old embedding
            self.db.query(KnowledgeBaseEmbedding).filter(
                KnowledgeBaseEmbedding.entry_id == entry_id
            ).delete()

            # Generate new embedding
            embedding_text = f"{entry.title}\n\n{entry.content}"
            embedding_vector = await self._generate_embedding(embedding_text)

            if embedding_vector:
                embedding = KnowledgeBaseEmbedding(
                    entry_id=entry.id,
                    embedding=embedding_vector,
                    model="text-embedding-ada-002"
                )
                self.db.add(embedding)

        self.db.commit()
        self.db.refresh(entry)

        logger.info(f"Updated knowledge base entry: {entry.id}")
        return entry

    def delete_entry(self, entry_id: int) -> bool:
        """
        Delete a knowledge base entry (cascade deletes embedding).

        Args:
            entry_id: Entry ID to delete

        Returns:
            True if deleted, False if not found
        """
        entry = self.get_entry(entry_id)
        if not entry:
            return False

        self.db.delete(entry)
        self.db.commit()

        logger.info(f"Deleted knowledge base entry: {entry_id}")
        return True

    def list_entries(
        self,
        entry_types: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        min_priority: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[KnowledgeBaseEntry], int]:
        """
        List knowledge base entries with filtering and pagination.

        Returns:
            Tuple of (entries, total_count)
        """
        query = self.db.query(KnowledgeBaseEntry)

        # Apply filters
        if entry_types:
            query = query.filter(KnowledgeBaseEntry.entry_type.in_(entry_types))

        if categories:
            query = query.filter(KnowledgeBaseEntry.category.in_(categories))

        if tags:
            # Match any tag
            query = query.filter(KnowledgeBaseEntry.tags.overlap(tags))

        if is_active is not None:
            query = query.filter(KnowledgeBaseEntry.is_active == is_active)

        if search:
            search_filter = or_(
                KnowledgeBaseEntry.title.ilike(f"%{search}%"),
                KnowledgeBaseEntry.content.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        if min_priority is not None:
            query = query.filter(KnowledgeBaseEntry.priority >= min_priority)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        entries = query.order_by(
            KnowledgeBaseEntry.priority.desc(),
            KnowledgeBaseEntry.updated_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return entries, total

    async def semantic_search(self, search_request: SemanticSearchRequest) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector similarity.

        Args:
            search_request: Search parameters

        Returns:
            List of search results with similarity scores
        """
        start_time = time.time()

        # Generate query embedding
        query_embedding = await self._generate_embedding(search_request.query)
        if not query_embedding:
            logger.warning("Could not generate query embedding. Falling back to text search.")
            return self._fallback_text_search(search_request)

        # Build base query
        query = self.db.query(
            KnowledgeBaseEntry,
            KnowledgeBaseEmbedding,
            # Calculate cosine similarity
            (1 - KnowledgeBaseEmbedding.embedding.cosine_distance(query_embedding)).label('similarity')
        ).join(
            KnowledgeBaseEmbedding,
            KnowledgeBaseEntry.id == KnowledgeBaseEmbedding.entry_id
        )

        # Apply filters
        if search_request.only_active:
            query = query.filter(KnowledgeBaseEntry.is_active == True)

        if search_request.entry_types:
            entry_type_values = [et.value for et in search_request.entry_types]
            query = query.filter(KnowledgeBaseEntry.entry_type.in_(entry_type_values))

        if search_request.categories:
            query = query.filter(KnowledgeBaseEntry.category.in_(search_request.categories))

        if search_request.tags:
            query = query.filter(KnowledgeBaseEntry.tags.overlap(search_request.tags))

        # Filter by minimum similarity
        query = query.filter(
            (1 - KnowledgeBaseEmbedding.embedding.cosine_distance(query_embedding)) >= search_request.min_similarity
        )

        # Order by similarity and priority
        query = query.order_by(
            text('similarity DESC'),
            KnowledgeBaseEntry.priority.desc()
        ).limit(search_request.limit)

        # Execute query
        results = query.all()

        # Format results
        formatted_results = []
        for idx, (entry, embedding, similarity) in enumerate(results, 1):
            formatted_results.append({
                "entry": entry,
                "similarity": float(similarity),
                "rank": idx
            })

        search_time = (time.time() - start_time) * 1000  # Convert to ms
        logger.info(f"Semantic search completed in {search_time:.2f}ms, found {len(formatted_results)} results")

        return formatted_results

    def _fallback_text_search(self, search_request: SemanticSearchRequest) -> List[Dict[str, Any]]:
        """
        Fallback to text-based search when embeddings are not available.

        This is used when OpenAI API is not configured.
        """
        query = self.db.query(KnowledgeBaseEntry)

        # Apply filters
        if search_request.only_active:
            query = query.filter(KnowledgeBaseEntry.is_active == True)

        if search_request.entry_types:
            entry_type_values = [et.value for et in search_request.entry_types]
            query = query.filter(KnowledgeBaseEntry.entry_type.in_(entry_type_values))

        if search_request.categories:
            query = query.filter(KnowledgeBaseEntry.category.in_(search_request.categories))

        if search_request.tags:
            query = query.filter(KnowledgeBaseEntry.tags.overlap(search_request.tags))

        # Text search
        search_filter = or_(
            KnowledgeBaseEntry.title.ilike(f"%{search_request.query}%"),
            KnowledgeBaseEntry.content.ilike(f"%{search_request.query}%")
        )
        query = query.filter(search_filter)

        # Order by priority
        results = query.order_by(
            KnowledgeBaseEntry.priority.desc()
        ).limit(search_request.limit).all()

        # Format results (similarity is 0.5 as a placeholder)
        return [
            {
                "entry": entry,
                "similarity": 0.5,
                "rank": idx
            }
            for idx, entry in enumerate(results, 1)
        ]

    async def query_for_agent(self, agent_request: AgentQueryRequest) -> Dict[str, Any]:
        """
        Query knowledge base for AI agent context.

        Returns relevant entries combined into a structured context.

        Args:
            agent_request: Agent query parameters

        Returns:
            Dictionary with relevant entries and combined context
        """
        start_time = time.time()

        # Create semantic search request
        search_request = SemanticSearchRequest(
            query=agent_request.query,
            entry_types=agent_request.entry_types,
            limit=agent_request.limit,
            min_similarity=0.7,
            only_active=True
        )

        # Perform semantic search
        results = await self.semantic_search(search_request)

        # Combine context
        context_parts = []
        for result in results:
            entry = result["entry"]
            context_parts.append(f"[{entry.entry_type}] {entry.title}\n{entry.content}")

        combined_context = "\n\n---\n\n".join(context_parts)

        search_time = (time.time() - start_time) * 1000

        return {
            "query": agent_request.query,
            "agent_type": agent_request.agent_type,
            "relevant_entries": results,
            "combined_context": combined_context,
            "metadata": {
                "total_entries_found": len(results),
                "average_similarity": sum(r["similarity"] for r in results) / len(results) if results else 0,
                "search_time_ms": search_time,
                "agent_context": agent_request.context
            }
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        total_entries = self.db.query(func.count(KnowledgeBaseEntry.id)).scalar()
        active_entries = self.db.query(func.count(KnowledgeBaseEntry.id)).filter(
            KnowledgeBaseEntry.is_active == True
        ).scalar()

        # Entries by type
        entries_by_type = dict(
            self.db.query(
                KnowledgeBaseEntry.entry_type,
                func.count(KnowledgeBaseEntry.id)
            ).group_by(KnowledgeBaseEntry.entry_type).all()
        )

        # Entries by category
        entries_by_category = dict(
            self.db.query(
                KnowledgeBaseEntry.category,
                func.count(KnowledgeBaseEntry.id)
            ).filter(
                KnowledgeBaseEntry.category.isnot(None)
            ).group_by(KnowledgeBaseEntry.category).all()
        )

        # Total embeddings
        total_embeddings = self.db.query(func.count(KnowledgeBaseEmbedding.id)).scalar()

        # Last updated
        last_entry = self.db.query(KnowledgeBaseEntry).order_by(
            KnowledgeBaseEntry.updated_at.desc()
        ).first()

        return {
            "total_entries": total_entries,
            "active_entries": active_entries,
            "entries_by_type": entries_by_type,
            "entries_by_category": entries_by_category,
            "total_embeddings": total_embeddings,
            "last_updated": last_entry.updated_at if last_entry else None,
            "openai_configured": self._ai_client is not None
        }
