# Phase 3 Quick Reference Guide

Complete guide to Phase 3 website analysis and improvement planning features.

## Overview

Phase 3 adds comprehensive website analysis and AI-powered improvement planning to the Craigslist Lead Generation system.

```
┌─────────────────────────────────────────────────────────────┐
│                     Phase 3 Workflow                        │
│                                                             │
│  1. Scrape Website URL from Craigslist ad                  │
│              ↓                                              │
│  2. Analyze Website (Design, SEO, Performance, A11y)       │
│              ↓                                              │
│  3. Generate Improvement Plan (AI-powered)                 │
│              ↓                                              │
│  4. Export Plan (JSON, Markdown)                           │
│              ↓                                              │
│  5. Use insights in outreach email                         │
└─────────────────────────────────────────────────────────────┘
```

## API Endpoints

Base URL: `http://localhost:8000/api/v1/ai-mvp`

### 1. Analyze Website (Basic)

**Endpoint**: `POST /analyze-website`

**Purpose**: Quick business analysis of a website

**Request**:
```json
{
  "url": "https://example.com",
  "lead_value": 50000,
  "lead_id": 123
}
```

**Response**:
```json
{
  "url": "https://example.com",
  "title": "Example Corp - Web Services",
  "meta_description": "We build websites",
  "content_length": 5432,
  "ai_analysis": "BUSINESS ANALYSIS:\n- Company: Example Corp\n...",
  "ai_model": "anthropic/claude-sonnet-4",
  "ai_cost": 0.012,
  "ai_request_id": 1
}
```

**Cost**: $0.003-0.012 (depends on lead value)

---

### 2. Comprehensive Analysis

**Endpoint**: `POST /analyze-comprehensive`

**Purpose**: Full analysis with design, SEO, performance, and accessibility

**Request**:
```json
{
  "url": "https://example.com",
  "include_ai_design": false
}
```

**Response**:
```json
{
  "url": "https://example.com",
  "overall_score": 72.5,
  "design": {
    "score": 75,
    "issues": ["Poor color contrast on CTA buttons"],
    "strengths": ["Clean layout", "Good typography"],
    "metrics": {
      "has_responsive_design": true,
      "has_grid_layout": true,
      "color_count": 8
    }
  },
  "seo": {
    "score": 85,
    "issues": ["Meta description too short"],
    "strengths": ["Good H1 structure", "All images have alt text"],
    "details": {
      "title_length": 55,
      "meta_description_length": 120,
      "h1_count": 1,
      "images_with_alt": 12
    }
  },
  "performance": {
    "score": 60,
    "issues": ["Slow page load time (4.2s)"],
    "strengths": ["Optimized page size (2.1MB)"],
    "metrics": {
      "page_load_time": 4.2,
      "total_size_mb": 2.1,
      "script_count": 8
    }
  },
  "accessibility": {
    "score": 70,
    "issues": ["Some form inputs lack labels"],
    "strengths": ["Uses semantic HTML", "Has lang attribute"],
    "details": {
      "has_semantic_html": true,
      "form_labels_count": 3,
      "aria_labels_count": 5
    }
  },
  "title": "Example Corp - Web Services",
  "meta_description": "We provide professional web development..."
}
```

**Time**: 15-45 seconds
**Cost**: $0.002-0.007 (if using AI design assessment)

---

### 3. Generate Improvement Plan

**Endpoint**: `POST /generate-improvement-plan`

**Purpose**: AI-powered improvement recommendations

**Request**:
```json
{
  "url": "https://example.com",
  "analysis_result": {
    "url": "https://example.com",
    "title": "Example Corp - Web Services",
    "ai_analysis": "...from analyze-website endpoint...",
    "ai_model": "anthropic/claude-sonnet-4",
    "ai_cost": 0.012
  },
  "industry": "Web Development Services",
  "focus_areas": ["conversion", "performance"],
  "lead_value": 50000.0
}
```

**Response**:
```json
{
  "url": "https://example.com",
  "analyzed_at": "2025-01-15T10:30:00",
  "improvements": [
    {
      "id": "imp_001",
      "category": "conversion",
      "priority": "critical",
      "title": "Add Clear Call-to-Action Above the Fold",
      "description": "Website lacks a prominent CTA...",
      "current_state": "Missing primary call-to-action",
      "proposed_change": "Add prominent CTA button above fold",
      "impact": "40-60% increase in conversion rate",
      "difficulty": "easy",
      "time_estimate": "1 hour",
      "code_example": "<button class=\"cta-primary\">Get Started →</button>",
      "resources": ["https://www.nngroup.com/articles/call-to-action-buttons/"]
    }
  ],
  "summary": {
    "total_improvements": 12,
    "critical_priority": 1,
    "high_priority": 4,
    "medium_priority": 5,
    "low_priority": 2,
    "estimated_total_impact": "40-60% overall improvement",
    "estimated_total_time": "18 hours",
    "quick_wins": 3,
    "categories": {
      "conversion": 3,
      "performance": 2,
      "seo": 3
    }
  }
}
```

**Time**: 2-8 seconds
**Cost**: $0.003-0.015

---

### 4. Individual Analyzers

#### Design Analysis
**Endpoint**: `POST /analyze-design`

```json
{
  "url": "https://example.com",
  "use_ai": false
}
```

#### SEO Analysis
**Endpoint**: `POST /analyze-seo`

```json
{
  "url": "https://example.com"
}
```

#### Performance Analysis
**Endpoint**: `POST /analyze-performance`

```json
{
  "url": "https://example.com"
}
```

#### Accessibility Analysis
**Endpoint**: `POST /analyze-accessibility`

```json
{
  "url": "https://example.com"
}
```

---

## Python Usage Examples

### Complete Workflow

```python
from app.services.ai_mvp import WebsiteAnalyzer, AICouncil, AICouncilConfig
from app.services.improvement_planner import ImprovementPlanner

# Initialize AI Council
config = AICouncilConfig(openrouter_api_key="sk-or-v1-...")
ai_council = AICouncil(config=config)

# Step 1: Analyze website
async with WebsiteAnalyzer(ai_council) as analyzer:
    analysis = await analyzer.analyze_website(
        url="https://example.com",
        lead_value=50000.0
    )

# Step 2: Generate improvement plan
planner = ImprovementPlanner(ai_council=ai_council)
plan = await planner.generate_plan(
    analysis_result=analysis,
    industry="Web Development",
    focus_areas=["conversion", "performance"],
    lead_value=50000.0
)

# Step 3: Export results
markdown = planner.export_to_markdown(plan)
json_output = planner.export_to_json(plan)

# Step 4: Access specific improvements
for imp in plan.improvements[:5]:  # Top 5
    print(f"{imp.priority.upper()}: {imp.title}")
    print(f"  Impact: {imp.impact}")
    print(f"  Time: {imp.time_estimate}")
    if imp.code_example:
        print(f"  Code: {imp.code_example[:100]}...")

await ai_council.close()
```

### Quick Analysis

```python
from app.services.ai_mvp import analyze_website_quick, AICouncil, AICouncilConfig

config = AICouncilConfig(openrouter_api_key="sk-or-v1-...")
ai_council = AICouncil(config=config)

# Quick analysis (auto-manages browser)
result = await analyze_website_quick(
    url="https://example.com",
    ai_council=ai_council,
    lead_value=50000.0
)

print(result["ai_analysis"])
await ai_council.close()
```

---

## cURL Examples

### 1. Analyze Website

```bash
curl -X POST "http://localhost:8000/api/v1/ai-mvp/analyze-website" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "lead_value": 50000,
    "lead_id": 123
  }'
```

### 2. Comprehensive Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/ai-mvp/analyze-comprehensive" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "include_ai_design": false
  }'
```

### 3. Generate Improvement Plan

```bash
curl -X POST "http://localhost:8000/api/v1/ai-mvp/generate-improvement-plan" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "analysis_result": {
      "url": "https://example.com",
      "title": "Example Corp",
      "ai_analysis": "Company provides web services...",
      "ai_model": "anthropic/claude-sonnet-4",
      "ai_cost": 0.012
    },
    "industry": "Web Development",
    "focus_areas": ["conversion", "performance"],
    "lead_value": 50000.0
  }'
```

---

## Cost Breakdown

| Operation | Time | Cost | Model |
|-----------|------|------|-------|
| Basic Website Analysis | 5-15s | $0.003-0.012 | Routed by value |
| Comprehensive Analysis | 15-45s | $0.002-0.007 | Optional AI |
| Improvement Plan | 2-8s | $0.003-0.015 | Routed by value |
| **Total Workflow** | **22-68s** | **$0.006-0.034** | Mixed |

### Model Routing

| Lead Value | Model | Cost/1K tokens |
|------------|-------|----------------|
| $0-25K | Qwen 2.5 72B | $0.0003 |
| $25K-100K | DeepSeek-V3 | $0.008 |
| $100K+ | Claude Sonnet 4 | $0.015 |

---

## Priority Levels

| Priority | When to Use | Example |
|----------|-------------|---------|
| **Critical** | Blocking conversions/revenue | Missing CTA, broken checkout |
| **High** | Significant UX/SEO impact | Slow load time, poor mobile |
| **Medium** | Moderate improvements | Meta description, image alt |
| **Low** | Nice-to-have enhancements | Footer links, favicon |

---

## Improvement Categories

| Category | Focus | Examples |
|----------|-------|----------|
| **conversion** | Increase conversions | CTAs, forms, trust signals |
| **performance** | Speed optimization | Image compression, caching |
| **seo** | Search ranking | Meta tags, structured data |
| **accessibility** | WCAG compliance | Alt text, ARIA labels |
| **design** | Visual improvements | Color contrast, typography |
| **ux** | User experience | Navigation, mobile layout |
| **content** | Copy improvements | Headlines, value props |
| **technical** | Code/infrastructure | HTTPS, mobile responsive |

---

## Quick Reference: Improvement Plan Structure

```javascript
{
  improvements: [
    {
      id: "imp_001",              // Unique ID
      category: "conversion",     // Category (see table above)
      priority: "critical",       // Priority level
      title: "Add Clear CTA",     // Action-oriented title
      description: "...",         // 2-3 sentence explanation
      current_state: "...",       // What's happening now
      proposed_change: "...",     // Specific recommendation
      impact: "40-60% increase",  // Estimated improvement
      difficulty: "easy",         // easy/medium/hard
      time_estimate: "1 hour",    // Realistic time
      code_example: "<button>",   // Concrete implementation
      resources: ["url1"],        // Helpful links
      dependencies: []            // Related improvements
    }
  ],
  summary: {
    total_improvements: 12,
    critical_priority: 1,
    high_priority: 4,
    medium_priority: 5,
    low_priority: 2,
    estimated_total_impact: "40-60% overall",
    estimated_total_time: "18 hours",
    quick_wins: 3,                // High impact + easy
    categories: {
      "conversion": 3,
      "performance": 2
    }
  }
}
```

---

## Environment Variables

Required for Phase 3:

```bash
# OpenRouter API (required for AI features)
OPENROUTER_API_KEY="sk-or-v1-..."

# Optional: Force specific AI provider
AI_PROVIDER="openai"  # or "anthropic"
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."

# Optional: AI settings
AI_MAX_TOKENS=2000
AI_TEMPERATURE=0.7
AI_TIMEOUT_SECONDS=30
```

---

## Testing

### Run Test Scripts

```bash
cd /Users/greenmachine2.0/Craigslist/backend

# Test website analyzer
python test_website_analyzer.py

# Test improvement planner
export OPENROUTER_API_KEY="sk-or-v1-..."
python test_improvement_planner.py
```

### Check API Status

```bash
# Health check
curl http://localhost:8000/health

# AI-GYM stats
curl http://localhost:8000/api/v1/ai-mvp/stats

# Model performance
curl http://localhost:8000/api/v1/ai-mvp/performance
```

---

## Common Use Cases

### Use Case 1: Quick Lead Assessment

```python
# Scrape Craigslist ad for website URL
website_url = extract_url_from_ad(ad_text)

# Quick analysis
analysis = await analyze_website_quick(website_url, ai_council)

# Generate simple improvement summary
print(analysis["ai_analysis"][:500])
```

### Use Case 2: Detailed Audit Report

```python
# Comprehensive analysis
result = await analyzer.analyze_website_comprehensive(
    url=website_url,
    include_ai_design=True
)

# Generate improvement plan
plan = await planner.generate_plan(
    analysis_result=result,
    industry="Web Development",
    focus_areas=["conversion"]
)

# Export to markdown report
report = planner.export_to_markdown(plan)
with open("audit_report.md", "w") as f:
    f.write(report)
```

### Use Case 3: Outreach Email with Insights

```python
# Analyze website
analysis = await analyzer.analyze_website(url, lead_value=50000)

# Generate improvement plan
plan = await planner.generate_plan(analysis_result=analysis)

# Get top 3 quick wins
quick_wins = [
    imp for imp in plan.improvements
    if imp.priority in ["critical", "high"] and imp.difficulty == "easy"
][:3]

# Use in email
email_body = f"""
Hi {prospect_name},

I noticed a few quick wins that could significantly improve your website:

1. {quick_wins[0].title}
   Impact: {quick_wins[0].impact}
   Time to implement: {quick_wins[0].time_estimate}

2. {quick_wins[1].title}
   Impact: {quick_wins[1].impact}
   Time to implement: {quick_wins[1].time_estimate}

Would you be interested in a free 15-minute call to discuss these?
"""
```

---

## Error Handling

### Common Errors

1. **OpenRouter API Key Missing**
   ```
   HTTP 503: AI service not configured - OPENROUTER_API_KEY missing
   ```
   **Solution**: Set `OPENROUTER_API_KEY` environment variable

2. **Website Unreachable**
   ```
   HTTP 500: Website analysis failed: Failed to load https://...
   ```
   **Solution**: Check if URL is valid and accessible

3. **Timeout**
   ```
   HTTP 500: Website analysis failed: Timeout waiting for...
   ```
   **Solution**: Increase `fetch_timeout` parameter

4. **Invalid JSON from AI**
   ```
   Warning: improvement_planner.json_parse_failed
   ```
   **Solution**: Service falls back to rule-based improvements

---

## File Locations

```
backend/
├── app/
│   ├── services/
│   │   ├── improvement_planner.py        # Main service
│   │   └── ai_mvp/
│   │       ├── website_analyzer.py       # Website scraping
│   │       ├── ai_council.py             # AI orchestration
│   │       └── semantic_router.py        # Cost optimization
│   └── api/
│       └── endpoints/
│           └── ai_mvp.py                 # REST endpoints
├── docs/
│   ├── IMPROVEMENT_PLANNER.md            # Full docs
│   └── PHASE3_QUICK_REFERENCE.md         # This file
└── tests/
    ├── test_website_analyzer.py
    └── test_improvement_planner.py
```

---

## Next Steps

1. **Set up API key**: Export `OPENROUTER_API_KEY`
2. **Run tests**: Verify everything works
3. **Try API**: Test with curl/Postman
4. **Integrate**: Add to lead workflow
5. **Monitor costs**: Check AI-GYM stats

---

## Support

- **Documentation**: `/docs/IMPROVEMENT_PLANNER.md`
- **Logs**: `backend/logs/improvement_planner.log`
- **API Docs**: http://localhost:8000/docs
- **OpenRouter Status**: https://openrouter.ai/status

---

## Changelog

**v1.0.0** (2025-01-15)
- Initial release
- AI-powered improvement plans
- 8 improvement categories
- 4 priority levels
- Rule-based + AI recommendations
- JSON and Markdown export
- REST API integration
