# Knowledge Base - Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
pip install pgvector openai
```

### 2. Set OpenAI API Key
Add to `/Users/greenmachine2.0/Craigslist/backend/.env`:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### 3. Run Migration
```bash
cd /Users/greenmachine2.0/Craigslist/backend
alembic upgrade head
```

### 4. Populate with Examples
```bash
python examples/populate_knowledge_base.py
```

### 5. Test the API
```bash
# Start server
python -m uvicorn app.main:app --reload --port 8000

# Test search (in another terminal)
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How should I respond to a motivated seller?",
    "limit": 3
  }'
```

---

## Essential Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/knowledge/entries` | POST | Create entry |
| `/api/v1/knowledge/search` | POST | Semantic search |
| `/api/v1/knowledge/query` | POST | Query for AI agents |
| `/api/v1/knowledge/stats` | GET | Get statistics |

---

## Common Use Cases

### 1. Add Company Info
```bash
curl -X POST http://localhost:8000/api/v1/knowledge/entries \
  -H "Content-Type: application/json" \
  -d '{
    "entry_type": "company_info",
    "title": "About Our Company",
    "content": "We are a house flipping company...",
    "category": "company",
    "priority": 90
  }'
```

### 2. Search for Context
```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "property buying process",
    "entry_types": ["faq", "service_description"],
    "limit": 5
  }'
```

### 3. Get Agent Context
```bash
curl -X POST http://localhost:8000/api/v1/knowledge/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Generate email for motivated seller",
    "agent_type": "email_ai_agent",
    "limit": 5
  }'
```

---

## Python Integration

```python
from app.services.knowledge_base_service import KnowledgeBaseService
from app.schemas.knowledge_base import SemanticSearchRequest

# Search
db = get_db()
kb_service = KnowledgeBaseService(db)

search_request = SemanticSearchRequest(
    query="How do we handle urgent inquiries?",
    entry_types=["faq", "business_policy"],
    limit=5
)

results = kb_service.semantic_search(search_request)

for result in results:
    print(f"Similarity: {result['similarity']:.2f}")
    print(f"Title: {result['entry'].title}")
    print(f"Content: {result['entry'].content}\n")
```

---

## Entry Types Reference

- `company_info` - Company background, values, mission
- `service_description` - Services offered, features
- `faq` - Frequently asked questions
- `search_rule` - Scraping search criteria
- `qualification_rule` - Lead scoring rules
- `scraping_pattern` - Web scraping patterns
- `business_policy` - Business policies, terms
- `response_guideline` - Email response guidelines
- `customer_profile` - Ideal customer profiles
- `industry_knowledge` - Industry insights

---

## File Locations

```
/Users/greenmachine2.0/Craigslist/backend/
├── migrations/versions/020_create_knowledge_base.py
├── app/models/knowledge_base.py
├── app/schemas/knowledge_base.py
├── app/services/knowledge_base_service.py
├── app/api/endpoints/knowledge_base.py
├── examples/populate_knowledge_base.py
├── KNOWLEDGE_BASE_GUIDE.md (full documentation)
└── KNOWLEDGE_BASE_QUICK_START.md (this file)
```

---

## Troubleshooting

**OpenAI not working?**
- Check `.env` has valid `OPENAI_API_KEY`
- Restart server after adding key
- Falls back to text search if missing

**Slow searches?**
- Check database has vector index
- Reduce `limit` parameter
- Increase `min_similarity` threshold

**No results?**
- Lower `min_similarity` (try 0.6-0.7)
- Add more relevant entries
- Check entry `is_active=true`

---

## Next Steps

1. Read full guide: `KNOWLEDGE_BASE_GUIDE.md`
2. View API docs: http://localhost:8000/docs
3. Check examples: `/examples/populate_knowledge_base.py`
4. Integrate with AI agents
5. Monitor with `/stats` endpoint

**Your knowledge base is ready to power AI agents!**
