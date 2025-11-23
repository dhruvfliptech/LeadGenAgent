## QA & Risk Plan – Pivot Assurance Framework

### 1. Objectives
- Guarantee quality and compliance throughout the pivot.
- Provide clear verification gates for each epic.
- Identify, track, and mitigate risks with ownership assignments.

### 2. Testing Strategy
| Layer | Approach | Tools |
|-------|----------|-------|
| Unit | 90% coverage on new modules (scrapers, AI council adapters, services) | pytest, pytest-asyncio |
| Integration | End-to-end workflows (scrape→analysis→email), external API stubs | Playwright, pytest, responses |
| Contract | OpenAPI schema validation, JSON schema for events | schemathesis, pydantic |
| UI | Component tests + visual regression | Testing Library, Cypress, Chromatic |
| Performance | Load (2x expected), stress, soak tests | Locust, k6 |
| Security | Static analysis, dependency scanning, auth/role tests | Bandit, Snyk, OWASP ZAP |

### 3. Environment Matrix
- **Local**: Docker Compose, mocked external APIs.
- **Dev**: Shared cluster, feature flags enabled, synthetic data.
- **Staging**: Near-prod parity, real integrations (sandbox API keys), nightly smoke tests.
- **Prod**: Blue/green deployments, feature flags controlled via LaunchDarkly (or custom).

### 4. Release Gates per Epic
- **Epic 0 Gate**: Auth tests passing, rate limit tests validated, basic pen test.
- **Epic 1 Gate**: Cross-source scraping intake QA (sample 50 leads), AI Council latency < 5s p95.
- **Epic 2 Gate**: Analysis accuracy review (human audit of 25 plans), scoring regression < ±5% difference.
- **Epic 3 Gate**: Demo QA (pass ≥ 85%), email deliverability seed test > 85% inbox.
- **Epic 4 Gate**: Conversation agent success (≥5 approved auto-replies), analytics accuracy (cross-check with manual calculations).

### 5. Risk Register
| Risk | Impact | Likelihood | Mitigation | Owner |
|------|--------|------------|------------|-------|
| API rate limits (Google/LinkedIn) | Medium | Medium | Rotate proxies, cache results, purchase API quotas | Platform Eng |
| AI cost overruns | High | Medium | Budget alerts, fallback models, throttle low-priority tasks | AI/ML Lead |
| Deliverability drop | High | Medium | Warm-up accounts, monitor inbox placement, use seed testing | Outreach Ops |
| Demo generator failures | Medium | Medium | Automated tests, fallback mockups, human QA queue | Frontend Guild |
| Compliance breach (GDPR/CAN-SPAM) | High | Low | Legal review, consent tracking, unsubscribe automation | Compliance Officer |
| Security incident | High | Low | Regular pen tests, patch cadence, secrets rotation | DevSecOps |
| Timeline slip | Medium | Medium | Buffer in roadmap, weekly risk review, re-prioritize scope | Product Lead |

### 6. Monitoring & Alerts
- **Metrics**: AI cost per lead, demo success rate, email bounce rate, API error rates, queue latency.
- **Alerts**: Slack + PagerDuty for Sev1 (API outage, deliverability < 70%), email for Sev2 (high latency, rising costs).
- **Dashboards**: Grafana boards for infrastructure, Metabase/Looker for business KPIs.

### 7. Incident Response
1. Trigger detection (alert, user report).
2. Declare severity, assemble response team (Tech + Product + Comms).
3. Mitigate (rollback feature flag, throttle jobs, switch models).
4. Root cause analysis within 48 hours.
5. Post-incident review logged with action items.

### 8. Documentation & Training
- QA runbooks stored in `docs/qa/` (to be created) with test plans per module.
- Risk register reviewed weekly during program sync.
- Onboarding checklists for new engineers covering auth, compliance, AI council usage.

### 9. Continuous Improvement
- After each epic, conduct quality retro: defect density, escaped bug count, test effectiveness.
- Update automation backlog with recurring manual tests.
- Maintain “quality debt” log to track deferred fixes.

