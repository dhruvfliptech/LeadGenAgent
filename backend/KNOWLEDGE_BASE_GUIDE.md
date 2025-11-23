# Knowledge Base System - Complete Guide

## Overview

The Knowledge Base System is the **CORE DIFFERENTIATOR** for FlipTech Pro. It powers all AI agents with contextual knowledge through semantic search using OpenAI embeddings and pgvector.

### What It Powers

1. **Email AI Agent** - Contextual, personalized email responses
2. **Deep Search Agent** - Scraping rules, search criteria, patterns
3. **Lead Qualification** - Company info, ideal customer profiles
4. **Auto-Response Rules** - Business policies, FAQs, service descriptions

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Knowledge Base System                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────┐     ┌──────────────┐                     │
│  │   FastAPI     │────▶│   Service    │                     │
│  │   Endpoints   │     │    Layer     │                     │
│  └───────────────┘     └──────┬───────┘                     │
│                                │                              │
│                       ┌────────▼────────┐                    │
│                       │  OpenAI API     │                    │
│                       │  (Embeddings)   │                    │
│                       └────────┬────────┘                    │
│                                │                              │
│  ┌────────────────────────────▼─────────────────────────┐   │
│  │           PostgreSQL + pgvector                       │   │
│  │  ┌──────────────────┐  ┌─────────────────────────┐   │   │
│  │  │  knowledge_base  │  │  knowledge_base_        │   │   │
│  │  │     _entries     │  │    embeddings           │   │   │
│  │  │                  │  │                         │   │   │
│  │  │  - entry_type    │  │  - embedding (1536d)   │   │   │
│  │  │  - title         │  │  - cosine similarity   │   │   │
│  │  │  - content       │  │                         │   │   │
│  │  │  - metadata      │  │                         │   │   │
│  │  │  - tags          │  │                         │   │   │
│  │  └──────────────────┘  └─────────────────────────┘   │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Setup Instructions

### 1. Install Dependencies

```bash
cd /Users/greenmachine2.0/Craigslist/backend
pip install pgvector openai sqlalchemy
```

### 2. Configure OpenAI API Key

Add to your `.env` file:

```bash
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

**Important:** The system will work without OpenAI, but will fall back to text search instead of semantic search.

### 3. Run Database Migration

```bash
# Make sure pgvector extension is enabled
psql your_database -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run the migration
alembic upgrade head
```

This creates:
- `knowledge_base_entries` table
- `knowledge_base_embeddings` table with vector index
- Triggers for automatic timestamp updates

### 4. Start the Server

```bash
cd /Users/greenmachine2.0/Craigslist/backend
python -m uvicorn app.main:app --reload --port 8000
```

### 5. Verify Installation

```bash
curl http://localhost:8000/api/v1/knowledge/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "openai_configured": true,
  "total_entries": 0,
  "total_embeddings": 0
}
```

---

## API Endpoints

### Base URL: `/api/v1/knowledge`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/entries` | Create new entry (auto-generates embedding) |
| GET | `/entries` | List entries with filters and pagination |
| GET | `/entries/{id}` | Get single entry by ID |
| PUT | `/entries/{id}` | Update entry (regenerates embedding if content changed) |
| DELETE | `/entries/{id}` | Delete entry (cascade deletes embedding) |
| POST | `/search` | Semantic search using vector similarity |
| POST | `/query` | Query for AI agents (returns structured context) |
| GET | `/stats` | Get knowledge base statistics |
| GET | `/health` | Health check |

---

## Entry Types

```python
class EntryType:
    COMPANY_INFO = "company_info"              # Company information
    SERVICE_DESCRIPTION = "service_description"  # Services offered
    FAQ = "faq"                                 # Frequently asked questions
    SEARCH_RULE = "search_rule"                 # Scraping search criteria
    QUALIFICATION_RULE = "qualification_rule"    # Lead qualification rules
    SCRAPING_PATTERN = "scraping_pattern"       # Web scraping patterns
    BUSINESS_POLICY = "business_policy"         # Business policies
    RESPONSE_GUIDELINE = "response_guideline"   # Email response guidelines
    CUSTOMER_PROFILE = "customer_profile"       # Ideal customer profiles
    INDUSTRY_KNOWLEDGE = "industry_knowledge"   # Industry insights
```

---

## Usage Examples

### 1. Create a FAQ Entry

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/entries \
  -H "Content-Type: application/json" \
  -d '{
    "entry_type": "faq",
    "title": "What is our response time?",
    "content": "We respond to all leads within 24 hours during business days. For urgent inquiries, we provide same-day responses. Our team monitors emails Monday-Friday, 9 AM to 6 PM EST.",
    "metadata": {
      "question": "What is your response time?",
      "related_topics": ["customer_service", "response_time"]
    },
    "tags": ["faq", "customer_service", "timing"],
    "category": "customer_support",
    "priority": 80
  }'
```

### 2. Create a Service Description

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/entries \
  -H "Content-Type: application/json" \
  -d '{
    "entry_type": "service_description",
    "title": "House Flipping Wholesale Service",
    "content": "We specialize in identifying undervalued properties perfect for house flipping. Our service includes: automated lead generation from Craigslist and other platforms, property analysis, seller contact management, and deal structuring. We focus on distressed properties, fixer-uppers, and motivated sellers in the $50k-$300k range.",
    "metadata": {
      "service_name": "House Flipping Wholesale",
      "pricing_model": "commission",
      "target_properties": ["fixer-upper", "distressed", "motivated seller"],
      "price_range": {"min": 50000, "max": 300000}
    },
    "tags": ["service", "house_flipping", "wholesale"],
    "category": "services",
    "priority": 95
  }'
```

### 3. Create a Search Rule

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/entries \
  -H "Content-Type: application/json" \
  -d '{
    "entry_type": "search_rule",
    "title": "Craigslist Fixer-Upper Search Criteria",
    "content": "When searching Craigslist for potential properties, look for keywords: handyman special, fixer upper, needs work, TLC, as-is, cash only, motivated seller. Avoid: rental, lease, room for rent. Target price range: $50k-$300k. Focus on categories: real estate for sale, housing.",
    "metadata": {
      "platform": "craigslist",
      "include_keywords": ["handyman special", "fixer upper", "needs work", "TLC", "as-is", "cash only", "motivated seller"],
      "exclude_keywords": ["rental", "lease", "room for rent"],
      "price_range": {"min": 50000, "max": 300000},
      "categories": ["real estate for sale", "housing"]
    },
    "tags": ["search", "craigslist", "criteria"],
    "category": "scraping",
    "priority": 90
  }'
```

### 4. Create a Qualification Rule

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/entries \
  -H "Content-Type: application/json" \
  -d '{
    "entry_type": "qualification_rule",
    "title": "High-Value Lead Criteria",
    "content": "A lead qualifies as high-value if: property price is between $100k-$250k, listing mentions motivated seller or needs quick sale, property condition is fixer/needs work, location is in target zip codes, seller responds within 48 hours, and contact information is available.",
    "metadata": {
      "rule_name": "High Value Lead",
      "criteria": {
        "price_range": {"min": 100000, "max": 250000},
        "keywords": ["motivated seller", "quick sale", "needs work"],
        "response_time": "< 48 hours",
        "contact_required": true
      },
      "score_weight": 0.85
    },
    "tags": ["qualification", "scoring", "high_value"],
    "category": "lead_qualification",
    "priority": 85
  }'
```

### 5. Semantic Search

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How should I respond to a seller asking about our buying process?",
    "entry_types": ["faq", "service_description", "business_policy"],
    "limit": 5,
    "min_similarity": 0.75
  }'
```

Response:
```json
{
  "query": "How should I respond to a seller asking about our buying process?",
  "results": [
    {
      "entry": {
        "id": 2,
        "entry_type": "service_description",
        "title": "House Flipping Wholesale Service",
        "content": "We specialize in...",
        "priority": 95
      },
      "similarity": 0.89,
      "rank": 1
    }
  ],
  "total_results": 3,
  "search_time_ms": 42.3
}
```

### 6. Query for AI Agent

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Generate email response for seller asking about timeline",
    "agent_type": "email_ai_agent",
    "context": {
      "lead_id": 123,
      "property_type": "fixer-upper",
      "asking_price": 150000
    },
    "entry_types": ["faq", "service_description", "response_guideline"],
    "limit": 5
  }'
```

Response:
```json
{
  "query": "Generate email response for seller asking about timeline",
  "agent_type": "email_ai_agent",
  "relevant_entries": [...],
  "combined_context": "[faq] What is our response time?\nWe respond to all leads within 24 hours...\n\n---\n\n[service_description] House Flipping Wholesale Service\nWe specialize in...",
  "metadata": {
    "total_entries_found": 3,
    "average_similarity": 0.82,
    "search_time_ms": 38.7,
    "agent_context": {
      "lead_id": 123,
      "property_type": "fixer-upper",
      "asking_price": 150000
    }
  }
}
```

---

## AI Agent Integration

### Example: Email AI Agent

```python
from app.services.knowledge_base_service import KnowledgeBaseService
from app.schemas.knowledge_base import AgentQueryRequest

# Get database session
db = get_db()

# Initialize service
kb_service = KnowledgeBaseService(db)

# Query for context
agent_request = AgentQueryRequest(
    query="Respond to seller asking about our buying process",
    agent_type="email_ai_agent",
    context={
        "lead_id": 123,
        "property_address": "123 Main St",
        "asking_price": 175000
    },
    entry_types=["service_description", "business_policy", "faq"],
    limit=5
)

result = kb_service.query_for_agent(agent_request)

# Use combined_context in your LLM prompt
system_prompt = f"""
You are an AI assistant for a house flipping company.

Business Context:
{result['combined_context']}

Generate a professional email response.
"""

# Send to OpenAI/Claude/etc
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Seller asks: What is your buying process?"}
    ]
)
```

### Example: Deep Search Agent

```python
from app.schemas.knowledge_base import SemanticSearchRequest

# Search for scraping rules
search_request = SemanticSearchRequest(
    query="Find properties on Craigslist that are good for house flipping",
    entry_types=["search_rule", "scraping_pattern"],
    limit=3,
    min_similarity=0.8
)

results = kb_service.semantic_search(search_request)

# Extract search criteria from results
for result in results:
    entry = result["entry"]
    if entry.entry_type == "search_rule":
        keywords = entry.metadata.get("include_keywords", [])
        exclude = entry.metadata.get("exclude_keywords", [])
        price_range = entry.metadata.get("price_range", {})

        # Use in your scraper
        scraper.search(
            keywords=keywords,
            exclude=exclude,
            min_price=price_range.get("min"),
            max_price=price_range.get("max")
        )
```

---

## Metadata Examples

### Company Info
```json
{
  "company_name": "FlipTech Pro",
  "industry": "Real Estate Technology",
  "founded": "2024",
  "specialties": ["house flipping", "lead generation", "AI automation"],
  "location": "United States",
  "team_size": "5-10"
}
```

### Search Rule
```json
{
  "platform": "craigslist",
  "search_keywords": ["handyman special", "fixer upper"],
  "exclude_keywords": ["rental", "lease"],
  "price_range": {"min": 50000, "max": 300000},
  "categories": ["real estate for sale"],
  "regions": ["sfbay", "losangeles", "sandiego"]
}
```

### Qualification Rule
```json
{
  "rule_name": "High Value Lead",
  "criteria": {
    "min_price": 100000,
    "max_price": 250000,
    "property_condition": ["fixer", "needs work"],
    "response_time": "< 48 hours",
    "contact_required": true
  },
  "score_weight": 0.85,
  "auto_approve": false
}
```

### Scraping Pattern
```json
{
  "platform": "craigslist",
  "selectors": {
    "title": ".result-title",
    "price": ".result-price",
    "location": ".result-hood",
    "description": "#postingbody"
  },
  "extraction_rules": {
    "phone": "\\d{3}-\\d{3}-\\d{4}",
    "email": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
  }
}
```

---

## Best Practices

### 1. Entry Organization

- **Use specific titles**: "Response Time Policy" not "Policy 1"
- **Write clear content**: Make it readable by both humans and AI
- **Add relevant tags**: Help with filtering and discovery
- **Set appropriate priority**: Higher priority = more relevant in search results

### 2. Metadata Strategy

- **Store structured data**: Use metadata for machine-readable information
- **Keep content human-readable**: Content should be understandable text
- **Use consistent schemas**: Standardize metadata per entry type

### 3. Semantic Search Optimization

- **Combine title + content**: Both are embedded for search
- **Use natural language**: Write how users will query
- **Update regularly**: Keep embeddings current by updating entries

### 4. Performance Tips

- **Batch inserts**: Create multiple entries in one transaction
- **Set min_similarity**: Filter out low-quality matches (0.7-0.8 recommended)
- **Limit results**: Don't request more than you need
- **Cache frequently used queries**: Consider caching common agent queries

---

## Monitoring & Maintenance

### Check System Health

```bash
curl http://localhost:8000/api/v1/knowledge/health
```

### Get Statistics

```bash
curl http://localhost:8000/api/v1/knowledge/stats
```

Response:
```json
{
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
  "last_updated": "2024-11-05T10:00:00",
  "openai_configured": true
}
```

### Maintenance Tasks

1. **Clean up inactive entries**: Periodically review and delete unused entries
2. **Update embeddings**: When switching OpenAI models, regenerate all embeddings
3. **Monitor costs**: OpenAI embedding API calls cost money
4. **Audit relevance**: Review search results and adjust content/priority

---

## Troubleshooting

### OpenAI API Not Working

**Symptom:** Embeddings not generated, falls back to text search

**Solution:**
1. Check `.env` file has valid `OPENAI_API_KEY`
2. Verify API key with: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`
3. Check OpenAI billing status
4. Restart the server after adding key

### Vector Index Slow

**Symptom:** Semantic search takes > 1 second

**Solution:**
1. Rebuild vector index: `REINDEX INDEX idx_kb_embedding_vector;`
2. Increase IVFFlat lists parameter (in migration)
3. Consider upgrading to HNSW index for larger datasets

### Low Similarity Scores

**Symptom:** Search results have similarity < 0.5

**Solution:**
1. Rephrase query to match content style
2. Add more entries covering the topic
3. Lower `min_similarity` threshold
4. Review entry content for clarity

---

## File Locations

```
/Users/greenmachine2.0/Craigslist/backend/
├── migrations/versions/
│   └── 020_create_knowledge_base.py       # Database migration
├── app/
│   ├── models/
│   │   └── knowledge_base.py              # SQLAlchemy models
│   ├── schemas/
│   │   └── knowledge_base.py              # Pydantic schemas
│   ├── services/
│   │   └── knowledge_base_service.py      # Service layer with semantic search
│   ├── api/endpoints/
│   │   └── knowledge_base.py              # API endpoints
│   └── main.py                            # Router registration
└── KNOWLEDGE_BASE_GUIDE.md                # This file
```

---

## Next Steps

1. **Add Initial Entries**: Populate with your company's knowledge
2. **Integrate with Email AI**: Use in email response generation
3. **Configure Deep Search**: Add scraping rules and patterns
4. **Set Up Qualification**: Define lead qualification criteria
5. **Monitor Performance**: Track search relevance and adjust

---

## Support

For issues or questions:
1. Check this guide first
2. Review API documentation at `/docs`
3. Check server logs for errors
4. Verify OpenAI API key is valid
5. Test with `/health` endpoint

**The Knowledge Base is the foundation of your AI agents. Keep it updated and organized!**
