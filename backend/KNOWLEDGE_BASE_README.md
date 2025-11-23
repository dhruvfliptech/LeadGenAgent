# Knowledge Base System - README

## What This Does

The Knowledge Base System is the **intelligence layer** that powers all AI agents in FlipTech Pro. It uses:

- **OpenAI embeddings** to understand semantic meaning
- **pgvector** for fast similarity search in PostgreSQL
- **REST API** for easy integration

Think of it as a **smart memory** that AI agents can query to get relevant context.

---

## Quick Start (3 Commands)

```bash
# 1. Set your OpenAI API key in .env
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# 2. Run database migration
alembic upgrade head

# 3. Populate with example data
python examples/populate_knowledge_base.py
```

**That's it!** Your knowledge base is ready.

---

## What Gets Created

### Database Tables

1. **knowledge_base_entries** - Your knowledge entries
   - Company info, FAQs, policies, search rules, etc.
   - Flexible JSON metadata
   - Tags and categories

2. **knowledge_base_embeddings** - Vector search index
   - 1536-dimension vectors (OpenAI)
   - Cosine similarity search
   - Automatic updates

### API Endpoints

All available at `/api/v1/knowledge/*`:

```
POST   /entries          # Create new entry
GET    /entries          # List all entries
GET    /entries/{id}     # Get one entry
PUT    /entries/{id}     # Update entry
DELETE /entries/{id}     # Delete entry
POST   /search           # Semantic search
POST   /query            # Query for AI agents
GET    /stats            # System stats
GET    /health           # Health check
```

### Example Knowledge

15 pre-populated entries covering:
- Company information
- Service descriptions
- FAQs about your business
- Search rules for web scraping
- Lead qualification criteria
- Email response guidelines
- Customer profiles

---

## How AI Agents Use It

### Email AI Agent
```python
# Get context for email response
context = kb_service.query_for_agent(
    query="Respond to motivated seller inquiry",
    agent_type="email_ai_agent"
)

# Use in LLM prompt
prompt = f"Context: {context['combined_context']}\n\nGenerate email..."
```

### Deep Search Agent
```python
# Get scraping rules
rules = kb_service.semantic_search(
    query="Craigslist fixer-upper criteria",
    entry_types=["search_rule"]
)

# Configure scraper
keywords = rules[0]['entry'].metadata_json['include_keywords']
```

### Lead Qualifier
```python
# Get qualification rules
rules = kb_service.semantic_search(
    query="High value lead criteria",
    entry_types=["qualification_rule"]
)

# Score lead
score = apply_rules(lead, rules)
```

---

## Why This Matters

**Before Knowledge Base:**
- Hard-coded business rules in code
- Manual context for each email
- No semantic understanding
- Difficult to update policies

**After Knowledge Base:**
- Business rules in database (easy to update)
- AI automatically finds relevant context
- Semantic search understands intent
- Update knowledge without code changes

**Result:** More intelligent, flexible, maintainable AI agents.

---

## Testing It

### 1. Check Health
```bash
curl http://localhost:8000/api/v1/knowledge/health
```

Should return:
```json
{
  "status": "healthy",
  "openai_configured": true,
  "total_entries": 15,
  "total_embeddings": 15
}
```

### 2. Try Semantic Search
```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What do we tell sellers about response time?",
    "limit": 3
  }'
```

Should return FAQs with similarity scores > 0.7

### 3. View in Browser
Go to: http://localhost:8000/docs

Try the `/api/v1/knowledge/search` endpoint interactively.

---

## Common Operations

### Add New Company Info
```bash
curl -X POST http://localhost:8000/api/v1/knowledge/entries \
  -H "Content-Type: application/json" \
  -d '{
    "entry_type": "company_info",
    "title": "Our Company Values",
    "content": "We value integrity, speed, and win-win deals...",
    "category": "company",
    "priority": 85
  }'
```

### Update an Entry
```bash
curl -X PUT http://localhost:8000/api/v1/knowledge/entries/1 \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Updated content here...",
    "priority": 95
  }'
```

### Search for Anything
```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "your question here",
    "limit": 5,
    "min_similarity": 0.7
  }'
```

---

## Costs

**OpenAI Embeddings Pricing:**
- $0.0001 per 1,000 tokens
- Average entry: ~500 tokens = $0.00005
- 1,000 entries: ~$0.05
- 10,000 searches/month: ~$1

**Very affordable for most use cases.**

---

## Files You Need to Know

```
backend/
├── migrations/versions/
│   └── 020_create_knowledge_base.py        # Database setup
│
├── app/
│   ├── models/knowledge_base.py            # Database models
│   ├── schemas/knowledge_base.py           # API schemas
│   ├── services/knowledge_base_service.py  # Business logic
│   └── api/endpoints/knowledge_base.py     # API endpoints
│
├── examples/
│   └── populate_knowledge_base.py          # Example data
│
└── Documentation:
    ├── KNOWLEDGE_BASE_README.md            # This file (start here)
    ├── KNOWLEDGE_BASE_QUICK_START.md       # Quick reference
    ├── KNOWLEDGE_BASE_GUIDE.md             # Complete guide
    └── KNOWLEDGE_BASE_IMPLEMENTATION_SUMMARY.md  # Technical details
```

**Start with this README, then:**
1. Quick Start → Get it running fast
2. Guide → Learn everything
3. Implementation Summary → Technical deep dive

---

## Troubleshooting

### "OpenAI not configured"
**Fix:** Add `OPENAI_API_KEY` to `.env` file and restart server

### "No results found"
**Fix:**
- Make sure you ran `populate_knowledge_base.py`
- Lower `min_similarity` to 0.6
- Check entries are `is_active=true`

### "Slow searches"
**Fix:**
- Check database has vector index
- Reduce `limit` parameter
- Consider upgrading to HNSW index for large datasets

### "Import errors"
**Fix:**
```bash
pip install pgvector openai
```

---

## Next Steps

1. **Customize the knowledge** - Edit example entries to match your business
2. **Add more entries** - Use the API to add your own knowledge
3. **Integrate with agents** - Update email AI, scraper, qualifier
4. **Monitor usage** - Check `/stats` endpoint regularly
5. **Optimize** - Adjust similarity thresholds based on results

---

## Support

- Full documentation: `KNOWLEDGE_BASE_GUIDE.md`
- API docs: http://localhost:8000/docs
- Quick reference: `KNOWLEDGE_BASE_QUICK_START.md`

---

## The Big Picture

```
┌─────────────────────────────────────────────────┐
│         Knowledge Base System                    │
│                                                  │
│  Your business knowledge + OpenAI embeddings    │
│  = Smart context for AI agents                   │
│                                                  │
│  Benefits:                                       │
│  ✓ Semantic understanding                        │
│  ✓ Context-aware AI                              │
│  ✓ Easy to update                                │
│  ✓ No code changes needed                        │
│  ✓ Scales with your business                     │
└─────────────────────────────────────────────────┘
```

**This is what makes your AI agents intelligent.**

---

**Ready to start?** Run the 3 commands at the top and you're live! 🚀
