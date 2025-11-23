# Website Analysis Agent - Quick Start Guide

## TL;DR

AI-powered website analyzer that generates actionable improvement recommendations using GPT-4, Claude, Qwen, or Grok.

**API Endpoint**: `POST /api/v1/website-analysis/analyze`

---

## Quick Start

### 1. Start Backend

```bash
cd /Users/greenmachine2.0/Craigslist/backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 2. Analyze a Website

```bash
curl -X POST http://localhost:8000/api/v1/website-analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "depth": "comprehensive",
    "include_screenshot": true
  }'
```

### 3. View Results

Open http://localhost:8000/docs and test the endpoints interactively.

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/website-analysis/analyze` | POST | Analyze a website |
| `/api/v1/website-analysis/analysis/{id}` | GET | Get analysis by ID |
| `/api/v1/website-analysis/analyses` | GET | List all analyses |
| `/api/v1/website-analysis/analysis/{id}/screenshot` | GET | Download screenshot |
| `/api/v1/website-analysis/analysis/{id}` | DELETE | Delete analysis |
| `/api/v1/website-analysis/stats` | GET | Get statistics |

---

## Request Examples

### Comprehensive Analysis

```bash
curl -X POST http://localhost:8000/api/v1/website-analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://stripe.com",
    "depth": "comprehensive",
    "include_screenshot": true,
    "ai_model": "openai/gpt-4-turbo-preview"
  }'
```

### Quick Analysis (Faster, Cheaper)

```bash
curl -X POST http://localhost:8000/api/v1/website-analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "depth": "quick",
    "include_screenshot": false
  }'
```

### Use Claude 3.5 (Best Balance)

```bash
curl -X POST http://localhost:8000/api/v1/website-analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "ai_model": "anthropic/claude-3.5-sonnet"
  }'
```

### Use Qwen (Cheapest)

```bash
curl -X POST http://localhost:8000/api/v1/website-analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "ai_model": "qwen/qwen-2.5-72b-instruct"
  }'
```

---

## Response Example

```json
{
  "id": 1,
  "url": "https://example.com",
  "status": "completed",
  "overall_score": 78.5,
  "design": {
    "score": 75,
    "summary": "Simple, clean design",
    "strengths": ["Clear typography", "Good contrast"],
    "weaknesses": ["Limited visual hierarchy"]
  },
  "seo": {
    "score": 65,
    "summary": "Missing key meta tags",
    "strengths": ["Has SSL", "Mobile-friendly"],
    "weaknesses": ["No meta description", "No sitemap"]
  },
  "performance": {
    "score": 92,
    "summary": "Excellent load time",
    "strengths": ["Fast load (523ms)", "Small page size (12KB)"],
    "weaknesses": []
  },
  "accessibility": {
    "score": 82,
    "summary": "Good semantic HTML",
    "strengths": ["Semantic HTML", "Good heading structure"],
    "weaknesses": ["Missing ARIA labels"]
  },
  "improvements": [
    {
      "id": "seo-1",
      "category": "seo",
      "priority": "high",
      "difficulty": "easy",
      "title": "Add meta description",
      "description": "Add a meta description tag for better SEO",
      "impact": "Improve search engine visibility by 20-30%",
      "code_example": "<meta name=\"description\" content=\"Your description here\">",
      "estimated_time": "5 minutes"
    }
  ],
  "cost": {
    "ai_cost": 0.0234,
    "processing_time_seconds": 8.45
  }
}
```

---

## What Gets Analyzed

### 1. Design
- Color scheme
- Typography
- Layout and spacing
- Visual hierarchy
- Responsive design

### 2. SEO
- Meta tags (title, description)
- Headers (H1-H6)
- Content structure
- robots.txt
- sitemap.xml
- Mobile-friendly
- SSL certificate

### 3. Performance
- Page load time
- Page size
- Number of resources (images, scripts, CSS)
- Resource optimization opportunities

### 4. Accessibility
- ARIA labels
- Keyboard navigation
- Color contrast
- Semantic HTML
- Screen reader compatibility

---

## Analysis Results Include

✅ **Scores**: 0-100 for each category + overall
✅ **Strengths**: What's working well
✅ **Weaknesses**: What needs improvement
✅ **Improvements**: 5-10 prioritized recommendations
✅ **Code Examples**: Copy-paste ready fixes
✅ **Impact Estimates**: Expected improvement
✅ **Time Estimates**: How long to implement
✅ **Resources**: Helpful links
✅ **Screenshot**: Full-page PNG
✅ **Technical Metrics**: Load time, page size, etc.
✅ **Cost Tracking**: AI usage cost

---

## AI Model Comparison

| Model | Speed | Cost | Quality | Best For |
|-------|-------|------|---------|----------|
| **GPT-4 Turbo** | Medium | High ($0.02-0.05) | Excellent | Premium analysis |
| **Claude 3.5** | Fast | Medium ($0.01-0.03) | Excellent | Balanced choice ⭐ |
| **Qwen 2.5** | Fast | Very Low ($0.001-0.003) | Good | High-volume |
| **Grok** | Medium | Medium ($0.015-0.04) | Good | Creative insights |

**Recommendation**: Use **Claude 3.5 Sonnet** for best balance of cost, speed, and quality.

---

## Python Client

```python
import httpx
import asyncio

async def analyze_website(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/website-analysis/analyze",
            json={
                "url": url,
                "depth": "comprehensive",
                "include_screenshot": True,
                "ai_model": "anthropic/claude-3.5-sonnet"  # Recommended
            },
            timeout=60.0
        )
        response.raise_for_status()
        return response.json()

# Usage
result = asyncio.run(analyze_website("https://example.com"))
print(f"Score: {result['overall_score']}/100")
for improvement in result['improvements'][:3]:
    print(f"- [{improvement['priority']}] {improvement['title']}")
```

---

## JavaScript Client

```javascript
async function analyzeWebsite(url) {
  const response = await fetch(
    'http://localhost:8000/api/v1/website-analysis/analyze',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url,
        depth: 'comprehensive',
        include_screenshot: true,
        ai_model: 'anthropic/claude-3.5-sonnet'
      })
    }
  );

  const result = await response.json();
  console.log(`Score: ${result.overall_score}/100`);
  return result;
}

// Usage
analyzeWebsite('https://example.com')
  .then(result => console.log('Analysis ID:', result.id))
  .catch(error => console.error('Error:', error));
```

---

## Common Use Cases

### 1. Lead Generation

```python
# Analyze prospect's website
analysis = await analyzer.analyze_website(
    url=lead.website,
    depth="comprehensive"
)

# Personalize outreach based on score
if analysis.overall_score < 60:
    email = f"I noticed {len(analysis.improvements)} areas for improvement..."
else:
    email = f"Your website looks great! Here are some optimization ideas..."
```

### 2. Competitor Analysis

```bash
# Analyze competitor websites
for url in competitor_urls:
  curl -X POST http://localhost:8000/api/v1/website-analysis/analyze \
    -d '{"url": "'$url'", "depth": "comprehensive"}'
done

# Compare results
curl http://localhost:8000/api/v1/website-analysis/analyses
```

### 3. Client Reporting

```python
# Generate analysis report
analysis = await get_analysis(analysis_id)

report = f"""
Website Analysis Report
======================

Overall Score: {analysis.overall_score}/100

Key Findings:
- Design: {analysis.design.score}/100
- SEO: {analysis.seo.score}/100
- Performance: {analysis.performance.score}/100
- Accessibility: {analysis.accessibility.score}/100

Top 3 Improvements:
{format_improvements(analysis.improvements[:3])}

Full Report: /api/v1/website-analysis/analysis/{analysis.id}
Screenshot: /api/v1/website-analysis/analysis/{analysis.id}/screenshot
"""
```

---

## Filtering & Searching

```bash
# Get high-scoring sites (80+)
curl "http://localhost:8000/api/v1/website-analysis/analyses?min_score=80"

# Get failed analyses
curl "http://localhost:8000/api/v1/website-analysis/analyses?status=failed"

# Search by domain
curl "http://localhost:8000/api/v1/website-analysis/analyses?domain=example.com"

# Get recent analyses (last page)
curl "http://localhost:8000/api/v1/website-analysis/analyses?page=1&page_size=10"
```

---

## Cost Optimization Tips

1. **Use Quick Mode** for initial screening: `"depth": "quick"`
2. **Use Qwen** for high-volume: `"ai_model": "qwen/qwen-2.5-72b-instruct"`
3. **Skip Screenshot** if not needed: `"include_screenshot": false`
4. **Don't Store HTML** by default: `"store_html": false`
5. **Cache Results** to avoid re-analysis

---

## Troubleshooting

### Analysis Fails

```json
{
  "error": "AnalysisFailed",
  "message": "Timeout loading https://example.com",
  "code": "PlaywrightTimeout"
}
```

**Solutions**:
- Check if URL is accessible
- Try again (timeout may be temporary)
- Use quick mode for faster analysis

### Low Scores

If all scores are low (< 50), check:
- Is the URL correct?
- Is the website accessible?
- Try viewing the screenshot to see what was captured

### Missing Improvements

If `improvements` array is empty:
- AI may have failed (check `error_message`)
- Website may be perfect (score 95+)
- Try with different AI model

---

## Performance Tips

**Typical Analysis Time**: 8-22 seconds

**Speed Up:**
- Use `"depth": "quick"` (30% faster)
- Skip screenshot: `"include_screenshot": false` (20% faster)
- Use faster model: `"ai_model": "qwen/qwen-2.5-72b-instruct"`

**Batch Processing:**
```python
# Analyze multiple sites concurrently
tasks = [
    analyze_website(url1),
    analyze_website(url2),
    analyze_website(url3)
]
results = await asyncio.gather(*tasks)
```

---

## Database Schema

Table: `website_analyses`

Key fields:
- `id` - Primary key
- `url` - Website URL
- `overall_score` - 0-100
- `design_score`, `seo_score`, `performance_score`, `accessibility_score`
- `improvements` - JSONB array
- `screenshot_path` - Local file path
- `ai_cost` - Cost in USD
- `created_at`, `completed_at`

---

## File Locations

**Service**: `/Users/greenmachine2.0/Craigslist/backend/app/services/website_analyzer.py`
**API**: `/Users/greenmachine2.0/Craigslist/backend/app/api/endpoints/website_analysis.py`
**Model**: `/Users/greenmachine2.0/Craigslist/backend/app/models/website_analysis.py`
**Schemas**: `/Users/greenmachine2.0/Craigslist/backend/app/schemas/website_analysis.py`
**Screenshots**: `/Users/greenmachine2.0/Craigslist/backend/exports/screenshots/`

---

## Environment Variables

Required:
```bash
OPENROUTER_API_KEY=your_key_here
DATABASE_URL=postgresql://user:pass@host:port/db
```

Optional:
```bash
AI_MODEL_DEFAULT=openai/gpt-4-turbo-preview
EXPORT_DIRECTORY=/path/to/exports
```

---

## Support

**Documentation**: `/Users/greenmachine2.0/Craigslist/WEBSITE_ANALYZER_IMPLEMENTATION.md`
**API Docs**: http://localhost:8000/docs
**Test Script**: `/Users/greenmachine2.0/Craigslist/backend/test_website_analysis_new.py`

---

## Summary

✅ Analyze any website in 8-22 seconds
✅ Get 0-100 scores for design, SEO, performance, accessibility
✅ Receive 5-10 prioritized improvements with code examples
✅ Choose from 4 AI models (GPT-4, Claude, Qwen, Grok)
✅ Track costs (as low as $0.001 per analysis)
✅ Full REST API with filtering and pagination
✅ Screenshots included
✅ Production ready

**Get Started**: `POST /api/v1/website-analysis/analyze {"url": "https://example.com"}`
