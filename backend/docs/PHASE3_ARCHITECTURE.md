# Phase 3: Website Analysis & Improvement Planning Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Phase 3: Website Intelligence                    │
│                                                                     │
│  ┌────────────────┐    ┌────────────────┐    ┌──────────────────┐ │
│  │   Craigslist   │───→│   Extract      │───→│   Website        │ │
│  │   Scraper      │    │   URL          │    │   Analyzer       │ │
│  │   (Phase 1)    │    │                │    │   (Task 1)       │ │
│  └────────────────┘    └────────────────┘    └──────────────────┘ │
│                                                        │            │
│                                                        ↓            │
│                                               ┌──────────────────┐ │
│                                               │  Improvement     │ │
│                                               │  Planner         │ │
│                                               │  (Task 2)        │ │
│                                               └──────────────────┘ │
│                                                        │            │
│                                                        ↓            │
│                                               ┌──────────────────┐ │
│                                               │  Response        │ │
│                                               │  Generator       │ │
│                                               │  (Phase 1)       │ │
│                                               └──────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Website Analyzer (Phase 3, Task 1)

```
WebsiteAnalyzer
├── Playwright Browser
│   ├── Fetch HTML/CSS/JS
│   ├── Execute JavaScript
│   ├── Capture screenshots
│   └── Extract metadata
├── Content Extraction
│   ├── Remove scripts/styles
│   ├── Extract main content
│   ├── Clean whitespace
│   └── Limit to 15K chars
├── Analysis Methods
│   ├── analyze_website() - Basic business analysis
│   ├── analyze_design_quality() - Design metrics
│   ├── analyze_seo() - SEO audit
│   ├── analyze_performance() - Speed metrics
│   ├── analyze_accessibility() - WCAG compliance
│   └── analyze_website_comprehensive() - All metrics
└── AI Integration
    ├── Semantic routing (cheap → expensive)
    ├── AI Council orchestration
    └── Cost tracking via AI-GYM
```

**Input**: Website URL
**Output**: Analysis with scores, issues, strengths, metrics

### 2. Improvement Planner (Phase 3, Task 2)

```
ImprovementPlanner
├── AI-Powered Generation
│   ├── Build context prompt
│   │   ├── Website analysis
│   │   ├── Industry context
│   │   ├── Focus areas
│   │   └── Best practices guide
│   ├── Call AI Council
│   │   ├── Route by lead value
│   │   ├── Temperature 0.7
│   │   └── Max 3000 tokens
│   └── Parse JSON response
│       ├── Extract improvements
│       ├── Validate categories
│       └── Create objects
├── Rule-Based Generation
│   ├── Meta description check
│   ├── Title length check
│   ├── Mobile responsiveness
│   ├── Performance issues
│   ├── CTA detection
│   └── Accessibility audit
├── Deduplication & Prioritization
│   ├── Remove duplicate titles
│   ├── Boost focus area priority
│   ├── Sort by priority
│   └── Re-assign IDs
└── Summary Generation
    ├── Count by priority
    ├── Count by category
    ├── Calculate time
    ├── Identify quick wins
    └── Estimate impact
```

**Input**: Website analysis result
**Output**: Prioritized improvement plan with 8-12 recommendations

### 3. AI Council (Core Infrastructure)

```
AICouncil
├── Semantic Router
│   ├── Task complexity detection
│   ├── Lead value consideration
│   └── Model selection
├── OpenRouter Integration
│   ├── Claude Sonnet 4 (premium)
│   ├── GPT-4o (premium)
│   ├── DeepSeek-V3 (cheap)
│   ├── Qwen 2.5 72B (cheap)
│   └── Gemini Flash 1.5 (ultra-cheap)
├── Request Handling
│   ├── Retry logic (3 attempts)
│   ├── Exponential backoff
│   └── Timeout handling
└── Tracking
    ├── AI-GYM cost tracking
    ├── Performance metrics
    └── Quality scores
```

## Data Flow

### Complete Workflow

```
1. SCRAPE CRAIGSLIST AD
   ├── Extract: title, description, contact, URL
   └── Store in database (Lead)

2. EXTRACT WEBSITE URL
   ├── Parse description for URLs
   ├── Validate URL format
   └── Clean/normalize URL

3. ANALYZE WEBSITE
   ├── Fetch with Playwright
   │   ├── Navigate to URL
   │   ├── Wait for load
   │   └── Extract HTML/metadata
   ├── Clean content
   │   ├── Remove scripts/styles
   │   ├── Extract main content
   │   └── Limit to 15K chars
   └── AI Analysis
       ├── Route by lead value
       ├── Generate analysis
       └── Return structured data

4. GENERATE IMPROVEMENT PLAN
   ├── AI Improvements
   │   ├── Build context prompt
   │   ├── Call AI Council
   │   └── Parse 6-10 improvements
   ├── Rule-Based Improvements
   │   ├── Run 6 deterministic checks
   │   └── Generate 2-6 improvements
   ├── Combine & Deduplicate
   │   ├── Remove duplicates
   │   └── Prioritize by focus areas
   └── Generate Summary
       ├── Count by priority/category
       ├── Calculate time/impact
       └── Identify quick wins

5. GENERATE OUTREACH EMAIL
   ├── Load user profile
   ├── Extract lead variables
   ├── Select template
   ├── Process variables
   ├── Enhance with AI
   └── Include top 3 improvements

6. SEND EMAIL
   ├── Via Postmark API
   ├── Track opens/clicks
   └── Store in conversation
```

## API Endpoints

### Phase 3 Endpoints (`/api/v1/ai-mvp`)

| Endpoint | Method | Purpose | Time | Cost |
|----------|--------|---------|------|------|
| `/analyze-website` | POST | Basic business analysis | 5-15s | $0.003-0.012 |
| `/analyze-design` | POST | Design quality metrics | 10-20s | $0.002-0.005 |
| `/analyze-seo` | POST | SEO audit | 5-10s | Free |
| `/analyze-performance` | POST | Performance metrics | 15-30s | Free |
| `/analyze-accessibility` | POST | Accessibility audit | 5-10s | Free |
| `/analyze-comprehensive` | POST | All metrics combined | 15-45s | $0.002-0.007 |
| `/generate-improvement-plan` | POST | AI-powered recommendations | 2-8s | $0.003-0.015 |
| `/generate-email` | POST | Personalized email | 2-5s | $0.003-0.008 |
| `/send-email` | POST | Send via Postmark | 1-2s | Postmark |
| `/stats` | GET | AI-GYM cost stats | <100ms | Free |
| `/performance` | GET | Model performance | <100ms | Free |

## Data Models

### Improvement Plan Structure

```typescript
interface ImprovementPlan {
  url: string;
  analyzed_at: string;
  improvements: Improvement[];
  summary: ImprovementPlanSummary;
  analysis_metadata: {
    industry?: string;
    focus_areas: string[];
    competitor_urls: string[];
    ai_model: string;
    ai_cost: number;
  };
}

interface Improvement {
  id: string;                    // "imp_001"
  category: Category;            // "conversion", "performance", etc.
  priority: Priority;            // "critical", "high", "medium", "low"
  title: string;                 // "Add Clear Call-to-Action"
  description: string;           // Detailed explanation
  current_state: string;         // What's happening now
  proposed_change: string;       // Specific recommendation
  impact: string;                // "40-60% increase in conversions"
  difficulty: Difficulty;        // "easy", "medium", "hard"
  time_estimate: string;         // "1 hour", "2-4 hours", "1 day"
  code_example?: string;         // HTML/CSS/JS snippet
  resources: string[];           // Helpful links
  dependencies: string[];        // Related improvement IDs
}

interface ImprovementPlanSummary {
  total_improvements: number;
  critical_priority: number;
  high_priority: number;
  medium_priority: number;
  low_priority: number;
  estimated_total_impact: string;
  estimated_total_time: string;
  quick_wins: number;            // High priority + easy difficulty
  categories: {
    [category: string]: number;  // Count per category
  };
}
```

### Website Analysis Structure

```typescript
interface WebsiteAnalysis {
  url: string;
  title: string;
  meta_description: string;
  status_code: number;
  content_length: number;
  ai_analysis: string;           // Markdown formatted analysis
  ai_model: string;              // Model used
  ai_cost: number;               // Cost in dollars
  ai_request_id: number;         // AI-GYM request ID
  lead_id?: number;
  lead_value?: number;
}

interface ComprehensiveAnalysis {
  url: string;
  overall_score: number;         // 0-100
  design: DesignAnalysis;        // 25% weight
  seo: SEOAnalysis;              // 30% weight
  performance: PerformanceAnalysis; // 25% weight
  accessibility: AccessibilityAnalysis; // 20% weight
  title: string;
  meta_description: string;
}
```

## Cost Optimization Strategy

### Semantic Routing

```
Lead Value → Model Selection → Cost/Quality Balance

$0-25K
  ├→ Qwen 2.5 72B ($0.0003/1K tokens)
  └→ Quality: Good, Speed: Fast

$25K-100K
  ├→ DeepSeek-V3 ($0.008/1K tokens)
  └→ Quality: Very Good, Speed: Fast

$100K+
  ├→ Claude Sonnet 4 ($0.015/1K tokens)
  └→ Quality: Excellent, Speed: Moderate
```

### Cost Breakdown

```
Typical Lead Analysis (lead_value=$50K):

1. Website Analysis
   ├→ Routed to: DeepSeek-V3
   ├→ Tokens: ~1,500 (analysis)
   └→ Cost: $0.012

2. Improvement Plan
   ├→ Routed to: DeepSeek-V3
   ├→ Tokens: ~2,000 (recommendations)
   └→ Cost: $0.016

3. Email Generation
   ├→ Routed to: DeepSeek-V3
   ├→ Tokens: ~500 (email)
   └→ Cost: $0.004

TOTAL: $0.032 per lead
```

## Performance Characteristics

| Operation | Latency | Throughput | Concurrency |
|-----------|---------|------------|-------------|
| Website Fetch | 5-15s | 20/min | 5 concurrent |
| AI Analysis | 2-8s | 30/min | 10 concurrent |
| Improvement Plan | 2-8s | 30/min | 10 concurrent |
| Rule-Based Check | <100ms | 1000/min | 100 concurrent |
| JSON Export | <5ms | 10000/min | Unlimited |
| Markdown Export | <10ms | 5000/min | Unlimited |

## Error Handling Strategy

```
AI-First with Fallbacks:

1. Try AI Generation
   ├→ Success → Continue
   └→ Failure → Log error, continue

2. Always Run Rule-Based
   ├→ 6 deterministic checks
   └→ 2-6 guaranteed improvements

3. Combine Results
   ├→ Merge AI + Rule-Based
   ├→ Deduplicate
   └→ Always return valid plan

Result: Never fails completely
```

## Integration Points

### Existing System

```
Phase 1: Craigslist Scraper
  └→ Extracts website URLs

Phase 2: Lead Qualification
  └→ Can use website analysis for scoring

Phase 3: Website Intelligence
  ├→ Analyzes scraped websites
  └→ Generates improvement plans

Response Generator
  └→ Uses improvement plan in outreach
```

### Future Enhancements

```
Phase 4: Automated Implementation (Future)
  ├→ Generate code templates
  ├→ Create GitHub PRs
  └→ A/B test variations

Phase 5: Result Tracking (Future)
  ├→ Monitor actual impact
  ├→ Compare to estimates
  └→ Improve recommendations
```

## Deployment Architecture

```
Production Setup:

┌─────────────────────────────────────────────┐
│          Load Balancer (nginx)              │
└─────────────────┬───────────────────────────┘
                  │
    ┌─────────────┴─────────────┐
    │                           │
┌───▼────┐                 ┌────▼───┐
│ FastAPI│                 │ FastAPI│
│ Server │                 │ Server │
│   #1   │                 │   #2   │
└───┬────┘                 └────┬───┘
    │                           │
    └─────────────┬─────────────┘
                  │
    ┌─────────────▼─────────────┐
    │      PostgreSQL DB        │
    │   (Leads, Analysis)       │
    └───────────────────────────┘

    ┌───────────────────────────┐
    │      OpenRouter API       │
    │   (AI Models)             │
    └───────────────────────────┘

    ┌───────────────────────────┐
    │      Playwright           │
    │   (Browser Pool)          │
    └───────────────────────────┘
```

## Security Considerations

1. **API Keys**: Store in environment variables, never commit
2. **Rate Limiting**: Prevent abuse of AI endpoints
3. **Input Validation**: Sanitize URLs and user input
4. **Content Filtering**: Avoid analyzing malicious sites
5. **Cost Limits**: Cap AI spending per user/day
6. **CORS**: Restrict API access to approved domains

## Monitoring & Observability

### Key Metrics

```
Business Metrics:
├── Improvement plans generated/day
├── Average cost per plan
├── Conversion rate (leads with plans → contacted)
└── Response rate (contacted → replied)

Technical Metrics:
├── API latency (p50, p95, p99)
├── Error rate (4xx, 5xx)
├── AI model usage breakdown
└── Browser pool utilization

Cost Metrics:
├── Daily AI spend
├── Cost per lead
├── Model efficiency (quality/cost ratio)
└── Unused credits
```

### AI-GYM Tracking

```sql
-- View cost by model
SELECT
  model_name,
  COUNT(*) as requests,
  AVG(cost) as avg_cost,
  SUM(cost) as total_cost,
  AVG(quality_score) as avg_quality
FROM ai_gym_requests
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY model_name
ORDER BY total_cost DESC;

-- View performance by task type
SELECT
  task_type,
  COUNT(*) as requests,
  AVG(duration_seconds) as avg_duration,
  AVG(cost) as avg_cost
FROM ai_gym_requests
GROUP BY task_type;
```

## Best Practices

### 1. Lead Value Optimization

```python
# Set accurate lead values for optimal routing
high_value_lead = 100000  # → Claude Sonnet 4
mid_value_lead = 50000    # → DeepSeek-V3
low_value_lead = 10000    # → Qwen 2.5 72B
```

### 2. Focus Areas

```python
# Guide prioritization with focus areas
focus_areas = ["conversion", "performance"]
# Boosts priority of improvements in these categories
```

### 3. Industry Context

```python
# Provide industry for better recommendations
industry = "Web Development Services"
# AI generates industry-specific suggestions
```

### 4. Batch Processing

```python
# Process multiple websites concurrently
urls = ["https://site1.com", "https://site2.com"]
results = await analyzer.analyze_multiple_websites(urls, max_concurrent=3)
```

### 5. Error Recovery

```python
# Always get some improvements, even if AI fails
try:
    plan = await planner.generate_plan(analysis)
except Exception as e:
    logger.error(f"AI failed: {e}")
    # Still returns rule-based improvements
```

## File Structure

```
backend/
├── app/
│   ├── services/
│   │   ├── improvement_planner.py         # Main service
│   │   └── ai_mvp/
│   │       ├── website_analyzer.py        # Website scraping
│   │       ├── ai_council.py              # AI orchestration
│   │       ├── semantic_router.py         # Cost optimization
│   │       └── ai_gym_tracker.py          # Cost tracking
│   ├── api/
│   │   └── endpoints/
│   │       └── ai_mvp.py                  # REST endpoints
│   └── models/
│       └── ai_gym.py                      # Database models
├── docs/
│   ├── IMPROVEMENT_PLANNER.md             # Service docs
│   ├── PHASE3_QUICK_REFERENCE.md          # Quick guide
│   └── PHASE3_ARCHITECTURE.md             # This file
├── tests/
│   ├── test_website_analyzer.py
│   └── test_improvement_planner.py
└── PHASE3_TASK2_COMPLETE.md               # Completion report
```

## Summary

Phase 3 adds powerful website intelligence to the lead generation system:

✅ **Website Analysis**: Comprehensive metrics (design, SEO, performance, accessibility)
✅ **Improvement Plans**: AI-powered + rule-based recommendations
✅ **Cost Optimization**: Semantic routing based on lead value
✅ **Smart Prioritization**: Focus areas, quick wins, time estimates
✅ **Multiple Exports**: JSON, Markdown for various use cases
✅ **Error Resilience**: Always returns useful results
✅ **Production Ready**: Complete documentation, tests, monitoring

**Total Investment**: ~2,600 lines of code
**Time to Value**: < 10 seconds per lead
**Cost per Lead**: $0.006-0.034
**Quality**: Production-grade with comprehensive error handling

---

**Last Updated**: January 15, 2025
**Version**: 1.0.0
**Status**: ✅ Production Ready
