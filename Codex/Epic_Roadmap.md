## Epic Roadmap – AI Outreach Transformation

### Overview
An eight-week execution plan (four sprint cycles) enabling a controlled pivot from the Craigslist-focused product to the AI-driven outreach platform. Each epic includes goals, deliverables, dependencies, team roles, and acceptance criteria.

### Sprint Cadence
- **Sprint Length**: 2 weeks
- **Teams**: Platform (backend/services), Experience (frontend/UX), Intelligence (AI/ML), Ops (DevOps & QA)
- **Ceremonies**: Architecture sync (weekly), AI Council calibration (bi-weekly), Go/No-Go gate at end of each sprint.

### Epic 0 – Baseline Hardening (Week 0)
- **Goal**: Ensure current system is production-safe before pivot.
- **Key Tasks**:
  1. Implement JWT auth & RBAC.
  2. Enforce rate limiting + request validation.
  3. Enable disabled routers (templates, notifications) or document removal.
  4. Establish CI pipeline (lint, tests, type check, docker build).
  5. Instrument logging/metrics baseline.
- **Deliverables**: Hardened API, security checklist, smoke test suite.
- **Exit Criteria**: All critical endpoints authenticated; automated test pass ≥ 90%; no Sev1 bugs.

### Epic 1 – Multi-Source Acquisition & AI Foundations (Weeks 1-2)
- **Goal**: Expand lead intake and prepare AI infrastructure.
- **Tasks**:
  - Build scraper abstraction + Google Maps adapter (Craigslist re-implemented via adapter).
  - Integrate OpenRouter; create AI Council base library with three models.
  - Extend DB schema (`scraping_jobs`, `scraped_data`, `ai_gym_performance`).
  - Update admin UI for source configuration.
  - Set up n8n and define initial `scrape -> queue` workflow.
- **Deliverables**: Google Maps leads in DB, AI Council smoke tests, schema migrations applied.
- **Exit Criteria**: ≥ 50 leads/day across two sources; AI calls recorded with metrics; ops docs updated.

### Epic 2 – Website Intelligence & Lead Enrichment (Weeks 3-4)
- **Goal**: Automate site analysis and feed intelligence into scoring.
- **Tasks**:
  - Implement Playwright-based analyzer + metadata extractor.
  - Define improvement plan schema; integrate AI Council analysis prompts.
  - Extend lead scoring service to ingest analysis metrics.
  - Build frontend view for analysis results (side-by-side comparison).
  - Add cache/invalidation and rate control for site crawls.
- **Deliverables**: Stored improvement plans, updated scoring, visual dashboards.
- **Exit Criteria**: 95% of analyzed leads have improvement plans; scoring accuracy validated via sample review; page load < 2s for analysis view.

### Epic 3 – Outreach Asset Generation (Weeks 5-6)
- **Goal**: Produce personalized demos, videos (optional), and emails.
- **Tasks**:
  - Demo builder service with Vercel deployments + QA automation.
  - Video automation MVP (script + voice + screen capture) or documented fallback.
  - Email personalization pipeline using AI Council + template mgmt.
  - Campaign scheduler UI with daily send distribution.
  - Deliverability setup (SPF, DKIM, DMARC, warm-up scheduler).
- **Deliverables**: Live demo URLs, video links, personalized emails ready to send.
- **Exit Criteria**: 10 lead pilot processed end-to-end; QA pass rate ≥ 85%; deliverability monitoring active.

### Epic 4 – Conversation Automation & Analytics (Weeks 7-8)
- **Goal**: Close the loop with reply handling and optimization insights.
- **Tasks**:
  - Conversation agent pipeline (reply detection, sentiment, AI responses, HITL queue).
  - Deploy AI-GYM dashboards with model leaderboards and cost tracking.
  - Implement campaign analytics (opens, clicks, replies, pipeline revenue).
  - Enable A/B testing manager for subject/body variants.
  - Harden logging, alerts, run load tests, finalize documentation.
- **Deliverables**: Conversation dashboard, AI-GYM reports, incident response playbooks.
- **Exit Criteria**: > 5 automated replies accepted in pilot; analytics dashboards functioning; load test at 2x expected volume passes.

### Post-Epic Backlog
- LinkedIn/Piloterr integration
- Multi-channel (SMS, LinkedIn messaging)
- Customer portal + billing hooks
- Marketplace for template sharing

### Dependencies & Milestones
| Milestone | Date | Dependency |
|-----------|------|------------|
| M0: Hardened Baseline | End Week 0 | Auth, rate limit, tests |
| M1: AI-ready Acquisition | End Week 2 | Scraper abstraction, OpenRouter integration |
| M2: Intelligence Online | End Week 4 | Improvement plans feeding scoring |
| M3: Outreach Pilot | End Week 6 | Demo/video/email assets deployed |
| M4: Closed-Loop Automation | End Week 8 | Conversation agent + analytics |

### Roles & RACI
| Role | Responsibilities | Epic Coverage |
|------|------------------|---------------|
| Tech Lead | Design approval, sequencing | All |
| Backend Eng | Scrapers, API, workers | Epics 1-4 |
| AI/ML Eng | AI Council, scoring, AI-GYM | Epics 1-4 |
| Frontend Eng | Dashboard, UX, approval UI | Epics 1-4 |
| DevOps | Infra, CI/CD, observability | All |
| Product | Requirements, acceptance, prioritization | All |
| Compliance | CAN-SPAM/GDPR review | Epics 3-4 |

### Risk Mitigation Gates
- AI spend > budget: trigger cost controls (model fallback) before Epic 3.
- Deliverability < 80% inbox placement: pause sends, run seed list diagnostics.
- Demo failure rate > 25%: revert to mockup fallback, schedule swarm to debug code-gen.
- Velocity slip > 1 sprint: re-baseline roadmaps with execs.

### Reporting
- Weekly status update referencing KPI dashboard (leads processed, analysis coverage, reply rate).
- End-of-epic demo to stakeholders with retro & Go/No-Go decision for next epic.

