"""
Vector Store - Stores and retrieves conversation embeddings using pgvector.

Features:
- Store conversation messages with embeddings
- Find similar successful conversations for context
- Semantic search for best practice examples
- Integration with PostgreSQL pgvector extension

Used by ConversationAI to provide context from historical conversations.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = structlog.get_logger(__name__)


class VectorStore:
    """
    Vector store for conversation embeddings using pgvector.

    Stores:
    - Message embeddings for semantic search
    - Conversation outcomes (successful/unsuccessful)
    - Context metadata (intent, sentiment, industry)
    """

    # OpenAI embedding model (cheap and effective)
    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS = 1536
    OPENAI_EMBEDDING_URL = "https://api.openai.com/v1/embeddings"

    def __init__(
        self,
        db_session: AsyncSession,
        openai_api_key: str
    ):
        """Initialize vector store."""
        self.db = db_session
        self.openai_api_key = openai_api_key
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()

    async def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text using OpenAI.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (1536 dimensions)
        """
        try:
            response = await self.http_client.post(
                self.OPENAI_EMBEDDING_URL,
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": text,
                    "model": self.EMBEDDING_MODEL
                }
            )
            response.raise_for_status()
            data = response.json()
            embedding = data["data"][0]["embedding"]

            logger.info(
                "vector_store.embedding_created",
                text_length=len(text),
                embedding_dims=len(embedding)
            )

            return embedding

        except Exception as e:
            logger.error(
                "vector_store.embedding_failed",
                error=str(e),
                text_preview=text[:100]
            )
            # Return zero vector as fallback
            return [0.0] * self.EMBEDDING_DIMENSIONS

    async def store_message(
        self,
        conversation_id: int,
        message_id: int,
        message_text: str,
        role: str,
        intent: Optional[str] = None,
        sentiment: Optional[str] = None,
        outcome: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Store a conversation message with its embedding.

        Args:
            conversation_id: ID of conversation
            message_id: ID of message
            message_text: Message content
            role: "user" or "lead"
            intent: Message intent (question, interest, etc.)
            sentiment: Message sentiment (positive, neutral, negative)
            outcome: Conversation outcome (if applicable)
            metadata: Additional metadata

        Returns:
            Vector record ID
        """
        # Generate embedding
        embedding = await self._get_embedding(message_text)

        # Store in database
        query = text("""
            INSERT INTO conversation_vectors (
                conversation_id,
                message_id,
                message_text,
                embedding,
                role,
                intent,
                sentiment,
                outcome,
                metadata,
                created_at
            )
            VALUES (
                :conversation_id,
                :message_id,
                :message_text,
                :embedding::vector,
                :role,
                :intent,
                :sentiment,
                :outcome,
                :metadata,
                NOW()
            )
            RETURNING id
        """)

        import json

        result = await self.db.execute(
            query,
            {
                "conversation_id": conversation_id,
                "message_id": message_id,
                "message_text": message_text[:2000],  # Limit stored text
                "embedding": str(embedding),  # Convert to string for pgvector
                "role": role,
                "intent": intent,
                "sentiment": sentiment,
                "outcome": outcome,
                "metadata": json.dumps(metadata or {})
            }
        )
        await self.db.commit()

        vector_id = result.scalar()

        logger.info(
            "vector_store.message_stored",
            vector_id=vector_id,
            conversation_id=conversation_id,
            message_id=message_id,
            role=role
        )

        return vector_id

    async def find_similar_conversations(
        self,
        query_text: str,
        intent: Optional[str] = None,
        sentiment: Optional[str] = None,
        limit: int = 5,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find similar conversations using semantic search.

        Args:
            query_text: Text to search for (incoming reply)
            intent: Filter by intent (optional)
            sentiment: Filter by sentiment (optional)
            limit: Max results to return
            min_similarity: Minimum cosine similarity (0-1)

        Returns:
            List of similar conversations with metadata
        """
        # Generate query embedding
        query_embedding = await self._get_embedding(query_text)

        # Build filters
        filters = ["outcome = 'success'"]  # Only successful conversations
        params = {
            "query_embedding": str(query_embedding),
            "limit": limit,
            "min_similarity": min_similarity
        }

        if intent:
            filters.append("intent = :intent")
            params["intent"] = intent

        if sentiment:
            filters.append("sentiment = :sentiment")
            params["sentiment"] = sentiment

        where_clause = " AND ".join(filters)

        # Semantic search using pgvector cosine similarity
        query = text(f"""
            SELECT
                cv.conversation_id,
                cv.message_text,
                cv.intent,
                cv.sentiment,
                cv.outcome,
                cv.metadata,
                (1 - (cv.embedding <=> :query_embedding::vector)) as similarity
            FROM conversation_vectors cv
            WHERE {where_clause}
            ORDER BY cv.embedding <=> :query_embedding::vector ASC
            LIMIT :limit
        """)

        try:
            result = await self.db.execute(query, params)
            rows = result.fetchall()

            similar_conversations = []
            for row in rows:
                import json
                metadata = json.loads(row[5]) if row[5] else {}

                # Get the response message (next message in conversation)
                response_query = text("""
                    SELECT message_text
                    FROM conversation_vectors
                    WHERE conversation_id = :conversation_id
                      AND role = 'user'
                      AND id > (
                          SELECT id FROM conversation_vectors
                          WHERE conversation_id = :conversation_id
                          ORDER BY id ASC LIMIT 1
                      )
                    ORDER BY id ASC
                    LIMIT 1
                """)
                response_result = await self.db.execute(
                    response_query,
                    {"conversation_id": row[0]}
                )
                response_row = response_result.fetchone()
                response_text = response_row[0] if response_row else "No response found"

                similar_conversations.append({
                    "conversation_id": row[0],
                    "their_message": row[1],
                    "our_response": response_text,
                    "intent": row[2],
                    "sentiment": row[3],
                    "outcome": row[4],
                    "similarity": float(row[6]),
                    "metadata": metadata
                })

            logger.info(
                "vector_store.similar_found",
                query_length=len(query_text),
                results_count=len(similar_conversations),
                intent_filter=intent,
                sentiment_filter=sentiment
            )

            return similar_conversations

        except Exception as e:
            logger.error(
                "vector_store.search_failed",
                error=str(e),
                query_preview=query_text[:100]
            )
            return []

    async def update_conversation_outcome(
        self,
        conversation_id: int,
        outcome: str,
        conversion_value: Optional[float] = None
    ):
        """
        Update conversation outcome (success/failure).

        Args:
            conversation_id: Conversation ID
            outcome: "success", "failure", "pending"
            conversion_value: Optional monetary value
        """
        query = text("""
            UPDATE conversation_vectors
            SET
                outcome = :outcome,
                metadata = jsonb_set(
                    COALESCE(metadata, '{}'::jsonb),
                    '{conversion_value}',
                    to_jsonb(:conversion_value)
                ),
                updated_at = NOW()
            WHERE conversation_id = :conversation_id
        """)

        await self.db.execute(
            query,
            {
                "conversation_id": conversation_id,
                "outcome": outcome,
                "conversion_value": conversion_value
            }
        )
        await self.db.commit()

        logger.info(
            "vector_store.outcome_updated",
            conversation_id=conversation_id,
            outcome=outcome,
            conversion_value=conversion_value
        )

    async def get_best_practices(
        self,
        intent: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get best practice examples for a specific intent.

        Args:
            intent: Intent type (question, objection, etc.)
            limit: Max examples

        Returns:
            List of successful conversation examples
        """
        query = text("""
            SELECT
                cv1.message_text as their_message,
                cv2.message_text as our_response,
                cv1.sentiment,
                cv1.metadata
            FROM conversation_vectors cv1
            JOIN conversation_vectors cv2
                ON cv1.conversation_id = cv2.conversation_id
                AND cv2.id > cv1.id
                AND cv2.role = 'user'
            WHERE cv1.intent = :intent
              AND cv1.role = 'lead'
              AND cv1.outcome = 'success'
            ORDER BY
                (cv1.metadata->>'conversion_value')::float DESC NULLS LAST,
                cv1.created_at DESC
            LIMIT :limit
        """)

        result = await self.db.execute(
            query,
            {"intent": intent, "limit": limit}
        )
        rows = result.fetchall()

        import json
        best_practices = []
        for row in rows:
            metadata = json.loads(row[3]) if row[3] else {}
            best_practices.append({
                "their_message": row[0],
                "our_response": row[1],
                "sentiment": row[2],
                "metadata": metadata
            })

        logger.info(
            "vector_store.best_practices_retrieved",
            intent=intent,
            count=len(best_practices)
        )

        return best_practices

    async def get_conversation_stats(self) -> Dict[str, Any]:
        """Get statistics about stored conversations."""
        query = text("""
            SELECT
                COUNT(DISTINCT conversation_id) as total_conversations,
                COUNT(*) as total_messages,
                COUNT(DISTINCT CASE WHEN outcome = 'success' THEN conversation_id END) as successful_conversations,
                AVG(CASE WHEN outcome = 'success' THEN (metadata->>'conversion_value')::float END) as avg_conversion_value,
                COUNT(DISTINCT intent) as unique_intents
            FROM conversation_vectors
        """)

        result = await self.db.execute(query)
        row = result.fetchone()

        stats = {
            "total_conversations": row[0] or 0,
            "total_messages": row[1] or 0,
            "successful_conversations": row[2] or 0,
            "avg_conversion_value": float(row[3]) if row[3] else 0.0,
            "unique_intents": row[4] or 0,
            "success_rate": (row[2] / row[0] * 100) if row[0] and row[2] else 0.0
        }

        return stats


# Database migration helper
VECTOR_STORE_SCHEMA = """
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Conversation vectors table
CREATE TABLE IF NOT EXISTS conversation_vectors (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    message_text TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'lead')),
    intent VARCHAR(50),
    sentiment VARCHAR(20),
    outcome VARCHAR(20) CHECK (outcome IN ('success', 'failure', 'pending')),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversation_vectors_conversation_id
    ON conversation_vectors(conversation_id);

CREATE INDEX IF NOT EXISTS idx_conversation_vectors_intent
    ON conversation_vectors(intent);

CREATE INDEX IF NOT EXISTS idx_conversation_vectors_outcome
    ON conversation_vectors(outcome);

-- CRITICAL: Index for vector similarity search (HNSW for best performance)
CREATE INDEX IF NOT EXISTS idx_conversation_vectors_embedding
    ON conversation_vectors USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Alternative: IVFFlat index (faster build, slightly slower query)
-- CREATE INDEX idx_conversation_vectors_embedding_ivfflat
--     ON conversation_vectors USING ivfflat (embedding vector_cosine_ops)
--     WITH (lists = 100);

-- Composite index for filtered searches
CREATE INDEX IF NOT EXISTS idx_conversation_vectors_intent_outcome
    ON conversation_vectors(intent, outcome);

COMMENT ON TABLE conversation_vectors IS 'Stores conversation message embeddings for semantic search';
COMMENT ON COLUMN conversation_vectors.embedding IS 'OpenAI text-embedding-3-small (1536 dimensions)';
COMMENT ON INDEX idx_conversation_vectors_embedding IS 'HNSW index for fast cosine similarity search';
"""
