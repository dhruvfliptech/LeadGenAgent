# Craigslist Lead Generation System - Formal Requirements Document

**Document Version:** 1.0
**Last Updated:** 2025-11-05
**Status:** Complete Implementation Specification

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Implementation Status Matrix](#implementation-status-matrix)
4. [Architectural Decisions](#architectural-decisions)
5. [Feature Specifications](#feature-specifications)
6. [AI-GYM Multi-Model Optimization](#ai-gym-multi-model-optimization)
7. [Frontend UX Improvements](#frontend-ux-improvements)
8. [Development Roadmap](#development-roadmap)
9. [Technical Debt & Known Issues](#technical-debt--known-issues)

---

## Executive Summary

### Current Reality

The Craigslist Lead Generation System was designed as a comprehensive AI-powered lead generation platform with multi-source scraping, website analysis, demo site building, video creation, and AI-driven outreach capabilities.

**Critical Finding:** While the frontend UI presents a complete application interface (~90% UI coverage), the backend implementation is only ~20% complete. This creates a significant disconnect between user expectations and actual functionality.

### What Exists (✅ Implemented)
- **Core Infrastructure:** FastAPI backend, PostgreSQL database, Redis caching, React frontend
- **Craigslist Scraping:** Basic scraping with Playwright, location/category management
- **Lead Storage:** Database models and basic CRUD operations
- **Frontend UI:** Comprehensive React components for all planned features
- **Database Schema:** All 50+ tables created for full feature set

### What's Missing (❌ Not Implemented)
- **Multi-Source Scraping:** Google Maps, LinkedIn, Job Boards (80% of scraping sources)
- **Website Analysis Agent:** AI-powered website evaluation
- **Demo Site Builder:** AI-generated code from website analysis
- **Video Creation System:** Loom-style video generation with voiceovers
- **Email Outreach:** Automated email sending and conversation management
- **AI-GYM:** Multi-model performance tracking and optimization
- **n8n Integration:** Workflow orchestration layer
- **Approval Workflows:** Human-in-the-loop approval system

### Document Purpose

This document serves as the definitive source of truth for:
1. **What has been built** - Detailed status of each component
2. **Why decisions were made** - Architectural rationale and tradeoffs
3. **What remains to be built** - Gap analysis with effort estimates
4. **How to move forward** - Prioritized roadmap to completion

---

## System Overview

### Original Vision

A comprehensive AI-powered lead generation platform that:
1. **Scrapes leads** from multiple sources (Craigslist, Google Maps, LinkedIn, Job Boards)
2. **Analyzes websites** using AI to identify improvement opportunities
3. **Generates demo sites** showing proposed improvements
4. **Creates Loom-style videos** demonstrating the improvements
5. **Sends automated emails** with personalized outreach
6. **Manages conversations** with AI-powered responses
7. **Optimizes AI performance** using multi-model comparison (AI-GYM)
8. **Orchestrates workflows** through n8n integration

### Target Users

- **Lead Generation Agencies:** Automating cold outreach at scale
- **Web Design Firms:** Generating qualified leads with demo sites
- **Marketing Teams:** Data-driven outreach with AI personalization
- **Solo Entrepreneurs:** Complete automation of lead generation funnel

### Success Metrics

- **Conversion Rate:** % of scraped leads that respond
- **Demo Quality Score:** AI evaluation of generated demo sites
- **Response Time:** Speed of AI-generated responses
- **Cost Efficiency:** Cost per qualified lead
- **Model Performance:** AI-GYM optimization improvements

---

## Implementation Status Matrix

### Overall Progress

| Component | UI Status | Backend Status | Overall % | Priority |
|-----------|-----------|----------------|-----------|----------|
| **Core Infrastructure** | ✅ 100% | ✅ 100% | ✅ 100% | P0 |
| **Craigslist Scraping** | ✅ 100% | ⚠️ 60% | ⚠️ 70% | P0 |
| **Lead Management** | ✅ 100% | ✅ 80% | ✅ 85% | P0 |
| **Google Maps Scraping** | ✅ 100% | ❌ 0% | ⚠️ 50% | P1 |
| **LinkedIn Scraping** | ✅ 100% | ❌ 0% | ⚠️ 50% | P1 |
| **Job Board Scraping** | ✅ 100% | ❌ 0% | ⚠️ 50% | P1 |
| **Website Analysis** | ✅ 100% | ❌ 0% | ⚠️ 50% | P1 |
| **Demo Site Builder** | ✅ 100% | ❌ 0% | ⚠️ 50% | P1 |
| **Video Creation** | ✅ 100% | ❌ 0% | ⚠️ 50% | P2 |
| **Email Outreach** | ✅ 90% | ❌ 0% | ⚠️ 45% | P1 |
| **Conversation AI** | ✅ 100% | ❌ 0% | ⚠️ 50% | P2 |
| **AI-GYM** | ❌ 0% | ❌ 0% | ❌ 0% | P1 |
| **n8n Integration** | ✅ 100% | ❌ 0% | ⚠️ 50% | P2 |
| **Approval Workflows** | ✅ 100% | ❌ 0% | ⚠️ 50% | P2 |

**Legend:**
- ✅ **Complete:** Feature is fully functional
- ⚠️ **Partial:** Feature is partially implemented
- ❌ **Missing:** Feature not yet implemented
- **P0:** Critical path (MVP)
- **P1:** High priority (Phase 2)
- **P2:** Medium priority (Phase 3)

### Detailed Component Status

#### 1. Core Infrastructure (✅ 100%)
**Status:** COMPLETE
**Components:**
- ✅ FastAPI backend with async/await
- ✅ PostgreSQL database with 50+ tables
- ✅ Redis for caching and job queues
- ✅ React + TypeScript frontend
- ✅ WebSocket support for real-time updates
- ✅ Docker-ready configuration
- ✅ Environment configuration system

**Gaps:** None - fully functional

---

#### 2. Craigslist Scraping (⚠️ 70%)
**Status:** PARTIALLY COMPLETE
**What Works:**
- ✅ Location hierarchy (US, Canada, World)
- ✅ Category selection and filtering
- ✅ Basic Playwright-based scraping
- ✅ Job queue system
- ✅ Real-time WebSocket progress updates
- ✅ Lead storage and deduplication

**What's Missing:**
- ❌ CAPTCHA solving integration (2Captcha configured but not tested)
- ❌ Email extraction from listing pages
- ❌ Contact information parsing (phone numbers, etc.)
- ❌ Advanced filtering (price range, date posted, etc.)
- ❌ Retry logic for failed scrapes
- ❌ Scraping rate limiting/throttling

**Effort to Complete:** 40 hours

---

#### 3. Lead Management (✅ 85%)
**Status:** MOSTLY COMPLETE
**What Works:**
- ✅ Lead CRUD operations
- ✅ Lead listing with pagination
- ✅ Basic filtering and search
- ✅ Lead status tracking
- ✅ Custom fields storage

**What's Missing:**
- ❌ Advanced search (full-text, fuzzy matching)
- ❌ Lead scoring/ranking
- ❌ Bulk operations (delete, update, export)
- ❌ Lead enrichment (append additional data)
- ❌ Lead deduplication across sources

**Effort to Complete:** 20 hours

---

#### 4. Google Maps Scraping (⚠️ 50% - UI Only)
**Status:** FRONTEND ONLY
**What Works:**
- ✅ UI components for Google Maps source configuration
- ✅ Location/area selection interface
- ✅ Business category filters

**What's Missing:**
- ❌ Google Maps scraping endpoint (`/api/v1/google-maps/*`)
- ❌ Playwright automation for Google Maps
- ❌ Business information extraction
- ❌ Review scraping
- ❌ Contact information extraction
- ❌ API integration (Google Places API alternative)

**Technical Approach:**
- Use Playwright to scrape search results
- Extract: name, address, phone, website, rating, reviews
- Store in `leads` table with `source='google_maps'`
- Handle Google's anti-bot measures (rate limiting, CAPTCHA)

**Effort to Complete:** 60 hours

---

#### 5. LinkedIn Scraping (⚠️ 50% - UI Only)
**Status:** FRONTEND ONLY
**What Works:**
- ✅ UI for LinkedIn source configuration
- ✅ Search query builder
- ✅ Industry/title filters

**What's Missing:**
- ❌ LinkedIn scraping endpoint (`/api/v1/linkedin/*`)
- ❌ LinkedIn authentication handling
- ❌ Profile scraping
- ❌ Company page scraping
- ❌ Connection/messaging integration
- ❌ Compliance with LinkedIn ToS

**Technical Considerations:**
- **HIGH RISK:** LinkedIn actively blocks scrapers
- **Alternative:** Use LinkedIn Sales Navigator API (paid)
- **Legal:** Must comply with LinkedIn ToS and CFAA
- **Recommendation:** Deprioritize or use official API only

**Effort to Complete:** 80 hours (high complexity/risk)

---

#### 6. Job Board Scraping (⚠️ 50% - UI Only)
**Status:** FRONTEND ONLY
**What Works:**
- ✅ UI for job board source configuration
- ✅ Multi-board selection (Indeed, Monster, ZipRecruiter)

**What's Missing:**
- ❌ Job board scraping endpoints (`/api/v1/job-boards/*`)
- ❌ Indeed scraping
- ❌ Monster scraping
- ❌ ZipRecruiter scraping
- ❌ Generic job board scraper
- ❌ Job posting deduplication

**Technical Approach:**
- Build modular scraper per job board
- Extract: job title, company, location, description, apply URL
- Store in `leads` table with `source='indeed'`, etc.

**Effort to Complete:** 100 hours (need scraper per board)

---

#### 7. Website Analysis Agent (⚠️ 50% - UI Only)
**Status:** FRONTEND ONLY
**What Works:**
- ✅ UI showing analysis results
- ✅ Score display (design, SEO, performance, accessibility)
- ✅ Improvement recommendations display

**What's Missing:**
- ❌ Website analysis endpoint (`/api/v1/website-analysis/*`)
- ❌ HTML fetching and parsing
- ❌ AI-powered analysis (design, SEO, performance, accessibility)
- ❌ Screenshot capture
- ❌ Lighthouse integration
- ❌ Improvement plan generation

**Technical Approach:**
```python
# Pseudocode
async def analyze_website(url: str):
    # 1. Fetch HTML + screenshot
    html = await fetch_html(url)
    screenshot = await capture_screenshot(url)

    # 2. Run Lighthouse audit
    lighthouse_scores = await run_lighthouse(url)

    # 3. AI analysis
    analysis = await ai_council_query({
        "html": html,
        "screenshot": screenshot,
        "lighthouse": lighthouse_scores,
        "prompt": "Analyze this website and suggest improvements..."
    })

    # 4. Generate improvement plan
    improvements = parse_ai_analysis(analysis)

    return ComprehensiveAnalysis(
        overall_score=calculate_score(lighthouse_scores, analysis),
        design=analysis.design,
        seo=analysis.seo,
        performance=lighthouse_scores,
        accessibility=lighthouse_scores.accessibility,
        improvements=improvements
    )
```

**Effort to Complete:** 80 hours

---

#### 8. Demo Site Builder (⚠️ 50% - UI Only)
**Status:** FRONTEND ONLY
**What Works:**
- ✅ UI wizard for demo site creation
- ✅ Framework selection (HTML, React, Next.js)
- ✅ Preview display
- ✅ File tree viewer
- ✅ Deployment configuration

**What's Missing:**
- ❌ Demo site generation endpoint (`/api/v1/demo-sites/*`)
- ❌ AI-powered code generation
- ❌ Multi-framework support (HTML/React/Next.js)
- ❌ Code validation
- ❌ Deployment integration (Vercel/Netlify)
- ❌ Preview server

**Technical Approach:**
```python
# Pseudocode
async def generate_demo_site(
    lead_id: int,
    original_url: str,
    improvement_plan: ImprovementPlan,
    framework: Framework
):
    # 1. Fetch original website
    html = await fetch_html(original_url)

    # 2. AI generates improved code
    prompt = f"""
    Original HTML: {html}
    Improvement Plan: {improvement_plan}
    Target Framework: {framework}

    Generate a complete {framework} website implementing these improvements...
    """

    generated_code = await ai_council_query(prompt, model="claude-4.5-sonnet")

    # 3. Validate generated code
    validation = validate_code(generated_code, framework)

    # 4. Store in database
    demo_site = DemoSite(
        lead_id=lead_id,
        framework=framework,
        files=generated_code.files,
        status="completed"
    )

    # 5. Deploy to preview
    preview_url = await deploy_to_vercel(generated_code)
    demo_site.preview_url = preview_url

    return demo_site
```

**AI-GYM Integration:**
- Test multiple models (Claude, GPT-4, DeepSeek) for code generation
- Track which model produces best code quality
- Optimize for: valid syntax, design quality, performance

**Effort to Complete:** 120 hours

---

#### 9. Video Creation System (⚠️ 50% - UI Only)
**Status:** FRONTEND ONLY
**What Works:**
- ✅ UI wizard for video creation
- ✅ Demo site selection
- ✅ Script generation display
- ✅ Voiceover configuration
- ✅ Video preview player

**What's Missing:**
- ❌ Video creation endpoints (`/api/v1/videos/*`)
- ❌ AI script generation
- ❌ Text-to-speech (ElevenLabs integration)
- ❌ Screen recording (Puppeteer-based)
- ❌ Video composition (FFmpeg)
- ❌ Video hosting/CDN

**Technical Approach:**
```python
# Pseudocode - Complete Video Generation Pipeline
async def create_demo_video(demo_site_id: int):
    # Phase 1: Generate Script
    script = await generate_script(demo_site_id)
    # AI analyzes demo site and creates presentation script

    # Phase 2: Generate Voiceover
    voiceover = await generate_voiceover(script.text)
    # ElevenLabs TTS creates audio file

    # Phase 3: Record Screen
    recording = await record_screen(demo_site_id, script.timings)
    # Puppeteer navigates demo site, captures video

    # Phase 4: Compose Video
    video = await compose_video(recording, voiceover)
    # FFmpeg combines screen recording + voiceover

    # Phase 5: Upload & Store
    video_url = await upload_to_cdn(video)

    return ComposedVideo(
        demo_site_id=demo_site_id,
        video_url=video_url,
        duration_seconds=video.duration,
        status="completed"
    )
```

**Dependencies:**
- ElevenLabs API for TTS (paid service)
- Puppeteer for screen recording
- FFmpeg for video composition
- S3/CloudFlare for video hosting

**Effort to Complete:** 150 hours

---

#### 10. Email Outreach (⚠️ 45% - UI Only)
**Status:** FRONTEND ONLY
**What Works:**
- ✅ Email template UI
- ✅ Recipient selection
- ⚠️ Frontend campaign tracking (no backend)

**What's Missing:**
- ❌ Email sending endpoints (`/api/v1/email/*`)
- ❌ SMTP integration
- ❌ Email template engine
- ❌ Personalization tokens
- ❌ Campaign management
- ❌ Tracking (opens, clicks, replies)
- ❌ Deliverability optimization
- ❌ Bounce/spam handling

**Technical Approach:**
- Use SendGrid or Amazon SES for sending
- Store templates in database
- Track opens via pixel tracking
- Track clicks via redirect URLs
- Parse replies via webhook/IMAP

**Effort to Complete:** 60 hours

---

#### 11. Conversation AI (⚠️ 50% - UI Only)
**Status:** FRONTEND ONLY
**What Works:**
- ✅ Conversation thread UI
- ✅ Message display
- ✅ AI suggestion display

**What's Missing:**
- ❌ Conversation endpoints (`/api/v1/conversations/*`)
- ❌ Email reply parsing
- ❌ AI response generation
- ❌ Conversation context management
- ❌ Sentiment analysis
- ❌ Auto-reply rules engine

**Technical Approach:**
```python
# Pseudocode
async def generate_ai_response(conversation_id: int, incoming_message: str):
    # 1. Get conversation history
    messages = await get_conversation_history(conversation_id)

    # 2. Build context
    context = {
        "lead": conversation.lead,
        "previous_messages": messages,
        "demo_site": conversation.demo_site,
        "video": conversation.video
    }

    # 3. AI generates response
    response = await ai_council_query(
        prompt=f"""
        Conversation history: {messages}
        Latest message: {incoming_message}
        Lead context: {context}

        Generate a helpful, personalized response...
        """,
        model="claude-4.5-sonnet"
    )

    # 4. Store as suggestion (human approval before sending)
    suggestion = AISuggestion(
        conversation_id=conversation_id,
        suggested_response=response,
        status="pending_approval"
    )

    return suggestion
```

**Effort to Complete:** 80 hours

---

#### 12. AI-GYM Multi-Model Optimization (❌ 0%)
**Status:** NOT IMPLEMENTED (Critical Gap)
**What Works:**
- ❌ Nothing - feature completely missing from UI and backend

**What's Needed:**
- ✅ Database schema exists (`model_metrics`, `ab_test_variants` tables)
- ❌ AI Council implementation
- ❌ Model performance tracking
- ❌ A/B test framework
- ❌ Cost tracking per model
- ❌ Quality scoring system
- ❌ Admin dashboard for AI-GYM

**See Dedicated Section:** [AI-GYM Multi-Model Optimization](#ai-gym-multi-model-optimization)

---

#### 13. n8n Integration (⚠️ 50% - UI Only)
**Status:** FRONTEND ONLY
**What Works:**
- ✅ Webhook configuration UI
- ✅ Workflow trigger UI
- ✅ Approval queue UI

**What's Missing:**
- ❌ n8n webhook endpoints (`/api/v1/n8n-webhooks/*`)
- ❌ Workflow orchestration
- ❌ Webhook queue processing
- ❌ n8n API integration
- ❌ Workflow status tracking

**Technical Approach:**
- n8n runs as separate service
- Our app sends webhooks to n8n workflows
- n8n calls our webhooks for data/actions
- `webhook_queue` table manages async processing

**Effort to Complete:** 40 hours

---

#### 14. Approval Workflows (⚠️ 50% - UI Only)
**Status:** FRONTEND ONLY
**What Works:**
- ✅ Approval queue UI
- ✅ Item review interface
- ✅ Approve/reject buttons

**What's Missing:**
- ❌ Approval endpoints (`/api/v1/workflow-approvals/*`)
- ❌ Approval queue processing
- ❌ Role-based permissions
- ❌ Approval history tracking
- ❌ Notification on approval needed

**Effort to Complete:** 30 hours

---

## Architectural Decisions

### 1. Why FastAPI + React (Not Django/Vue/Angular)

**Decision:** Use FastAPI backend with React frontend

**Rationale:**
- **FastAPI chosen for:**
  - Native async/await support (critical for scraping workloads)
  - Automatic OpenAPI documentation
  - High performance (comparable to Node.js)
  - Python ecosystem for AI/ML libraries
  - Type hints and Pydantic validation

- **React chosen for:**
  - Rich component ecosystem (shadcn/ui)
  - TypeScript support for type safety
  - Vite for fast development/builds
  - Large talent pool
  - Excellent WebSocket support

**Tradeoffs:**
- ✅ Pros: Performance, type safety, modern stack
- ❌ Cons: Two language ecosystems to maintain

---

### 2. Why PostgreSQL (Not MongoDB)

**Decision:** Use PostgreSQL as primary database

**Rationale:**
- Relational data model fits our domain (leads, conversations, videos, etc.)
- JSONB columns provide flexibility where needed
- Strong ACID guarantees for financial/transactional data
- Excellent full-text search (useful for lead search)
- pgvector extension for future AI/embeddings

**Tradeoffs:**
- ✅ Pros: Data integrity, powerful queries, mature tooling
- ❌ Cons: More complex schema changes than NoSQL

---

### 3. Why Playwright (Not Puppeteer/Selenium)

**Decision:** Use Playwright for web scraping

**Rationale:**
- Auto-waits for elements (more reliable than Puppeteer)
- Better handling of modern SPAs
- Built-in network interception
- Cross-browser support (Chromium, Firefox, WebKit)
- Excellent documentation

**Tradeoffs:**
- ✅ Pros: Reliability, modern API, active development
- ❌ Cons: Slightly heavier than Puppeteer

---

### 4. Why OpenRouter (Not Direct OpenAI/Anthropic)

**Decision:** Use OpenRouter as AI gateway

**Rationale:**
- Single API for multiple models (Claude, GPT-4, DeepSeek, etc.)
- Unified billing
- Easy model switching for A/B testing
- Fallback support if one model is down
- Cost optimization across providers

**Tradeoffs:**
- ✅ Pros: Flexibility, cost optimization, redundancy
- ❌ Cons: Additional abstraction layer, slight latency

---

### 5. Why Redis (Not RabbitMQ/Kafka)

**Decision:** Use Redis for caching and job queues

**Rationale:**
- Simple setup and operation
- Works well for our scale (not billions of jobs)
- Also useful for caching (dual purpose)
- Good Python support (rq, arq libraries)
- Persistent queues with AOF

**Tradeoffs:**
- ✅ Pros: Simplicity, dual purpose, fast
- ❌ Cons: Not as feature-rich as Kafka for complex streaming

---

### 6. Why Bypass Alembic (Use create_tables_simple.py)

**Decision:** Bypass Alembic migrations, create tables directly from models

**Rationale:**
- Alembic migrations were broken and time-consuming to fix
- For development/MVP, direct table creation is faster
- Can revisit proper migrations later for production
- Team is small, can manage schema changes manually

**Tradeoffs:**
- ✅ Pros: Fast unblocking, less complexity
- ❌ Cons: No migration history, harder to rollback changes

**Future Plan:** Re-enable Alembic for production deployments

---

### 7. Why AI Council (Multi-Model Query)

**Decision:** Query multiple AI models simultaneously for critical tasks

**Rationale:**
- Different models excel at different tasks
- Reduces single-model bias
- Can compare outputs and choose best
- Redundancy if one model fails
- Enables AI-GYM optimization

**Implementation:**
```python
async def ai_council_query(prompt: str, models: List[str]):
    """Query multiple AI models in parallel."""
    tasks = [
        query_model(prompt, model="claude-4.5-sonnet"),
        query_model(prompt, model="gpt-4-turbo"),
        query_model(prompt, model="deepseek-chat"),
    ]
    responses = await asyncio.gather(*tasks)
    return select_best_response(responses)
```

**Use Cases:**
- Website analysis (different models see different issues)
- Code generation (compare quality)
- Email response generation (tone/style variations)

---

### 8. Why Separate Video Tables (Not Just demo_sites.video_url)

**Decision:** Create dedicated tables for video creation pipeline

**Rationale:**
- Videos involve multiple steps (script → voiceover → recording → composition)
- Need to track each step independently
- Enables retries of individual steps
- Better analytics (which step fails most?)
- Allows video creation without demo site (future use case)

**Schema Design:**
```sql
video_scripts → voiceovers → screen_recordings → composed_videos
```

---

### 9. Why Webhook Queue (Not Direct n8n Calls)

**Decision:** Queue webhooks to n8n instead of synchronous calls

**Rationale:**
- n8n might be down (don't block our app)
- Retry logic for failed webhooks
- Rate limiting to n8n
- Audit trail of all webhook calls
- Enables batching webhooks

**Tradeoffs:**
- ✅ Pros: Reliability, decoupling, observability
- ❌ Cons: Eventual consistency (not immediate)

---

### 10. Why Approval Queue (Not Auto-Send Everything)

**Decision:** Human approval required before sending emails/videos

**Rationale:**
- AI can make mistakes (hallucinations, inappropriate tone)
- Legal/brand risk if AI sends bad content
- Enables quality control
- Builds trust with users
- Can be disabled for trusted AI models later

**Implementation:**
- All AI-generated content goes to `approval_queue`
- User reviews and approves/rejects
- Approved items trigger actual send
- Track approval rates per model (AI-GYM)

---

## Feature Specifications

### Craigslist Scraping (Detailed)

**Endpoint:** `POST /api/v1/scraper/jobs`

**Request:**
```json
{
  "locations": ["sfbay", "newyork", "losangeles"],
  "categories": ["ggg", "csr"],
  "keywords": ["web design", "SEO"],
  "search_distance": 0,
  "has_image": true,
  "posted_today": false,
  "max_results": 100
}
```

**Process Flow:**
1. Validate locations exist in database
2. Create job record with status="pending"
3. Enqueue job to Redis
4. Return job_id immediately
5. Worker picks up job:
   - For each location + category combination:
     - Navigate to Craigslist search page
     - Apply filters (keywords, has_image, etc.)
     - Scrape listing titles, URLs, prices, dates
     - For each listing:
       - Visit listing detail page
       - Extract: description, images, contact info
       - Store in leads table
   - Update job status via WebSocket
6. Mark job complete

**Error Handling:**
- CAPTCHA encountered → Queue for 2Captcha solving → Retry
- Rate limited → Exponential backoff
- Page load timeout → Skip and continue
- Network error → Retry up to 3 times

---

### Google Maps Scraping (Specification)

**Endpoint:** `POST /api/v1/google-maps/scrape`

**Request:**
```json
{
  "query": "web design agency",
  "location": "San Francisco, CA",
  "radius_miles": 25,
  "max_results": 50,
  "include_reviews": false
}
```

**Process Flow:**
1. Navigate to Google Maps search
2. Enter query + location
3. Scroll results to load all listings
4. For each business:
   - Extract: name, address, phone, website, rating, review_count
   - Click business → Get full details
   - Optionally scrape reviews
5. Store in leads with `source='google_maps'`

**Challenges:**
- Google's anti-bot detection (need rotating proxies)
- Dynamic loading (need proper waits)
- Inconsistent HTML structure

---

### Website Analysis Agent (Specification)

**Endpoint:** `POST /api/v1/website-analysis/analyze`

**Request:**
```json
{
  "url": "https://example.com",
  "depth": "comprehensive",
  "include_screenshot": true
}
```

**Analysis Components:**

1. **Design Analysis**
   - Color scheme evaluation
   - Typography assessment
   - Layout/spacing review
   - Visual hierarchy
   - Brand consistency

2. **SEO Analysis**
   - Meta tags (title, description)
   - Header structure (H1, H2, H3)
   - Alt text on images
   - Internal linking
   - Mobile-friendliness
   - Page speed

3. **Performance Analysis**
   - Load time
   - Bundle size
   - Image optimization
   - Caching headers
   - Lighthouse scores

4. **Accessibility Analysis**
   - ARIA labels
   - Keyboard navigation
   - Color contrast
   - Screen reader compatibility
   - WCAG compliance

**AI Prompt:**
```
Analyze this website:
URL: {url}
HTML: {html}
Screenshot: [image]
Lighthouse: {lighthouse_scores}

Provide:
1. Overall score (0-100)
2. Design issues and strengths
3. SEO issues and strengths
4. Performance issues and strengths
5. Accessibility issues and strengths
6. Top 10 improvement recommendations (prioritized)

Format: JSON
```

**Response:**
```json
{
  "overall_score": 72,
  "design": {
    "score": 68,
    "issues": ["Poor color contrast", "Inconsistent spacing"],
    "strengths": ["Modern typography", "Clear CTA buttons"]
  },
  "seo": {
    "score": 81,
    "issues": ["Missing H1 tag", "No meta description"],
    "strengths": ["Fast load time", "Mobile responsive"]
  },
  "improvements": [
    {
      "id": "imp-1",
      "category": "design",
      "priority": "high",
      "title": "Improve color contrast",
      "description": "Text-to-background contrast is below WCAG AA",
      "impact": "Better readability, accessibility",
      "difficulty": "easy",
      "code_example": "color: #333; background: #fff;"
    }
  ]
}
```

---

### Demo Site Builder (Specification)

**Endpoint:** `POST /api/v1/demo-sites/generate`

**Request:**
```json
{
  "lead_id": 123,
  "original_url": "https://example.com",
  "improvement_plan_id": 456,
  "framework": "react",
  "include_comments": true,
  "auto_deploy": true,
  "deployment_provider": "vercel"
}
```

**Code Generation Process:**

1. **Analyze Original Site**
   - Fetch HTML, CSS, JavaScript
   - Extract content, structure, assets
   - Identify frameworks used

2. **Build Context for AI**
   ```python
   context = {
       "original_html": html,
       "original_css": css,
       "content": extracted_content,
       "improvement_plan": improvements,
       "target_framework": "react",
       "style_guide": {
           "colors": ["#1a1a1a", "#f0f0f0"],
           "fonts": ["Inter", "sans-serif"],
           "design_system": "modern-minimal"
       }
   }
   ```

3. **AI Prompt**
   ```
   You are an expert web developer. Generate a complete {framework} website that:

   1. Implements these improvements:
   {improvement_plan}

   2. Uses this content from the original site:
   {content}

   3. Follows this style guide:
   {style_guide}

   Requirements:
   - Production-ready code
   - Responsive design (mobile, tablet, desktop)
   - Accessibility (WCAG AA)
   - SEO optimized
   - Fast load time
   - Include inline comments explaining improvements

   Output Format:
   {
     "files": {
       "src/App.tsx": "...",
       "src/components/Header.tsx": "...",
       "src/styles/globals.css": "...",
       "package.json": "...",
       ...
     },
     "deployment_config": {
       "build_command": "npm run build",
       "output_directory": "dist",
       "install_command": "npm install"
     }
   }
   ```

4. **Validate Generated Code**
   ```python
   def validate_generated_code(files: Dict[str, str], framework: str):
       checks = []

       # Check required files exist
       required = get_required_files(framework)
       checks.append(all(f in files for f in required))

       # Check no placeholders
       placeholders = ["TODO", "FIXME", "{your-api-key}"]
       has_placeholders = any(p in content for content in files.values() for p in placeholders)
       checks.append(not has_placeholders)

       # Check syntax (run ESLint, tsc, etc.)
       syntax_valid = run_linter(files, framework)
       checks.append(syntax_valid)

       return all(checks)
   ```

5. **Deploy to Preview**
   ```python
   async def deploy_to_vercel(files: Dict[str, str]):
       # Create temp directory
       temp_dir = create_temp_directory()

       # Write files
       for path, content in files.items():
           write_file(temp_dir / path, content)

       # Deploy via Vercel CLI
       result = await run_command(f"vercel --prod --cwd {temp_dir}")

       # Extract preview URL
       preview_url = extract_url(result.stdout)

       return preview_url
   ```

**Quality Metrics:**
- Code validity (does it run?)
- Design quality (matches mockup?)
- Performance (Lighthouse score)
- Accessibility (a11y audit pass?)
- SEO (meta tags, structure)

---

### Video Creation System (Specification)

**Endpoint:** `POST /api/v1/videos/create`

**Request:**
```json
{
  "demo_site_id": 789,
  "style": "professional",
  "voice": "male-us-1",
  "duration_seconds": 60,
  "include_music": false
}
```

**Pipeline Stages:**

#### Stage 1: Script Generation
```python
async def generate_script(demo_site_id: int, duration_seconds: int):
    demo = await get_demo_site(demo_site_id)

    prompt = f"""
    Create a {duration_seconds}-second video script for this website demo:

    Demo URL: {demo.preview_url}
    Improvements: {demo.improvements_applied}
    Target Audience: Small business owners

    Script should:
    - Intro (5s): Hook viewer
    - Problem (15s): Current website issues
    - Solution (30s): Show improvements in demo
    - CTA (10s): Next steps

    Format:
    {{
      "segments": [
        {{"timecode": "0:00", "narration": "...", "action": "Show homepage"}},
        {{"timecode": "0:05", "narration": "...", "action": "Highlight header"}}
      ]
    }}
    """

    script_json = await ai_query(prompt)

    return VideoScript(
        demo_site_id=demo_site_id,
        script_json=script_json,
        estimated_duration=duration_seconds
    )
```

#### Stage 2: Voiceover Generation
```python
async def generate_voiceover(script: VideoScript, voice: str):
    # Combine all narration segments
    full_text = " ".join(s["narration"] for s in script.segments)

    # Call ElevenLabs API
    audio_bytes = await elevenlabs_tts(
        text=full_text,
        voice_id=voice,
        model="eleven_monolingual_v1"
    )

    # Upload to S3
    audio_url = await upload_to_s3(audio_bytes, f"voiceovers/{uuid4()}.mp3")

    return Voiceover(
        script_id=script.id,
        audio_url=audio_url,
        duration_seconds=get_audio_duration(audio_bytes),
        voice_id=voice
    )
```

#### Stage 3: Screen Recording
```python
async def record_screen(demo_site_id: int, script: VideoScript):
    demo = await get_demo_site(demo_site_id)

    # Launch browser
    browser = await playwright.chromium.launch()
    page = await browser.new_page()

    # Start video recording
    recorder = await page.video.start()

    # Execute script actions
    for segment in script.segments:
        await page.goto(demo.preview_url)

        # Perform action (scroll, click, hover, etc.)
        action = segment["action"]
        if "scroll" in action:
            await page.mouse.wheel(0, 500)
        elif "click" in action:
            selector = extract_selector(action)
            await page.click(selector)

        # Wait for segment duration
        await asyncio.sleep(segment["duration"])

    # Stop recording
    video_path = await recorder.stop()

    # Upload to S3
    video_url = await upload_to_s3(video_path, f"recordings/{uuid4()}.webm")

    return ScreenRecording(
        demo_site_id=demo_site_id,
        video_url=video_url,
        duration_seconds=script.estimated_duration
    )
```

#### Stage 4: Video Composition
```python
async def compose_video(recording: ScreenRecording, voiceover: Voiceover):
    # Download assets
    video_path = await download(recording.video_url)
    audio_path = await download(voiceover.audio_url)

    # FFmpeg composition
    output_path = f"/tmp/{uuid4()}.mp4"

    await run_command(f"""
        ffmpeg -i {video_path} -i {audio_path} \
        -c:v libx264 -preset slow -crf 22 \
        -c:a aac -b:a 192k \
        -movflags +faststart \
        {output_path}
    """)

    # Upload final video
    final_url = await upload_to_s3(output_path, f"videos/{uuid4()}.mp4")

    return ComposedVideo(
        screen_recording_id=recording.id,
        voiceover_id=voiceover.id,
        video_url=final_url,
        file_size_bytes=os.path.getsize(output_path),
        duration_seconds=recording.duration_seconds
    )
```

**Error Handling:**
- Script generation fails → Retry with different model
- Voiceover fails → Retry or use backup TTS service
- Recording fails → Retry with fresh browser instance
- Composition fails → Check FFmpeg logs, retry

---

## AI-GYM Multi-Model Optimization

### Concept

**AI-GYM** is a system for determining which AI models perform best for specific tasks, enabling cost optimization and quality improvement through data-driven model selection.

### Core Principles

1. **Model Agnostic:** Works with any AI model (OpenAI, Anthropic, DeepSeek, etc.)
2. **Task-Specific:** Different models excel at different tasks
3. **Data-Driven:** Use real metrics, not assumptions
4. **Continuous Learning:** Performance tracking improves over time
5. **Cost-Aware:** Balance quality vs. cost

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      AI-GYM Core                         │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Model Router │  │ Metric       │  │ A/B Test     │ │
│  │              │  │ Tracker      │  │ Manager      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │            Model Performance DB                   │  │
│  │   (model_metrics, ab_test_variants tables)       │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
  ┌──────────┐        ┌──────────┐        ┌──────────┐
  │ Claude   │        │ GPT-4    │        │ DeepSeek │
  │ 4.5      │        │ Turbo    │        │ Chat     │
  └──────────┘        └──────────┘        └──────────┘
```

### Implementation

#### 1. Model Registry

```python
# app/services/ai_gym/models.py

class AIModel:
    """Represents an AI model with its capabilities."""

    id: str  # "claude-4.5-sonnet"
    provider: str  # "anthropic"
    cost_per_1k_tokens: Decimal
    max_tokens: int
    supports_vision: bool
    supports_function_calling: bool
    latency_ms: int  # average response time

AVAILABLE_MODELS = [
    AIModel(
        id="claude-4.5-sonnet",
        provider="anthropic",
        cost_per_1k_tokens=Decimal("0.003"),
        max_tokens=200_000,
        supports_vision=True,
        supports_function_calling=True,
        latency_ms=1200
    ),
    AIModel(
        id="gpt-4-turbo",
        provider="openai",
        cost_per_1k_tokens=Decimal("0.01"),
        max_tokens=128_000,
        supports_vision=True,
        supports_function_calling=True,
        latency_ms=800
    ),
    AIModel(
        id="deepseek-chat",
        provider="deepseek",
        cost_per_1k_tokens=Decimal("0.00014"),
        max_tokens=32_000,
        supports_vision=False,
        supports_function_calling=True,
        latency_ms=2000
    ),
    # ... more models
]
```

#### 2. Task Types

```python
# app/services/ai_gym/tasks.py

class TaskType(str, Enum):
    WEBSITE_ANALYSIS = "website_analysis"
    CODE_GENERATION = "code_generation"
    EMAIL_WRITING = "email_writing"
    CONVERSATION_RESPONSE = "conversation_response"
    VIDEO_SCRIPT = "video_script"
    LEAD_SCORING = "lead_scoring"

class TaskMetrics:
    """Metrics for evaluating task performance."""

    # Universal metrics
    latency_ms: int
    cost_usd: Decimal
    tokens_used: int

    # Task-specific metrics
    quality_score: float  # 0-100
    user_approval_rate: float  # % of time human approves
    edit_distance: int  # How much human edited AI output
    task_success: bool  # Did task complete successfully?

    # Custom metrics per task type
    custom_metrics: Dict[str, Any]
```

#### 3. Model Router

```python
# app/services/ai_gym/router.py

class ModelRouter:
    """Routes AI tasks to optimal model."""

    async def route(
        self,
        task_type: TaskType,
        prompt: str,
        strategy: str = "best_quality"  # or "best_cost", "balanced"
    ) -> AIModel:
        """Select best model for task."""

        # Get historical performance
        metrics = await self.get_task_metrics(task_type)

        if strategy == "best_quality":
            # Choose model with highest quality score
            return max(metrics, key=lambda m: m.quality_score)

        elif strategy == "best_cost":
            # Choose cheapest model meeting quality threshold
            acceptable = [m for m in metrics if m.quality_score >= 70]
            return min(acceptable, key=lambda m: m.cost_usd)

        elif strategy == "balanced":
            # Optimize for quality/cost ratio
            return max(metrics, key=lambda m: m.quality_score / m.cost_usd)

    async def route_council(
        self,
        task_type: TaskType,
        prompt: str,
        num_models: int = 3
    ) -> List[AIModel]:
        """Select multiple models for AI council."""

        metrics = await self.get_task_metrics(task_type)

        # Choose diverse models (different providers)
        diverse_models = []
        providers_used = set()

        for model in sorted(metrics, key=lambda m: m.quality_score, reverse=True):
            if model.provider not in providers_used:
                diverse_models.append(model)
                providers_used.add(model.provider)

            if len(diverse_models) >= num_models:
                break

        return diverse_models
```

#### 4. Metric Tracker

```python
# app/services/ai_gym/tracker.py

class MetricTracker:
    """Tracks AI model performance metrics."""

    async def record_execution(
        self,
        model_id: str,
        task_type: TaskType,
        prompt: str,
        response: str,
        metrics: TaskMetrics
    ):
        """Record a model execution with metrics."""

        # Store in database
        metric_record = ModelMetric(
            model_id=model_id,
            task_type=task_type,
            prompt_tokens=metrics.tokens_used,
            completion_tokens=len(response.split()),
            latency_ms=metrics.latency_ms,
            cost_usd=metrics.cost_usd,
            quality_score=metrics.quality_score,
            user_approved=None,  # Set later by human
            created_at=datetime.utcnow()
        )

        await db.add(metric_record)

        # Update rolling averages
        await self.update_model_stats(model_id, task_type)

    async def record_user_feedback(
        self,
        metric_id: int,
        approved: bool,
        edit_distance: int = 0,
        feedback_text: str = None
    ):
        """Record human feedback on AI output."""

        metric = await db.get(ModelMetric, metric_id)
        metric.user_approved = approved
        metric.edit_distance = edit_distance
        metric.feedback_text = feedback_text

        # Update model stats with new feedback
        await self.update_model_stats(metric.model_id, metric.task_type)
```

#### 5. A/B Testing

```python
# app/services/ai_gym/ab_testing.py

class ABTestManager:
    """Manages A/B tests between models."""

    async def create_test(
        self,
        task_type: TaskType,
        model_a: str,
        model_b: str,
        duration_days: int = 7,
        sample_size: int = 100
    ) -> ABTest:
        """Create new A/B test."""

        test = ABTest(
            task_type=task_type,
            variant_a=ABTestVariant(
                model_id=model_a,
                traffic_percentage=50
            ),
            variant_b=ABTestVariant(
                model_id=model_b,
                traffic_percentage=50
            ),
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=duration_days),
            target_sample_size=sample_size
        )

        await db.add(test)
        return test

    async def assign_variant(
        self,
        task_type: TaskType
    ) -> str:
        """Assign user to test variant."""

        # Get active test
        test = await self.get_active_test(task_type)
        if not test:
            # No active test, use default routing
            return await self.router.route(task_type)

        # Randomly assign based on traffic percentage
        rand = random.random() * 100

        if rand < test.variant_a.traffic_percentage:
            return test.variant_a.model_id
        else:
            return test.variant_b.model_id

    async def analyze_test(
        self,
        test_id: int
    ) -> ABTestResults:
        """Analyze A/B test results."""

        test = await db.get(ABTest, test_id)

        # Get metrics for each variant
        metrics_a = await self.get_variant_metrics(test.variant_a.id)
        metrics_b = await self.get_variant_metrics(test.variant_b.id)

        # Calculate statistical significance
        significance = self.calculate_significance(metrics_a, metrics_b)

        # Determine winner
        winner = None
        if significance.p_value < 0.05:
            if metrics_a.quality_score > metrics_b.quality_score:
                winner = test.variant_a.model_id
            else:
                winner = test.variant_b.model_id

        return ABTestResults(
            test_id=test_id,
            variant_a_metrics=metrics_a,
            variant_b_metrics=metrics_b,
            statistical_significance=significance,
            winner=winner,
            recommendation="Deploy variant A" if winner == test.variant_a.model_id else "Deploy variant B"
        )
```

### Quality Scoring

```python
# app/services/ai_gym/quality.py

class QualityScorer:
    """Scores AI output quality."""

    async def score(
        self,
        task_type: TaskType,
        output: str,
        expected: Optional[str] = None,
        context: Dict[str, Any] = None
    ) -> float:
        """Calculate quality score (0-100)."""

        if task_type == TaskType.CODE_GENERATION:
            return await self.score_code_generation(output, context)
        elif task_type == TaskType.WEBSITE_ANALYSIS:
            return await self.score_website_analysis(output, context)
        elif task_type == TaskType.EMAIL_WRITING:
            return await self.score_email_writing(output, context)
        # ... other task types

    async def score_code_generation(
        self,
        code: str,
        context: Dict[str, Any]
    ) -> float:
        """Score generated code quality."""

        scores = []

        # 1. Syntax validity (0-30 points)
        syntax_valid = await self.check_syntax(code, context["framework"])
        scores.append(30 if syntax_valid else 0)

        # 2. No placeholders (0-20 points)
        has_placeholders = any(p in code for p in ["TODO", "FIXME", "...", "{your-"])
        scores.append(0 if has_placeholders else 20)

        # 3. Has required files (0-20 points)
        required_files = context.get("required_files", [])
        has_all_files = all(f in code for f in required_files)
        scores.append(20 if has_all_files else 0)

        # 4. Code quality (0-30 points)
        quality = await self.run_linter(code, context["framework"])
        scores.append(quality.score * 30)

        return sum(scores)

    async def score_website_analysis(
        self,
        analysis: dict,
        context: Dict[str, Any]
    ) -> float:
        """Score website analysis quality."""

        scores = []

        # 1. Completeness (0-40 points)
        required_sections = ["design", "seo", "performance", "accessibility"]
        has_all_sections = all(s in analysis for s in required_sections)
        scores.append(40 if has_all_sections else 0)

        # 2. Number of insights (0-30 points)
        total_insights = sum(len(analysis[s].get("issues", [])) for s in required_sections)
        insight_score = min(total_insights / 20 * 30, 30)  # Max 30 points for 20+ insights
        scores.append(insight_score)

        # 3. Actionability (0-30 points)
        # Check if improvements have code examples
        improvements = analysis.get("improvements", [])
        with_code = sum(1 for i in improvements if i.get("code_example"))
        actionability = with_code / len(improvements) * 30 if improvements else 0
        scores.append(actionability)

        return sum(scores)
```

### Dashboard UI

**New Page:** `frontend/src/pages/AIGym.tsx`

**Features:**
1. **Model Performance Table**
   - Show all models with metrics per task type
   - Columns: Model, Task Type, Quality Score, Approval Rate, Avg Cost, Avg Latency
   - Sortable and filterable

2. **Cost Optimization**
   - Current spend per model
   - Potential savings if switching to cheaper models
   - ROI calculation

3. **A/B Test Manager**
   - Create new tests
   - View active tests
   - Analyze completed tests

4. **Quality Trends**
   - Line chart showing quality scores over time
   - Compare multiple models

5. **Task Type Breakdown**
   - Which models are best for each task
   - Recommendations for model selection

### Integration Points

**1. Website Analysis**
```python
# Before
analysis = await analyze_website(url, model="claude-4.5-sonnet")

# After (with AI-GYM)
model = await ai_gym.route(TaskType.WEBSITE_ANALYSIS, strategy="balanced")
analysis = await analyze_website(url, model=model.id)
await ai_gym.record_execution(model.id, TaskType.WEBSITE_ANALYSIS, metrics)
```

**2. Code Generation**
```python
# Use AI council with top 3 models
models = await ai_gym.route_council(TaskType.CODE_GENERATION, num_models=3)

responses = await asyncio.gather(*[
    generate_code(prompt, model=m.id) for m in models
])

# Score each response
scored_responses = [
    (r, await quality_scorer.score(TaskType.CODE_GENERATION, r))
    for r in responses
]

# Return best response
best_response = max(scored_responses, key=lambda x: x[1])
```

**3. Email Writing**
```python
# A/B test between Claude and GPT-4
model = await ai_gym.assign_variant(TaskType.EMAIL_WRITING)
email = await generate_email(prompt, model=model)

# Later, when user approves/edits
await ai_gym.record_user_feedback(
    metric_id=email.metric_id,
    approved=True,
    edit_distance=len(diff(original_email, edited_email))
)
```

### Effort to Complete

**Backend (AI-GYM Core):** 80 hours
- Model registry and router: 16 hours
- Metric tracking: 24 hours
- A/B testing framework: 24 hours
- Quality scoring: 16 hours

**Frontend (Dashboard):** 40 hours
- Performance tables: 12 hours
- Charts and visualizations: 16 hours
- A/B test UI: 12 hours

**Integration:** 40 hours
- Update all AI calls to use router: 24 hours
- Add quality scoring to all tasks: 16 hours

**Total: 160 hours**

---

## Frontend UX Improvements

### Problem

The frontend UI shows features that don't exist in the backend, creating user confusion and frustration when features return 404 errors.

### Solutions

#### Option 1: Feature Flags with Status Indicators

Add status badges to show which features are available:

```tsx
// components/FeatureStatus.tsx
export type FeatureStatus = 'available' | 'coming_soon' | 'beta'

interface FeatureStatusProps {
  status: FeatureStatus
  tooltip?: string
}

export function FeatureStatusBadge({ status, tooltip }: FeatureStatusProps) {
  const config = {
    available: {
      color: 'bg-green-500',
      text: 'Available',
      icon: CheckIcon
    },
    coming_soon: {
      color: 'bg-yellow-500',
      text: 'Coming Soon',
      icon: ClockIcon
    },
    beta: {
      color: 'bg-blue-500',
      text: 'Beta',
      icon: BeakerIcon
    }
  }

  const { color, text, icon: Icon } = config[status]

  return (
    <Tooltip content={tooltip}>
      <span className={`${color} text-white px-2 py-1 rounded text-xs flex items-center gap-1`}>
        <Icon className="w-3 h-3" />
        {text}
      </span>
    </Tooltip>
  )
}
```

**Usage in UI:**
```tsx
// pages/Videos.tsx
<PageHeader
  title="Video Creation"
  trailing={<FeatureStatusBadge status="coming_soon" tooltip="Backend implementation in progress" />}
/>
```

#### Option 2: Disable Non-Functional Pages

Update navigation to disable/hide pages without backend:

```tsx
// components/Layout.tsx
const navigation = [
  { name: 'Scraper', href: '/scraper', enabled: true },
  { name: 'Leads', href: '/leads', enabled: true },
  { name: 'Videos', href: '/videos', enabled: false, tooltip: 'Coming soon' },
  { name: 'Demo Sites', href: '/demos', enabled: false, tooltip: 'Coming soon' },
  { name: 'Approvals', href: '/approvals', enabled: false, tooltip: 'Coming soon' },
  // ...
]

{navigation.map((item) => (
  <Tooltip key={item.name} content={item.enabled ? undefined : item.tooltip}>
    <Link
      to={item.href}
      className={cn(
        item.enabled ? 'text-white' : 'text-gray-500 cursor-not-allowed',
        'px-3 py-2 rounded-md'
      )}
      onClick={(e) => !item.enabled && e.preventDefault()}
    >
      {item.name}
      {!item.enabled && <LockIcon className="w-4 h-4 ml-2 inline" />}
    </Link>
  </Tooltip>
))}
```

#### Option 3: Graceful Degradation with Placeholders

Show page with explanation instead of errors:

```tsx
// components/ComingSoonPlaceholder.tsx
interface ComingSoonProps {
  feature: string
  description: string
  estimatedRelease?: string
  mockupImage?: string
}

export function ComingSoonPlaceholder({
  feature,
  description,
  estimatedRelease,
  mockupImage
}: ComingSoonProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8 text-center">
      <RocketIcon className="w-16 h-16 text-terminal-500 mb-4" />

      <h2 className="text-2xl font-bold text-dark-text-primary mb-2">
        {feature} Coming Soon
      </h2>

      <p className="text-dark-text-secondary mb-6 max-w-md">
        {description}
      </p>

      {estimatedRelease && (
        <p className="text-sm text-terminal-500 mb-4">
          Estimated Release: {estimatedRelease}
        </p>
      )}

      {mockupImage && (
        <img
          src={mockupImage}
          alt={`${feature} mockup`}
          className="rounded-lg shadow-lg max-w-2xl opacity-50"
        />
      )}

      <Button variant="outline" className="mt-6">
        Notify Me When Available
      </Button>
    </div>
  )
}
```

**Usage:**
```tsx
// pages/Videos.tsx
export function VideosPage() {
  return (
    <ComingSoonPlaceholder
      feature="Video Creation"
      description="AI-powered Loom-style video generation is currently in development. Soon you'll be able to create professional demo videos automatically from your demo sites."
      estimatedRelease="Q2 2025"
      mockupImage="/mockups/video-creation.png"
    />
  )
}
```

#### Option 4: Feature Roadmap Page

Add dedicated roadmap page showing all planned features:

```tsx
// pages/Roadmap.tsx
interface RoadmapItem {
  feature: string
  status: 'completed' | 'in_progress' | 'planned'
  progress: number  // 0-100
  quarter: string
  dependencies: string[]
}

const roadmap: RoadmapItem[] = [
  {
    feature: 'Craigslist Scraping',
    status: 'completed',
    progress: 100,
    quarter: 'Q4 2024',
    dependencies: []
  },
  {
    feature: 'Google Maps Scraping',
    status: 'planned',
    progress: 0,
    quarter: 'Q1 2025',
    dependencies: []
  },
  {
    feature: 'Website Analysis Agent',
    status: 'planned',
    progress: 0,
    quarter: 'Q1 2025',
    dependencies: ['Google Maps Scraping']
  },
  {
    feature: 'Demo Site Builder',
    status: 'planned',
    progress: 0,
    quarter: 'Q2 2025',
    dependencies: ['Website Analysis Agent']
  },
  {
    feature: 'Video Creation',
    status: 'planned',
    progress: 0,
    quarter: 'Q2 2025',
    dependencies: ['Demo Site Builder']
  },
  {
    feature: 'AI-GYM',
    status: 'in_progress',
    progress: 20,
    quarter: 'Q1 2025',
    dependencies: []
  },
]

export function RoadmapPage() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Product Roadmap</h1>

      <div className="space-y-4">
        {roadmap.map((item) => (
          <RoadmapCard key={item.feature} item={item} />
        ))}
      </div>
    </div>
  )
}
```

### Recommended Approach

**Combination of Options 1, 3, and 4:**

1. ✅ **Add feature status badges** to all navigation items (Option 1)
2. ✅ **Replace error-prone pages with ComingSoon placeholders** (Option 3)
3. ✅ **Create dedicated Roadmap page** showing implementation status (Option 4)
4. ✅ **Keep pages accessible** (don't disable) but show clear status

**Implementation Plan:**

1. Create `FeatureStatusBadge` component (2 hours)
2. Create `ComingSoonPlaceholder` component (3 hours)
3. Create `Roadmap` page (8 hours)
4. Update all pages with coming soon status:
   - Videos page (1 hour)
   - Demo Sites page (1 hour)
   - Approvals page (1 hour)
   - Workflows page (1 hour)
5. Update navigation with status badges (2 hours)
6. Add toast notifications explaining status on page load (2 hours)

**Total Effort: 21 hours**

---

## Development Roadmap

### Phase 1: MVP (P0 - Critical Path) - 8 Weeks

**Goal:** Deliver working Craigslist scraping with AI-powered insights

#### Sprint 1-2: Complete Craigslist Scraping (2 weeks, 80 hours)
- ✅ Implement CAPTCHA solving
- ✅ Add email extraction from listings
- ✅ Implement contact parsing
- ✅ Add advanced filtering
- ✅ Implement retry logic
- ✅ Add rate limiting

**Deliverable:** Reliable Craigslist scraping with 90%+ success rate

#### Sprint 3-4: Lead Management Enhancements (2 weeks, 80 hours)
- ✅ Implement advanced search
- ✅ Add lead scoring
- ✅ Implement bulk operations
- ✅ Add lead enrichment
- ✅ Implement deduplication

**Deliverable:** Complete lead management system

#### Sprint 5-6: Frontend UX Improvements (2 weeks, 80 hours)
- ✅ Add feature status badges
- ✅ Create ComingSoon placeholders
- ✅ Build Roadmap page
- ✅ Update all pages with status
- ✅ Add helpful error messages
- ✅ Improve loading states

**Deliverable:** Clear UX showing feature status

#### Sprint 7-8: AI-GYM Foundation (2 weeks, 80 hours)
- ✅ Implement model router
- ✅ Build metric tracking
- ✅ Create quality scoring
- ✅ Build dashboard UI
- ✅ Integrate with Craigslist scraping

**Deliverable:** Working AI-GYM tracking model performance

**Phase 1 Total: 320 hours**

---

### Phase 2: Multi-Source + Website Analysis (P1) - 12 Weeks

#### Sprint 9-11: Google Maps Scraping (3 weeks, 120 hours)
- ✅ Build Google Maps scraper
- ✅ Implement anti-bot evasion
- ✅ Add business info extraction
- ✅ Implement review scraping
- ✅ Create API endpoints
- ✅ Build frontend UI

**Deliverable:** Working Google Maps scraping

#### Sprint 12-14: Job Board Scraping (3 weeks, 120 hours)
- ✅ Build Indeed scraper
- ✅ Build Monster scraper
- ✅ Build ZipRecruiter scraper
- ✅ Implement deduplication
- ✅ Create API endpoints
- ✅ Build frontend UI

**Deliverable:** Multi-job-board scraping

#### Sprint 15-17: Website Analysis Agent (3 weeks, 120 hours)
- ✅ Implement HTML fetching
- ✅ Integrate Lighthouse
- ✅ Build AI analysis engine
- ✅ Implement screenshot capture
- ✅ Create improvement plan generator
- ✅ Build frontend UI

**Deliverable:** AI-powered website analysis

#### Sprint 18-20: Email Outreach System (3 weeks, 90 hours)
- ✅ Implement SMTP integration
- ✅ Build template engine
- ✅ Add campaign management
- ✅ Implement tracking
- ✅ Build frontend UI

**Deliverable:** Complete email outreach

**Phase 2 Total: 450 hours**

---

### Phase 3: Demo Sites + Videos (P2) - 14 Weeks

#### Sprint 21-25: Demo Site Builder (5 weeks, 200 hours)
- ✅ Implement AI code generation
- ✅ Build multi-framework support
- ✅ Add code validation
- ✅ Integrate Vercel/Netlify
- ✅ Build preview server
- ✅ Create frontend wizard

**Deliverable:** AI-generated demo sites

#### Sprint 26-28: Conversation AI (3 weeks, 120 hours)
- ✅ Implement reply parsing
- ✅ Build AI response engine
- ✅ Add context management
- ✅ Implement sentiment analysis
- ✅ Create approval workflow
- ✅ Build frontend UI

**Deliverable:** AI conversation handler

#### Sprint 29-34: Video Creation System (6 weeks, 240 hours)
- ✅ Implement script generation
- ✅ Integrate ElevenLabs TTS
- ✅ Build screen recording
- ✅ Implement FFmpeg composition
- ✅ Add CDN hosting
- ✅ Create frontend wizard

**Deliverable:** Automated video generation

**Phase 3 Total: 560 hours**

---

### Phase 4: Orchestration + Scale (P2) - 6 Weeks

#### Sprint 35-37: n8n Integration (3 weeks, 120 hours)
- ✅ Build webhook endpoints
- ✅ Implement queue processing
- ✅ Add n8n API integration
- ✅ Create workflow triggers
- ✅ Build frontend UI

**Deliverable:** n8n workflow orchestration

#### Sprint 38-40: Approval Workflows (3 weeks, 120 hours)
- ✅ Implement approval endpoints
- ✅ Build queue processing
- ✅ Add role-based permissions
- ✅ Implement notifications
- ✅ Create frontend UI

**Deliverable:** Human-in-the-loop approvals

**Phase 4 Total: 240 hours**

---

### Summary

| Phase | Duration | Effort | Priority | Status |
|-------|----------|--------|----------|--------|
| Phase 1: MVP | 8 weeks | 320 hours | P0 | 🟡 In Progress |
| Phase 2: Multi-Source | 12 weeks | 450 hours | P1 | ⬜ Not Started |
| Phase 3: Demo + Video | 14 weeks | 560 hours | P2 | ⬜ Not Started |
| Phase 4: Orchestration | 6 weeks | 240 hours | P2 | ⬜ Not Started |
| **TOTAL** | **40 weeks** | **1,570 hours** | - | **~20% Complete** |

**Assuming 40 hours/week:**
- Single developer: 40 weeks (10 months)
- Two developers: 20 weeks (5 months)
- Three developers: 13 weeks (3.25 months)

---

## Technical Debt & Known Issues

### 1. Alembic Migrations Broken

**Issue:** Database migrations don't work, using `create_tables_simple.py` workaround

**Impact:**
- Cannot track schema changes
- Difficult to rollback changes
- Production deployments risky

**Resolution Plan:**
1. Audit all models for migration conflicts
2. Create fresh migration baseline
3. Test migrations thoroughly
4. Document migration process
5. Add CI/CD checks for migrations

**Effort:** 40 hours
**Priority:** P1 (before production)

---

### 2. No Authentication/Authorization

**Issue:** No user authentication or role-based access control

**Impact:**
- Anyone can access all features
- No multi-tenant support
- No audit trail of who did what

**Resolution Plan:**
1. Implement JWT authentication
2. Add role-based permissions
3. Create user management UI
4. Add audit logging
5. Implement API key authentication

**Effort:** 80 hours
**Priority:** P0 (before launch)

---

### 3. No Error Monitoring

**Issue:** No Sentry/error tracking configured

**Impact:**
- Production errors go unnoticed
- Hard to debug user-reported issues
- No visibility into error rates

**Resolution Plan:**
1. Add Sentry SDK to backend
2. Add Sentry SDK to frontend
3. Configure error grouping
4. Set up alert notifications
5. Create error dashboard

**Effort:** 16 hours
**Priority:** P1

---

### 4. No Automated Tests

**Issue:** Zero test coverage (no unit, integration, or e2e tests)

**Impact:**
- High risk of regressions
- Difficult to refactor safely
- Slow development (manual testing)

**Resolution Plan:**
1. Add pytest for backend tests
2. Add Vitest for frontend tests
3. Add Playwright for e2e tests
4. Aim for 70%+ coverage
5. Add CI/CD test pipeline

**Effort:** 160 hours
**Priority:** P1

---

### 5. No Rate Limiting

**Issue:** API has no rate limiting or abuse prevention

**Impact:**
- Vulnerable to DoS attacks
- Scraping services could be abused
- Uncontrolled costs (AI API calls)

**Resolution Plan:**
1. Add rate limiting middleware
2. Implement per-user quotas
3. Add IP-based throttling
4. Monitor API usage
5. Add billing/usage dashboard

**Effort:** 40 hours
**Priority:** P0 (before launch)

---

### 6. No Logging Infrastructure

**Issue:** Minimal logging, no log aggregation

**Impact:**
- Hard to debug production issues
- No audit trail
- Cannot analyze usage patterns

**Resolution Plan:**
1. Add structured logging (Python logging)
2. Configure log levels
3. Add log aggregation (CloudWatch/Datadog)
4. Create log search dashboard
5. Set up log retention policies

**Effort:** 24 hours
**Priority:** P1

---

### 7. No Backup Strategy

**Issue:** No database backup or disaster recovery plan

**Impact:**
- Data loss risk
- No rollback capability
- Compliance issues

**Resolution Plan:**
1. Configure automated PostgreSQL backups
2. Test restore process
3. Add backup monitoring
4. Document DR procedures
5. Implement point-in-time recovery

**Effort:** 16 hours
**Priority:** P0 (before production data)

---

### 8. No Environment Parity

**Issue:** Development setup differs from production

**Impact:**
- "Works on my machine" issues
- Deployment surprises
- Hard to reproduce bugs

**Resolution Plan:**
1. Create production-like Docker Compose
2. Document environment differences
3. Add staging environment
4. Create deployment runbook
5. Automate deployments

**Effort:** 32 hours
**Priority:** P1

---

### 9. Hardcoded Configuration

**Issue:** Some settings hardcoded instead of environment variables

**Impact:**
- Cannot configure per environment
- Secrets in code (security risk)
- Difficult deployments

**Resolution Plan:**
1. Audit code for hardcoded values
2. Move to environment variables
3. Add config validation
4. Document all settings
5. Create .env.example templates

**Effort:** 16 hours
**Priority:** P1

---

### 10. No Performance Monitoring

**Issue:** No APM (Application Performance Monitoring)

**Impact:**
- Cannot identify slow endpoints
- No visibility into bottlenecks
- Poor user experience

**Resolution Plan:**
1. Add Datadog/New Relic APM
2. Instrument critical paths
3. Set up performance alerts
4. Create performance dashboard
5. Optimize slow queries

**Effort:** 24 hours
**Priority:** P2

---

## Conclusion

### Current State Summary

We have built **~20% of the planned system**:
- ✅ Core infrastructure is solid (FastAPI, PostgreSQL, React)
- ✅ Craigslist scraping works at a basic level
- ✅ Frontend UI exists for all features (but many lack backends)
- ✅ Database schema is complete (50+ tables)
- ⚠️ Significant technical debt (no auth, no tests, broken migrations)

### Path Forward

**Immediate Next Steps (Next 2 Weeks):**

1. ✅ **This Requirements Doc:** Review and finalize (now complete)
2. ✅ **Frontend UX:** Add feature status badges and ComingSoon placeholders (21 hours)
3. ✅ **Authentication:** Implement user auth before any production use (80 hours)
4. ✅ **Complete Craigslist Scraping:** Finish remaining features (40 hours)

**After MVP (Phase 1 Complete):**

4. Decide on Phase 2 priorities based on market feedback
5. Consider deprioritizing LinkedIn scraping (high risk/complexity)
6. Focus on AI-GYM to optimize costs early
7. Address critical technical debt (tests, monitoring, backups)

### Success Criteria

**MVP Success (Phase 1):**
- ✅ Craigslist scraping works reliably (90%+ success rate)
- ✅ Users can manage leads effectively
- ✅ AI-GYM shows which models perform best
- ✅ Clear UX showing what exists vs. coming soon
- ✅ Authentication and basic security in place

**Full Product Success (Phase 4):**
- ✅ Multi-source scraping (4+ sources)
- ✅ AI-powered website analysis
- ✅ Automated demo site generation
- ✅ Video creation pipeline working
- ✅ Email outreach with AI responses
- ✅ AI-GYM optimizing for cost and quality
- ✅ Production-ready with monitoring and backups

### Estimated Timeline

**Conservative Estimate (1 developer, 40 hrs/week):**
- MVP (Phase 1): 2 months
- Full Product (Phase 4): 10 months

**Aggressive Estimate (3 developers, 40 hrs/week):**
- MVP (Phase 1): 3 weeks
- Full Product (Phase 4): 3-4 months

### Final Notes

This document represents the complete picture of where we are and where we're going. The frontend UI created a false sense of completion—reality is we're at the beginning of the build, not the end.

**Key Takeaway:** We have a solid foundation (infrastructure, UI, database schema) but need sustained development effort to complete the backend functionality that makes this platform valuable.

The AI-GYM feature is the "secret sauce" that will make this platform competitive—it enables continuous optimization of AI costs and quality, which is critical for a system that relies heavily on AI.

Let's discuss priorities and next steps.

---

**Document Status:** ✅ Complete - Ready for Review
**Next Action:** Review with team, prioritize Phase 1 features, begin implementation
