## Data & API Specification – Unified Contract

### 1. Purpose
Define the authoritative schema, migrations, and API contracts required for the pivot. Ensures all teams implement consistent data models and interfaces.

### 2. Database Migrations
- Use Alembic for PostgreSQL; versioned migrations stored in `backend/migrations/versions`.
- Introduce the following tables/columns (new or extended):

#### 2.1 Core Entities
```sql
CREATE TABLE demo_sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id),
    analysis_id UUID REFERENCES website_analyses(id),
    model_used VARCHAR(50),
    deployment_url TEXT,
    qa_report JSONB,
    status VARCHAR(20) DEFAULT 'building',
    created_at TIMESTAMP DEFAULT NOW(),
    deployed_at TIMESTAMP,
    archived_at TIMESTAMP
);

CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id),
    demo_site_id UUID REFERENCES demo_sites(id),
    script JSONB,
    video_url TEXT,
    duration_seconds INTEGER,
    watch_stats JSONB,
    status VARCHAR(20) DEFAULT 'generating',
    created_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE leads
    ADD COLUMN source_platform VARCHAR(50),
    ADD COLUMN consent_source VARCHAR(255),
    ADD COLUMN consent_timestamp TIMESTAMP;

ALTER TABLE website_analyses
    ADD COLUMN model_breakdown JSONB,
    ADD COLUMN lighthouse_report JSONB;
```

#### 2.2 Outreach Entities
```sql
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255),
    source_types VARCHAR[],
    filters JSONB,
    daily_limit INTEGER DEFAULT 100,
    send_window JSONB,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE email_sends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id),
    lead_id UUID REFERENCES leads(id),
    subject_variant TEXT,
    body TEXT,
    demo_url TEXT,
    video_url TEXT,
    model_used VARCHAR(50),
    tracking_token UUID,
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    replied_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'queued'
);

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id),
    campaign_id UUID REFERENCES campaigns(id),
    thread_metadata JSONB,
    last_message_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    direction VARCHAR(10),
    from_email VARCHAR(255),
    to_email VARCHAR(255),
    subject TEXT,
    body TEXT,
    model_used VARCHAR(50),
    sentiment VARCHAR(20),
    gmail_message_id VARCHAR(255),
    sent_at TIMESTAMP DEFAULT NOW()
);
```

#### 2.3 Analytics & AI-GYM
```sql
CREATE TABLE ai_gym_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_type VARCHAR(50),
    model_name VARCHAR(50),
    lead_id UUID REFERENCES leads(id),
    cost NUMERIC(10,4),
    duration_seconds INTEGER,
    quality_score INTEGER,
    conversion_metric NUMERIC(10,4),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ab_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255),
    element_type VARCHAR(50),
    variants JSONB,
    split_ratio JSONB,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3. API Endpoints

#### 3.1 Versioning Strategy
- Introduce `v2` endpoints for new modules while keeping `v1` for compatibility.
- REST with JSON responses; consider GraphQL read-only aggregator for analytics.

#### 3.2 Endpoint Summary
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/scraping/jobs` | POST/GET | Manage source-agnostic scraping jobs |
| `/api/v2/analysis/{lead_id}` | POST/GET | Trigger & fetch website analysis |
| `/api/v2/demos/{lead_id}` | POST/GET | Generate demo site, retrieve status |
| `/api/v2/videos/{lead_id}` | POST/GET | Generate video, retrieve status |
| `/api/v2/campaigns` | CRUD | Create/manage outreach campaigns |
| `/api/v2/email/send` | POST | Queue personalized emails |
| `/api/v2/conversations/{id}` | GET/POST | Retrieve thread, post AI-generated reply |
| `/api/v2/analytics/overview` | GET | Platform KPIs |
| `/api/v2/analytics/models` | GET | AI-GYM leaderboards |
| `/api/v2/ab-tests` | CRUD | Manage A/B experiments |

#### 3.3 Sample Contracts
```http
POST /api/v2/demos
{
  "lead_id": "uuid",
  "analysis_id": "uuid",
  "preferences": {
    "framework": "react",
    "fallback": "mockup"
  }
}

Response 202 Accepted
{
  "demo_id": "uuid",
  "status": "queued",
  "expected_ready_at": "2025-11-04T15:30:00Z"
}
```

```http
GET /api/v2/analytics/models?task_type=website_analysis&period=30d
Response 200
{
  "data": [
    {
      "model_name": "claude-4.5-sonnet",
      "avg_quality": 92.1,
      "avg_cost": 0.08,
      "conversion_rate": 0.085,
      "usage_count": 385
    }
  ],
  "meta": {"generated_at": "2025-11-04T12:00:00Z"}
}
```

### 4. Event Schema
- Use JSON schema stored under `events/` for validation.
- Core events: `lead.scraped`, `analysis.completed`, `demo.deployed`, `video.ready`, `email.sent`, `reply.received`, `abtest.decided`.
- Include correlation IDs and event versioning.

### 5. Compliance & Privacy
- Audit log table capturing user ID, action, resource, timestamp.
- GDPR requirements: right to delete – cascade delete lead data & associated assets while retaining anonymized metrics.
- Consent tracking: store `consent_source` and proof link.
- PII minimization in logs; use tokenization for email addresses in analytics.

### 6. Performance Considerations
- Indexes: `email_sends(lead_id)`, `ai_gym_performance(task_type, model_name)`, `conversations(lead_id)`.
- Partition heavy tables (email_sends, ai_gym_performance) by month for retention/purge policies.
- Use read replicas for analytics queries; avoid locking core transactional tables.

### 7. API Governance
- OpenAPI spec auto-generated via FastAPI; publish to Stoplight/SwaggerHub.
- Contract tests in CI to detect breaking changes.
- API version deprecation policy: 90-day sunset notice.

### 8. Data Retention Policy
- Leads & analyses: 18 months (extendable if active).
- Email/conversation logs: 24 months.
- AI prompts/responses hashes: 12 months for audit.
- Video/demo assets: 6 months, then archived to cold storage unless flagged as case study.

### 9. Reporting & Analytics
- Materialized views for key KPIs (reply rate, meeting booking rate, revenue per campaign).
- Use dbt or SQL scripts to transform raw data into dashboards.
- Expose aggregated analytics via `/analytics` endpoints, not raw PII.

### 10. Open Issues
- Decide on GraphQL adoption timeline.
- Confirm choice of vector DB and embedding dimensions.
- Determine encryption scope (column-level vs. TDE).

