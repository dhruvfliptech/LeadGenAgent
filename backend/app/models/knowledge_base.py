"""
Knowledge Base models for storing and searching business knowledge with semantic embeddings.

This powers:
- Email AI Agent (context for personalized responses)
- Deep Search Agent (scraping rules, search criteria)
- Lead Qualification (company info, ideal customer profiles)
- Auto-Response Rules (business policies, FAQs, service descriptions)
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, ARRAY, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from datetime import datetime
import enum

from . import Base


class EntryType(str, enum.Enum):
    """Types of knowledge base entries"""
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


class KnowledgeBaseEntry(Base):
    """
    Main knowledge base entries table.

    Stores structured knowledge that can be used by AI agents for:
    - Personalizing email responses
    - Configuring scraping behavior
    - Qualifying leads
    - Generating automated responses
    """
    __tablename__ = "knowledge_base_entries"

    id = Column(Integer, primary_key=True, index=True)
    entry_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)

    # Flexible metadata storage for type-specific fields
    metadata_json = Column(JSONB, nullable=True, default={})

    # Categorization
    tags = Column(ARRAY(String(100)), nullable=True)
    category = Column(String(100), nullable=True, index=True)

    # Prioritization for search results
    priority = Column(Integer, default=0, index=True, nullable=False)

    # Soft delete support
    is_active = Column(Boolean, default=True, index=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    # NOTE: Embeddings temporarily disabled - pgvector extension not available for PostgreSQL 15
    # embeddings = relationship(
    #     "KnowledgeBaseEmbedding",
    #     back_populates="entry",
    #     cascade="all, delete-orphan"
    # )

    def __repr__(self):
        return f"<KnowledgeBaseEntry(id={self.id}, type={self.entry_type}, title='{self.title}')>"

    def to_dict(self):
        """Convert entry to dictionary"""
        return {
            "id": self.id,
            "entry_type": self.entry_type,
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata_json,
            "tags": self.tags,
            "category": self.category,
            "priority": self.priority,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# NOTE: KnowledgeBaseEmbedding class temporarily disabled - pgvector extension not available for PostgreSQL 15
# To enable: Install PostgreSQL 17+ or manually install pgvector extension for PostgreSQL 15
# class KnowledgeBaseEmbedding(Base):
#     """
#     Vector embeddings for semantic search using pgvector.
#
#     Stores OpenAI embeddings (1536 dimensions) for fast similarity search.
#     Each entry can have one embedding for efficient semantic matching.
#     """
#     __tablename__ = "knowledge_base_embeddings"
#
#     id = Column(Integer, primary_key=True, index=True)
#     entry_id = Column(Integer, ForeignKey("knowledge_base_entries.id", ondelete="CASCADE"), nullable=False, index=True)
#
#     # Vector embedding (1536 dimensions for text-embedding-ada-002)
#     embedding = Column(Vector(1536), nullable=False)
#
#     # Model used for embedding
#     model = Column(String(100), default="text-embedding-ada-002", nullable=False)
#
#     # Timestamp
#     created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
#
#     # Relationships
#     entry = relationship("KnowledgeBaseEntry", back_populates="embeddings")
#
#     def __repr__(self):
#         return f"<KnowledgeBaseEmbedding(id={self.id}, entry_id={self.entry_id}, model='{self.model}')>"


# Example metadata structures for different entry types:

"""
COMPANY_INFO metadata example:
{
    "company_name": "FlipTech Pro",
    "industry": "Real Estate Technology",
    "founded": "2024",
    "specialties": ["house flipping", "lead generation", "AI automation"]
}

SERVICE_DESCRIPTION metadata example:
{
    "service_name": "AI Lead Generation",
    "pricing_model": "subscription",
    "features": ["automated scraping", "email finding", "lead scoring"],
    "target_audience": "real estate investors"
}

FAQ metadata example:
{
    "question": "What is your response time?",
    "answer": "We respond within 24 hours",
    "related_categories": ["customer_service", "support"]
}

SEARCH_RULE metadata example:
{
    "platform": "craigslist",
    "search_keywords": ["handyman special", "fixer upper"],
    "exclude_keywords": ["rental", "lease"],
    "price_range": {"min": 50000, "max": 300000}
}

QUALIFICATION_RULE metadata example:
{
    "rule_name": "High Value Lead",
    "criteria": {
        "min_price": 100000,
        "property_condition": ["fixer", "needs work"],
        "response_time": "< 48 hours"
    },
    "score_weight": 0.8
}

SCRAPING_PATTERN metadata example:
{
    "platform": "craigslist",
    "selectors": {
        "title": ".result-title",
        "price": ".result-price",
        "location": ".result-hood"
    },
    "extraction_rules": {
        "phone": r"\d{3}-\d{3}-\d{4}"
    }
}
"""
