# Website Improvement Plan Generator

**Phase 3, Task 2** - AI-powered website improvement plan generation service

## Overview

The Improvement Planner service generates comprehensive, actionable improvement plans for analyzed websites. It combines AI-powered creative recommendations with rule-based analysis to produce prioritized, specific improvements with code examples and time estimates.

## Features

### Core Capabilities

1. **AI-Powered Recommendations**
   - Uses OpenRouter API via AI Council
   - Context-aware suggestions based on industry/niche
   - Creative, specific improvements with concrete examples
   - Competitor-inspired enhancements

2. **Rule-Based Analysis**
   - Deterministic improvements from technical analysis
   - SEO, accessibility, performance checks
   - Mobile responsiveness validation
   - Call-to-action detection

3. **Intelligent Prioritization**
   - 4 priority levels: Critical, High, Medium, Low
   - Focus area boosting (conversion, performance, etc.)
   - Quick win identification (high impact + easy implementation)
   - Category-based organization

4. **Detailed Implementation Guidance**
   - Specific current state analysis
   - Concrete proposed changes
   - Code examples (HTML/CSS/JavaScript)
   - Time estimates (minutes, hours, days)
   - Implementation difficulty (easy/medium/hard)
   - Resource links for further reading

## Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  ImprovementPlanner                         │
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │  1. AI-Powered Improvements                        │    │
│  │     - Build context prompt                         │    │
│  │     - Call AI Council (OpenRouter)                 │    │
│  │     - Parse JSON response                          │    │
│  │     - Generate 6-10 improvements                   │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↓                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │  2. Rule-Based Improvements                        │    │
│  │     - Missing meta description                     │    │
│  │     - Title length issues                          │    │
│  │     - Mobile responsiveness                        │    │
│  │     - Performance issues                           │    │
│  │     - Missing CTAs                                 │    │
│  │     - Accessibility problems                       │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↓                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │  3. Deduplication & Prioritization                 │    │
│  │     - Remove duplicates by title                   │    │
│  │     - Boost priority for focus areas               │    │
│  │     - Sort by priority                             │    │
│  │     - Re-assign IDs                                │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↓                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │  4. Summary Generation                             │    │
│  │     - Count by priority/category                   │    │
│  │     - Calculate total time                         │    │
│  │     - Identify quick wins                          │    │
│  │     - Estimate overall impact                      │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### Python API

```python
from app.services.improvement_planner import ImprovementPlanner
from app.services.ai_mvp.ai_council import AICouncil, AICouncilConfig

# Initialize AI Council
config = AICouncilConfig(
    openrouter_api_key="sk-or-v1-..."
)
ai_council = AICouncil(config=config)

# Initialize planner
planner = ImprovementPlanner(ai_council=ai_council)

# Generate plan
plan = await planner.generate_plan(
    analysis_result={
        "url": "https://example.com",
        "title": "Example Corp - Web Services",
        "meta_description": "We build websites",
        "ai_analysis": "...analysis text...",
        "ai_model": "anthropic/claude-sonnet-4",
        "ai_cost": 0.012
    },
    industry="Web Development Services",
    focus_areas=["conversion", "performance"],
    lead_value=50000.0
)

# Access results
print(f"Total improvements: {plan.summary.total_improvements}")
print(f"High priority: {plan.summary.high_priority}")
print(f"Quick wins: {plan.summary.quick_wins}")
print(f"Total time: {plan.summary.estimated_total_time}")

# Export to formats
json_output = planner.export_to_json(plan)
markdown_output = planner.export_to_markdown(plan)

# Close AI Council
await ai_council.close()
```

### REST API

**Endpoint**: `POST /api/v1/ai-mvp/generate-improvement-plan`

**Request Body**:
```json
{
  "url": "https://example.com",
  "analysis_result": {
    "url": "https://example.com",
    "title": "Example Corp - Web Services",
    "meta_description": "We build websites",
    "status_code": 200,
    "content_length": 5432,
    "ai_analysis": "BUSINESS ANALYSIS:\n- Company: Example Corp\n- Industry: Web Development\n...",
    "ai_model": "anthropic/claude-sonnet-4",
    "ai_cost": 0.012,
    "ai_request_id": 1,
    "lead_id": null,
    "lead_value": 50000.0
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
      "description": "Website lacks a prominent CTA. CTAs are essential for guiding users to conversion.",
      "current_state": "Missing or unclear primary call-to-action",
      "proposed_change": "Add prominent, action-oriented CTA button above the fold",
      "impact": "40-60% increase in conversion rate",
      "difficulty": "easy",
      "time_estimate": "1 hour",
      "code_example": "<button class=\"cta-primary\">Get Started Free →</button>\n\n.cta-primary {\n  background: #FF6B35;\n  color: white;\n  padding: 16px 32px;\n  font-size: 18px;\n}",
      "resources": [
        "https://www.nngroup.com/articles/call-to-action-buttons/"
      ],
      "dependencies": []
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
      "seo": 3,
      "accessibility": 2,
      "design": 2
    }
  },
  "analysis_metadata": {
    "industry": "Web Development Services",
    "focus_areas": ["conversion", "performance"],
    "competitor_urls": [],
    "ai_model": "anthropic/claude-sonnet-4",
    "ai_cost": 0.012
  }
}
```

## Improvement Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **design** | Visual design, layout, typography | Color contrast, button styling, spacing |
| **content** | Copy, messaging, headlines | CTA text, value propositions, headlines |
| **technical** | Code, infrastructure, architecture | Mobile responsive, HTTPS, caching |
| **ux** | User experience, navigation, flows | Menu structure, forms, page flow |
| **seo** | Search engine optimization | Meta tags, structured data, sitemap |
| **accessibility** | WCAG compliance, screen readers | Alt text, ARIA labels, keyboard nav |
| **performance** | Speed, loading time, Core Web Vitals | Image optimization, lazy loading, minification |
| **conversion** | Conversion rate optimization | CTAs, social proof, trust signals |

## Priority Levels

| Priority | Definition | Action |
|----------|------------|--------|
| **Critical** | Major issues blocking conversions/SEO | Fix immediately |
| **High** | Significant impact on performance/UX | Fix within 1 week |
| **Medium** | Moderate improvements | Schedule for next sprint |
| **Low** | Nice-to-have enhancements | Backlog for future |

## Implementation Difficulty

| Difficulty | Time Range | Skill Level |
|------------|------------|-------------|
| **Easy** | 15 min - 2 hours | Basic HTML/CSS |
| **Medium** | 2-8 hours | Intermediate dev |
| **Hard** | 1-3 days | Senior dev/architect |

## AI Prompting Strategy

The service uses a carefully crafted prompt that instructs the AI to:

1. **Be Specific**: Avoid vague recommendations like "improve design"
2. **Include Examples**: Provide actual code with realistic values
3. **Consider Standards**: Reference WCAG 2.1, Core Web Vitals, etc.
4. **Think Impact**: Estimate percentage improvements
5. **Be Actionable**: Every recommendation should be implementable
6. **Prioritize Quick Wins**: High impact + low effort = priority

Example prompt structure:
```
Generate 8-12 specific, actionable improvements for:

WEBSITE: https://example.com
INDUSTRY: Web Development Services
FOCUS AREAS: conversion, performance

ANALYSIS RESULTS:
[website analysis text]

For each improvement provide:
1. Category (design/content/technical/ux/seo/etc)
2. Priority (critical/high/medium/low)
3. Title (action-oriented)
4. Description (2-3 sentences explaining the issue)
5. Current State (what's happening now)
6. Proposed Change (specific recommendation)
7. Impact (estimated % improvement)
8. Difficulty (easy/medium/hard)
9. Time Estimate (realistic time)
10. Code Example (concrete implementation)
11. Resources (helpful links)

GUIDELINES:
- Be specific and actionable
- Include actual code examples
- Consider accessibility and performance
- Prioritize high-impact, low-effort improvements
- Reference modern web standards
```

## Rule-Based Improvements

The service includes several deterministic checks:

### 1. Meta Description
**Trigger**: Missing or < 50 characters
**Priority**: High
**Impact**: 10-30% SERP CTR improvement

### 2. Title Length
**Trigger**: < 30 or > 60 characters
**Priority**: Medium
**Impact**: 5-15% SERP visibility improvement

### 3. Mobile Responsiveness
**Trigger**: AI analysis mentions mobile issues
**Priority**: High
**Impact**: 30-50% mobile engagement improvement

### 4. Performance
**Trigger**: AI analysis mentions slow loading
**Priority**: High
**Impact**: 20-40% load time improvement, 10-15% conversion increase

### 5. Call-to-Action
**Trigger**: AI analysis mentions missing/unclear CTA
**Priority**: Critical
**Impact**: 40-60% conversion rate increase

### 6. Accessibility
**Trigger**: AI analysis mentions WCAG/contrast issues
**Priority**: Medium
**Impact**: 15-25% satisfaction improvement, legal compliance

## Cost Estimation

| Lead Value | Model Selected | Typical Cost | Quality |
|------------|----------------|--------------|---------|
| $0-25K | Qwen 2.5 72B | ~$0.003 | Good |
| $25K-100K | DeepSeek-V3 | ~$0.008 | Very Good |
| $100K+ | Claude Sonnet 4 | ~$0.015 | Excellent |

**Total Cost**: Analysis ($0.003-0.012) + Improvement Plan ($0.003-0.015) = **$0.006-0.027 per website**

## Output Formats

### JSON Export
```python
json_output = planner.export_to_json(plan)
# Returns: Pydantic JSON with full structure
```

### Markdown Export
```python
markdown_output = planner.export_to_markdown(plan)
# Returns: Formatted markdown report ready for display
```

**Markdown Structure**:
- Header with URL and timestamp
- Summary statistics table
- Category breakdown
- Improvements grouped by priority
- Code examples in fenced blocks
- Resource links

## Testing

Run the test script to verify functionality:

```bash
cd /Users/greenmachine2.0/Craigslist/backend

# With OpenRouter API key (full AI testing)
export OPENROUTER_API_KEY="sk-or-v1-..."
python test_improvement_planner.py

# Without API key (rule-based only)
python test_improvement_planner.py
```

**Test Output**:
- Generates sample improvement plan
- Displays summary statistics
- Shows top 5 improvements
- Exports to `improvement_plan.json` and `improvement_plan.md`

## Integration Example

Complete workflow from scraping to improvement plan:

```python
from app.services.ai_mvp import WebsiteAnalyzer, AICouncil, AICouncilConfig
from app.services.improvement_planner import ImprovementPlanner

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

# Step 3: Export and use
markdown_report = planner.export_to_markdown(plan)
print(markdown_report)

# Step 4: Implement top 3 improvements
for imp in plan.improvements[:3]:
    if imp.priority in ["critical", "high"]:
        print(f"Implement: {imp.title}")
        print(f"Code: {imp.code_example}")
```

## Error Handling

The service handles various error conditions:

1. **AI API Errors**: Falls back to rule-based improvements only
2. **Invalid JSON**: Logs warning, continues with valid improvements
3. **Missing Analysis Data**: Uses available data, skips AI enhancements
4. **Parsing Errors**: Individual improvements fail gracefully

Example error handling:

```python
try:
    plan = await planner.generate_plan(analysis_result)
except Exception as e:
    logger.error(f"Plan generation failed: {e}")
    # System will still return rule-based improvements
```

## Performance

| Operation | Time | Cost |
|-----------|------|------|
| AI Improvement Generation | 2-8 seconds | $0.003-0.015 |
| Rule-Based Generation | < 100ms | Free |
| JSON Parsing | < 50ms | Free |
| Deduplication | < 10ms | Free |
| Export to JSON | < 5ms | Free |
| Export to Markdown | < 10ms | Free |

**Total**: ~2-8 seconds for full plan generation

## Best Practices

1. **Always Include Analysis**: Pass complete analysis results for best AI recommendations
2. **Specify Industry**: Industry context significantly improves relevance
3. **Use Focus Areas**: Guide prioritization to business goals
4. **Set Lead Value**: Higher values get better AI models
5. **Review Quick Wins First**: Start with high-impact, easy implementations
6. **Track Results**: Monitor actual impact vs. estimates for tuning

## Future Enhancements

Potential improvements for v2:

1. **A/B Test Suggestions**: Generate testable variations
2. **Competitor Analysis**: Auto-analyze competitor URLs
3. **Historical Tracking**: Track which improvements worked
4. **Implementation Templates**: Ready-to-deploy code packages
5. **Video Tutorials**: Link to implementation guides
6. **Cost Calculator**: Estimate development cost in dollars
7. **Automated Implementation**: Generate PRs for code changes

## Related Documentation

- [Website Analyzer](./WEBSITE_ANALYZER.md) - Phase 3 Task 1
- [AI Council](./AI_COUNCIL.md) - Multi-model orchestration
- [Semantic Router](./SEMANTIC_ROUTER.md) - Cost-optimized routing
- [AI-GYM Tracker](./AI_GYM.md) - Performance tracking

## Support

For issues or questions:
1. Check logs: `backend/logs/improvement_planner.log`
2. Run test script: `python test_improvement_planner.py`
3. Review error messages in API responses
4. Check OpenRouter API status: https://openrouter.ai/status

## File Locations

- **Service**: `/Users/greenmachine2.0/Craigslist/backend/app/services/improvement_planner.py`
- **API Endpoint**: `/Users/greenmachine2.0/Craigslist/backend/app/api/endpoints/ai_mvp.py`
- **Test Script**: `/Users/greenmachine2.0/Craigslist/backend/test_improvement_planner.py`
- **Documentation**: `/Users/greenmachine2.0/Craigslist/backend/docs/IMPROVEMENT_PLANNER.md`
