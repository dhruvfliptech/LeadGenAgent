# Phase 3 Enhanced Website Analyzer - Quick Reference

## API Endpoints

### Base URL: `http://localhost:8000/api/v1/ai-mvp/`

---

## 1. Design Analysis

**Endpoint:** `POST /analyze-design`

**Speed:** 2-5 seconds

**Request:**
```json
{
  "url": "https://example.com",
  "use_ai": false
}
```

**Response:**
```json
{
  "score": 75,
  "issues": ["Missing viewport meta tag"],
  "strengths": ["Good use of whitespace"],
  "metrics": {
    "layout_type": "flexbox",
    "color_scheme": {"color_count": 8},
    "typography": {"font_count": 3}
  }
}
```

**Analyzes:** Layout, colors, typography, hierarchy, whitespace, responsiveness

---

## 2. SEO Analysis

**Endpoint:** `POST /analyze-seo`

**Speed:** 1-3 seconds

**Request:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "score": 85,
  "issues": ["Missing meta description"],
  "strengths": ["Good title length", "All images have alt text"],
  "details": {
    "title": {"text": "...", "length": 55, "optimal": true},
    "headings": {"h1": 1, "h2": 5},
    "images": {"total": 20, "alt_coverage": 100.0}
  }
}
```

**Checks:** Title, meta description, headings, images, links, mobile, schema, Open Graph

---

## 3. Performance Analysis

**Endpoint:** `POST /analyze-performance`

**Speed:** 10-30 seconds (real page loads)

**Request:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "score": 70,
  "issues": ["Moderate load time (3.2s)"],
  "strengths": ["Optimized page size (2.1MB)"],
  "metrics": {
    "load_times": {
      "dom_content_loaded": 1.5,
      "full_load": 3.2
    },
    "resources": {
      "total_size_mb": 2.1,
      "scripts": 8,
      "images": 12
    }
  }
}
```

**Measures:** Load times, resource sizes, scripts, stylesheets, images, render-blocking

---

## 4. Accessibility Analysis

**Endpoint:** `POST /analyze-accessibility`

**Speed:** 1-3 seconds

**Request:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "score": 70,
  "issues": ["Limited ARIA usage"],
  "strengths": ["Uses semantic HTML"],
  "details": {
    "aria": {"labels": 3, "roles": 5},
    "semantic_html": {"header": 1, "nav": 2, "main": 1},
    "forms": {"total_inputs": 8, "label_coverage": 75.0}
  }
}
```

**Checks:** ARIA, semantic HTML, form labels, image alt text, link text, lang, skip links

---

## 5. Comprehensive Analysis

**Endpoint:** `POST /analyze-comprehensive`

**Speed:** 15-45 seconds (all analyses)

**Request:**
```json
{
  "url": "https://example.com",
  "include_ai_design": false
}
```

**Response:**
```json
{
  "url": "https://example.com",
  "overall_score": 72.5,
  "design": {...},
  "seo": {...},
  "performance": {...},
  "accessibility": {...},
  "title": "Example Corp",
  "meta_description": "..."
}
```

**Includes:** All four analyses + weighted overall score

**Weights:** Design (25%), SEO (30%), Performance (25%), Accessibility (20%)

---

## Python Usage

### Import:
```python
from app.services.ai_mvp import WebsiteAnalyzer, AICouncil, AICouncilConfig
```

### Initialize:
```python
ai_config = AICouncilConfig(openrouter_api_key=os.getenv("OPENROUTER_API_KEY"))
ai_council = AICouncil(ai_config, gym_tracker=None)
```

### Analyze:
```python
async with WebsiteAnalyzer(ai_council) as analyzer:
    # Individual analysis
    seo_result = await analyzer.analyze_seo("https://example.com")

    # Comprehensive analysis
    full_result = await analyzer.analyze_website_comprehensive(
        url="https://example.com",
        include_ai_design=False
    )
```

---

## Scoring Guide

| Score | Rating | Meaning |
|-------|--------|---------|
| 90-100 | Excellent | Best practices followed |
| 80-89 | Good | Minor improvements needed |
| 70-79 | Fair | Several issues to address |
| 60-69 | Poor | Significant problems |
| 0-59 | Critical | Major overhaul required |

---

## Cost

| Analysis | AI Cost | Notes |
|----------|---------|-------|
| Design | $0 | $0.002-0.005 if use_ai=true |
| SEO | $0 | No AI used |
| Performance | $0 | No AI used |
| Accessibility | $0 | No AI used |
| Comprehensive | $0 | $0.002-0.005 if include_ai_design=true |

---

## Testing

```bash
# Test the implementation
cd backend
python3 test_phase3_analyzer.py https://example.com

# Or with curl
curl -X POST "http://localhost:8000/api/v1/ai-mvp/analyze-seo" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

---

## Common Use Cases

### 1. Quick SEO Check
```bash
curl -X POST localhost:8000/api/v1/ai-mvp/analyze-seo \
  -H "Content-Type: application/json" \
  -d '{"url": "https://prospect-site.com"}'
```

### 2. Full Audit Report
```bash
curl -X POST localhost:8000/api/v1/ai-mvp/analyze-comprehensive \
  -H "Content-Type: application/json" \
  -d '{"url": "https://prospect-site.com", "include_ai_design": true}'
```

### 3. Performance Only
```bash
curl -X POST localhost:8000/api/v1/ai-mvp/analyze-performance \
  -H "Content-Type: application/json" \
  -d '{"url": "https://prospect-site.com"}'
```

---

## Files

- **Implementation:** `/backend/app/services/ai_mvp/website_analyzer.py`
- **API Endpoints:** `/backend/app/api/endpoints/ai_mvp.py`
- **Documentation:** `/backend/PHASE3_WEBSITE_ANALYZER_ENHANCEMENT.md`
- **Summary:** `/backend/PHASE3_IMPLEMENTATION_SUMMARY.md`
- **Test Script:** `/backend/test_phase3_analyzer.py`
- **Quick Reference:** `/backend/PHASE3_QUICK_REFERENCE.md` (this file)

---

## Support

For issues or questions:
1. Check the comprehensive documentation: `PHASE3_WEBSITE_ANALYZER_ENHANCEMENT.md`
2. Run the test suite: `python3 test_phase3_analyzer.py`
3. Review implementation details: `PHASE3_IMPLEMENTATION_SUMMARY.md`
4. Check API docs: http://localhost:8000/docs (when server is running)
