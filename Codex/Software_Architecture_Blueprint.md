## Software Architecture Blueprint

### 1. Purpose
Provide the authoritative architecture baseline for the AI-powered outreach platform, blending existing Craigslist lead-gen capabilities with the new multi-agent, multi-source workflow. This document informs engineering design, DevOps provisioning, and governance decisions.

### 2. Context & Goals
- **Current Assets**: FastAPI backend, React/Vite frontend, PostgreSQL schema, Playwright-based Craigslist scraper, lead scoring ML services.
- **Target Outcomes**: Multi-source scraping, AI Council website analysis, automated demo/video generation, conversation automation, AI-GYM optimization, enterprise-ready analytics.
- **Constraints**: Maintain backwards compatibility with existing leads data; support phased rollout; ensure compliance (CAN-SPAM, GDPR) and observability.

### 3. Logical Architecture
```
┌──────────────────────────────────────────────────────────────────┐
│                           Experience Layer                        │
│  Next.js 14 (App Router) + shadcn/ui + React Query + Zustand       │
│  Dashboards · Campaign Ops · Approval Queue · AI-GYM Insights      │
└──────────────────────────────┬─────────────────────────────────────┘
                               │ GraphQL/REST (FastAPI)
┌───────────────────────────────┴───────────────────────────────────┐
│                          API Gateway Layer                        │
│  FastAPI 0.110 · JWT Auth · Rate Limiting · Validation · Webhooks │
└───────────────┬───────────────┬───────────────────┬───────────────┘
                │               │                   │
┌───────────────▼───────────────┴──────────────┬────▼────────────────┐
│                Service Fabric                │                      │
│  Scraping Orchestrator  Campaign Manager     │  Conversation Agent │
│  Website Analyzer      Demo Builder Service  │  Notification Hub   │
│  Video Automation      Email Personalization │  Analytics Engine   │
└───────────────┬──────────────────────────────┴──────────┬──────────┘
                │                                         │
┌───────────────▼───────────────┐        ┌────────────────▼───────────┐
│         AI Council Hub        │        │         Workflow Hub        │
│  Claude 4.5 · GPT-4o · DeepSeek│       │  n8n Orchestrator · Task Bus │
│  Qwen Max · Gemini 1.5 · Grok  │        │  Redis Streams · Celery      │
└───────────────┬───────────────┘        └────────────────┬───────────┘
                │                                         │
┌───────────────▼───────────────┐        ┌────────────────▼───────────┐
│         Data Platform         │        │     External Integrations   │
│ PostgreSQL · Redis · S3/CDN   │        │ Gmail API · Vercel · Loom   │
│ Pinecone/Weaviate · OpenRouter│        │ Playwright · ElevenLabs      │
└───────────────────────────────┘        └─────────────────────────────┘
```

### 4. Domain Breakdown
| Domain | Primary Services | Description |
|--------|-----------------|-------------|
| Acquisition | Scraping Orchestrator, Source Adapters | Multi-source lead capture (Craigslist, Google Maps, LinkedIn, Job Boards). |
| Intelligence | Website Analyzer, AI Council Hub | Multi-model insight aggregation, improvement plans, scoring augmentation. |
| Experience | Campaign Manager, Demo Builder, Video Automation | Personalized outreach assets (demo sites, videos, emails). |
| Engagement | Conversation Agent, Notification Hub | Reply handling, scheduling, multi-turn emails, human-in-the-loop approvals. |
| Optimization | Analytics Engine, AI-GYM Evaluator | Model performance tracking, A/B testing, KPI dashboards. |

### 5. Service Catalog

1. **Scraping Orchestrator**
   - Manages scraping jobs via n8n or Celery
   - Provides `/api/v2/scraping/jobs` endpoints
   - Pluggable source adapters (Craigslist, GoogleMaps, LinkedIn, Custom CSV)

2. **Website Analyzer Service**
   - Playwright crawler → structured DOM snapshot
   - AI Council prompts per perspective (SEO, UX, CRO, Content, Positioning)
   - Outputs stored into `website_analyses` and `improvement_plan`

3. **Demo Builder Service**
   - AI code-gen orchestrator with Vercel deployment API
   - Supports HTML/React templates, fallback to mockups
   - Automated QA pipeline (lighthouse, viewport checks)

4. **Video Automation Service**
   - Script generator + voice synthesis + Playwright recording
   - FFmpeg pipeline for composition, S3/CDN upload

5. **Email Personalization Service**
   - Template engine with AI Council copywriting
   - Gmail API + SendGrid fallback + warm-up logic
   - Tracking pixel and click proxy management

6. **Conversation Agent**
   - Monitors inbox via Gmail webhooks/polling
   - Intent detection, AI reply suggestions, HITL queue
   - Integrates knowledge base embeddings (Pinecone)

7. **Analytics & AI-GYM Engine**
   - Aggregates performance metrics per model, campaign, source
   - Generates leaderboards, ROI dashboards, recommendations

### 6. Data Architecture
- **PostgreSQL**: canonical store; migrations manage new tables (`demo_sites`, `videos`, `email_sends`, `ai_gym_performance`, `conversations`).
- **Redis**: caching (analysis results, dashboard caches) and job queue (with RQ/Celery).
- **Vector DB**: Pinecone/Weaviate for knowledge base, lead embeddings, similarity search.
- **Object Storage**: S3 + CloudFront for videos, static assets, demo archives.
- **Secrets**: AWS Secrets Manager / GCP Secret Manager, or Vault for API keys.

### 7. Integration Contracts
- **External APIs**: Gmail (send + webhook), OpenRouter (multi-model), Vercel (deploy), ElevenLabs (voice), Loom/S3 (video hosting), Playwright/Browserless (headless browsers).
- **Internal APIs**: Standardize on REST+JSON. Consider GraphQL read-only gateway for dashboards.
- **Events**: Use Redis streams or AWS SQS for asynchronous events (`lead.scraped`, `analysis.completed`, `demo.deployed`, `email.sent`, `reply.received`).

### 8. Infrastructure Topology
- **Frontend**: Vercel/Netlify for Next.js or containerized deployment (AWS Amplify). CI enforced preview deployments.
- **Backend**: Dockerized FastAPI behind API Gateway (AWS ALB or Cloudflare). Horizontal scaling via ECS/Kubernetes.
- **Workers**: Dedicated autoscaled queue workers for scraping, analysis, demo, video, email, AI tasks.
- **Observability**: OpenTelemetry collectors, Prometheus metrics, Grafana dashboards, ELK stack for logs.
- **Security**: JWT auth, mTLS between services, WAF, rate limiting (SlowAPI), secret rotation.

### 9. Non-Functional Requirements
- **Availability**: 99.5% for core APIs, 99.0% for async agents.
- **Scalability**: 1k+ emails/day, 500 concurrent analyses, 200 demo builds/day.
- **Latency**: API < 200ms p95, dashboard < 2s, job orchestration < 1 min dispatch.
- **Compliance**: CAN-SPAM, GDPR, SOC2-ready controls, audit logging retained 1 year.

### 10. Migration Strategy
1. Harden current stack (auth, rate limiting, tests) → baseline release.
2. Introduce new schema via additive migrations; backfill data.
3. Deploy AI Council services behind feature flags.
4. Gradually shift workflows to n8n orchestrations while ensuring rollback paths.

### 11. Open Decisions
- Choose between n8n self-hosted vs. orchestrating with Temporal/Celery.
- Determine GraphQL adoption vs. expanding REST for analytics aggregation.
- Select final vector DB vendor based on cost and latency requirements.
- Finalize hosting provider (AWS vs. GCP) and secret management tooling.

### 12. Approval
Architecture review board sign-off required prior to Sprint 0 kickoff. Updates tracked via ADRs stored alongside this document.

