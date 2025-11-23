## System Design Pivot – Legacy Alignment & Future Buildout

### 1. Document Purpose
Translate the architecture blueprint into actionable component designs. Defines how legacy modules evolve, details interfaces, data contracts, and sequencing necessary to blend existing Craigslist functionality with the AI-powered outreach vision.

### 2. Legacy Inventory & Target Mapping
| Legacy Module | Current State | Target Enhancement | Action |
|---------------|---------------|--------------------|--------|
| `app/scrapers/craigslist_scraper.py` | Playwright async scraper with rate limiting | Abstracted scraper interface supporting multiple sources | Refactor into `scrapers/base.py` + adapters |
| `services/lead_qualifier.py` | Rule-based scoring | Integrate website analysis factors, AI Council signals | Extend scoring schema, add weights |
| `services/auto_responder.py` | Template-based replies | Multi-model email generation, HITL queue | Add AI Council pipeline, connect to Gmail integration |
| `frontend/src/pages` | React/Vite dashboard | Next.js glassmorphism dashboard | Migrate to Next.js 14 app router, preserve component semantics |
| `ml/` (RL agent) | Q-learning for lead prioritization | Feed AI-GYM telemetry + conversation outcomes | Update state/action space, integrate with analytics |

### 3. Component Designs

#### 3.1 Scraping Platform
```
scrapers/
├── base.py              # AbstractScraper with async lifecycle hooks
├── craigslist.py        # Adapts current implementation
├── google_maps.py       # Places API + Playwright fallback
├── linkedin.py          # Piloterr/Selenium hybrid with proxy mgmt
└── job_boards.py        # Configurable HTML adapter
```
- `AbstractScraper` exposes `async def fetch_batch()`, `normalize_lead()`, `rate_limit_policy`.
- Each adapter registers via entry point; orchestrator loads active adapters from DB configuration.
- Output contract: normalized `LeadPayload` including metadata, raw HTML snapshot, enrichment status.

#### 3.2 AI Council Orchestrator
```
services/ai_council.py
- Model registry (Claude 4.5, GPT-4o, DeepSeek, Qwen, Gemini, Grok)
- Prompt templates per task (analysis, code, copywriting, reply, judge)
- Execution policy: parallel fan-out → synthesis model → scoring
```
- Each task defined in YAML: inputs, prompt, output schema, evaluation metrics.
- Claude 4.5 default judge; GPT-4o for code; Claude/Gemini for copy; DeepSeek for cost-saving alt.
- Log each call to `ai_gym_performance` with cost, latency, quality signals.

#### 3.3 Website Analysis Pipeline
1. `AnalyzerWorker` consumes `lead.scraped` event.
2. Fetch website via Playwright (headless Chromium in container).
3. Extract DOM, metadata, color palette, lighthouse metrics.
4. Fan-out prompts to AI Council; aggregate using Claude judge.
5. Persist `website_analyses` record with improvement plan JSON.
6. Emit `analysis.completed` event for downstream consumers.

Key Interfaces:
```python
class ImprovementPlan(BaseModel):
    lead_id: UUID
    overall_score: float
    top_improvements: List[ImprovementItem]
    technical_notes: Dict[str, Any]
    model_breakdown: Dict[str, ModelInsight]
```

#### 3.4 Demo Builder Service
- Worker receives `analysis.completed` event.
- Compose prompt with improvement plan, brand palette, tone guidelines.
- Generate 3 code variants (Claude Code, GPT-4o, DeepSeek Coder).
- Deploy via Vercel preview API; run automated checks (Playwright, Pa11y, Lighthouse).
- Score results; store best in `demo_sites` with QA report.
- If fail, fallback to Figma mock via v0.dev/bolt and mark status `mockup`.

#### 3.5 Video Automation
- Script generator invoked after demo success.
- Voiceover via ElevenLabs; caching per persona to reduce cost.
- Playwright automation script loads original + demo, executes timeline per segment.
- FFmpeg merges audio/video; upload to S3; record analytics hook.

#### 3.6 Email & Conversation Platform
- Email templates stored in DB with versioning, referencing improvement insights.
- Email send pipeline: segmentation → AI personalization → deliverability checks → Gmail API send → track pixel/click.
- Reply handler polls Gmail or uses Pub/Sub; classifies with AI Council; writes to `conversations` table; optionally queue for human review.

### 4. Data & Schema Extensions
- `demo_sites`: id, lead_id, model_used, url, qa_report, status.
- `videos`: id, lead_id, demo_id, video_url, duration, watch_stats.
- `email_sends`: campaign_id, lead_id, subject_variant, body, send_ts, open_ts, click_ts, reply_ts, status.
- `conversations`: thread metadata, sentiment, next_action.
- `ai_gym_performance`: task_type, model_name, cost, duration, quality_score, conversion_metric.
- `knowledge_base_entries`: text, embedding vector id, category, updated_at.

### 5. Workflow Orchestration
- Adopt n8n for high-level workflow definition; integrate with FastAPI through webhooks.
- Standard pipelines:
  - `Scrape -> Analyze -> Demo -> Video -> Email`
  - `Reply -> Analyze -> Respond -> Update CRM`
  - `Feedback -> AI-GYM Update -> Model Selection Adjust`
- Ensure idempotency via job IDs stored in Redis; repeated triggers check DB state before duplicate writes.

### 6. Security & Compliance Enhancements
- JWT auth with refresh tokens; role-based access (admin, ops, analyst).
- Rate limiting using SlowAPI or Kong gateway policies.
- PII encryption at rest for lead contact info (PG crypto extension).
- Consent tracking fields (`consent_source`, `consent_ts`) for GDPR compliance.
- Audit log service capturing mutating actions and AI-generated content lineage.

### 7. Deployment & Environments
- **Dev**: Docker Compose with local services, stubbed external APIs.
- **Staging**: Managed Postgres, Redis, ephemeral queue workers, limited API keys.
- **Prod**: Autoscaled ECS/K8s, dedicated VPC, NAT for scraping, secret rotation.
- Use GitHub Actions for CI (lint, tests, build images, run migrations).

### 8. Observability
- Structured logging (JSON) with correlation IDs (propagate through n8n).
- Metrics: per service + per model latency, success rate, cost.
- Traces: OpenTelemetry instrumentation across FastAPI, Celery/n8n tasks, AI calls.
- Alerts: email queue backlog, demo failures, deliverability drop, API error rates.

### 9. Rollout Phases
1. **Phase 0**: Harden legacy (auth, rate limit, tests, telemetry).
2. **Phase 1**: Release multi-source scraping + AI analysis behind feature flag.
3. **Phase 2**: Enable demo builder + email generation for closed beta.
4. **Phase 3**: Add video automation + conversation agent.
5. **Phase 4**: Activate AI-GYM optimization, analytics dashboards.

### 10. Dependencies & Risks
- Reliance on third-party APIs (Google Maps, LinkedIn) requiring proxy management.
- AI cost variance; need budget monitoring (AI-GYM cost ledger).
- Deliverability compliance (SPF/DKIM/DMARC) must be configured before large sends.
- Headless browser scaling: plan for Browserless/Satori cloud or Chromium fleet.

### 11. Approval & Updates
- System design reviewed by Tech Lead, Product, Security.
- Changes recorded as Design Change Requests (DCRs) appended to this document.

