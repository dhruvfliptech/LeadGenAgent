# Database Schema Validation Report

**Report Date:** 2025-11-05
**Working Directory:** `/Users/greenmachine2.0/Craigslist/backend`
**Database Administrator:** Database DBA Agent

---

## Executive Summary

This report validates the database models and schema for:
1. Auto-response models (AutoResponse, ResponseVariable)
2. Campaign metrics models (CampaignMetrics, CampaignMetricsSnapshot)
3. Workflow models conflict analysis (workflow_monitoring.py vs n8n_workflows.py)

### Overall Status: **NEEDS ATTENTION**

- **Base Import:** ✅ PASS - All models correctly use `app.models.base.Base`
- **Table Name Conflicts:** ⚠️ WARNING - Class name conflicts detected (different tables)
- **Foreign Key Relationships:** ✅ PASS - All foreign keys are valid
- **Migration Files:** ❌ FAIL - Missing migrations for new models

---

## 1. Auto-Response Models Validation

### File: `/Users/greenmachine2.0/Craigslist/backend/app/models/auto_response.py`

#### AutoResponse Model
- **Table Name:** `auto_responses`
- **Base Import:** ✅ Correct - `from app.models.base import Base`
- **Primary Key:** `id` (Integer)
- **Foreign Keys:**
  - ✅ `lead_id` → `leads.id` (VALID)
  - ✅ `template_id` → `response_templates.id` (VALID)

**Schema Structure:**
```python
- Core Fields: id, lead_id, template_id, subject, body
- Personalization: personalization_data (JSON), variables_used (JSON)
- Scheduling: delay_minutes, scheduled_at, sent_at
- Delivery Status: status, delivery_status, error_message, retry_count
- Engagement Tracking: email_opened, opened_at, open_count, email_clicked, clicked_at, click_count
- Response Tracking: lead_responded, responded_at, response_content
- A/B Testing: variant_id
- AI Enhancement: ai_enhanced, ai_model_used, ai_enhancement_cost
- Email Headers: message_id, from_address, to_address, cc_addresses, bcc_addresses
- Tracking Tokens: tracking_token, unsubscribe_token
- Metrics: send_duration_ms, quality_score
- Timestamps: created_at, updated_at
```

**Indexes:**
- ✅ `idx_auto_response_lead_template` on (lead_id, template_id)
- ✅ `idx_auto_response_status_scheduled` on (status, scheduled_at)
- ✅ `idx_auto_response_engagement` on (email_opened, email_clicked, lead_responded)
- ✅ `idx_auto_response_variant` on (variant_id, status)

**Relationships:**
- ✅ `lead` relationship to Lead model (backref: auto_responses)
- ✅ `template` relationship to ResponseTemplate model (backref: auto_responses)

**Status:** ✅ **PASS** - Model structure is valid

---

#### ResponseVariable Model
- **Table Name:** `response_variables`
- **Base Import:** ✅ Correct - `from app.models.base import Base`
- **Primary Key:** `id` (Integer)
- **Foreign Keys:** None

**Schema Structure:**
```python
- Definition: name (UNIQUE), display_name, description
- Type Info: variable_type, format_hint
- Defaults: default_value, fallback_value
- Extraction: source_field, source_path, extraction_function
- Validation: required, validation_regex, min_length, max_length
- Transformation: transform, truncate_at, sanitize_html
- Usage Tracking: usage_count, last_used_at
- Categorization: category, is_system, is_active
- Examples: example_value
- Metadata: variable_metadata (JSON)
- Timestamps: created_at, updated_at
```

**Indexes:**
- ✅ `idx_variable_category_active` on (category, is_active)

**Status:** ✅ **PASS** - Model structure is valid

---

## 2. Campaign Metrics Models Validation

### File: `/Users/greenmachine2.0/Craigslist/backend/app/models/campaign_metrics.py`

#### CampaignMetrics Model
- **Table Name:** `campaign_metrics`
- **Base Import:** ✅ Correct - `from app.models.base import Base`
- **Primary Key:** `id` (Integer)
- **Foreign Keys:**
  - ✅ `campaign_id` → `campaigns.id` (UNIQUE, VALID)

**Schema Structure:**
```python
- Send Metrics: total_recipients, total_sent, total_queued, total_sending, total_failed
- Delivery Metrics: total_delivered, total_bounced, total_rejected, hard_bounces, soft_bounces
- Engagement Metrics: total_opened, unique_opens, total_clicked, unique_clicks, total_replied,
                     total_unsubscribed, total_spam_reports
- Conversion Metrics: total_conversions, conversion_value, total_revenue
- Calculated Rates: delivery_rate, bounce_rate, open_rate, click_rate, click_to_open_rate,
                   reply_rate, unsubscribe_rate, spam_rate, conversion_rate
- Time Metrics: first_open_at, last_open_at, first_click_at, last_click_at,
               average_time_to_open, average_time_to_click
- Cost/ROI Metrics: total_cost, cost_per_send, cost_per_open, cost_per_click,
                   cost_per_conversion, roi
- Quality Scores: sender_reputation_score, content_quality_score, engagement_quality_score
- A/B Testing: is_test_campaign, test_group, statistical_significance
- Timestamps: metrics_started_at, metrics_updated_at, last_activity_at
```

**Indexes:**
- ✅ `idx_metrics_rates` on (delivery_rate, open_rate, click_rate)
- ✅ `idx_metrics_roi` on (roi, conversion_rate)

**Relationships:**
- ✅ `campaign` relationship to Campaign model (backref: metrics)

**Methods:**
- ✅ `calculate_rates()` - Recalculates all percentage metrics
- ✅ `is_high_performing` property - Benchmark checking
- ✅ `needs_attention` property - Alert threshold checking
- ✅ `to_dict()` - API serialization

**Status:** ✅ **PASS** - Model structure is valid

---

#### CampaignMetricsSnapshot Model
- **Table Name:** `campaign_metrics_snapshots`
- **Base Import:** ✅ Correct - `from app.models.base import Base`
- **Primary Key:** `id` (Integer)
- **Foreign Keys:**
  - ✅ `campaign_id` → `campaigns.id` (VALID)
  - ✅ `metrics_id` → `campaign_metrics.id` (VALID)

**Schema Structure:**
```python
- References: campaign_id, metrics_id
- Snapshot Timing: snapshot_at, snapshot_type (auto, manual, hourly, daily)
- Snapshot Data: total_sent, total_delivered, unique_opens, unique_clicks,
                open_rate, click_rate, total_conversions, conversion_rate
```

**Indexes:**
- ✅ `idx_snapshot_campaign_time` on (campaign_id, snapshot_at)

**Relationships:**
- ✅ `campaign` relationship to Campaign model (backref: metrics_snapshots)

**Status:** ✅ **PASS** - Model structure is valid

---

## 3. Workflow Models Conflict Analysis

### ⚠️ CRITICAL ISSUE: Duplicate Class Names with Different Tables

#### Conflict 1: WorkflowExecution Class

**File 1:** `/Users/greenmachine2.0/Craigslist/backend/app/models/workflow_monitoring.py`
```python
class WorkflowExecution(Base):
    __tablename__ = "workflow_execution_monitoring"
```

**File 2:** `/Users/greenmachine2.0/Craigslist/backend/app/models/n8n_workflows.py`
```python
class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"
```

**Analysis:**
- ⚠️ Same class name: `WorkflowExecution`
- ✅ Different table names: `workflow_execution_monitoring` vs `workflow_executions`
- ⚠️ Both imported in `__init__.py` - POTENTIAL CONFLICT
- ⚠️ Last import wins: `n8n_workflows.WorkflowExecution` will override

**Current Import in __init__.py:**
```python
# Line 34-37
from .n8n_workflows import (
    N8NWorkflow, WorkflowExecution, WorkflowApproval, WebhookQueue, WorkflowMonitoring,
    WorkflowStatus, ApprovalStatus, ApprovalPriority, QueueStatus, MonitoringSeverity
)
```

**Impact:**
- `workflow_monitoring.WorkflowExecution` is **NOT imported** - ✅ No runtime conflict
- Only `n8n_workflows.WorkflowExecution` is exposed
- `workflow_execution_monitoring` table exists but model is not accessible via imports

---

#### Conflict 2: WorkflowApproval Class

**File 1:** `/Users/greenmachine2.0/Craigslist/backend/app/models/workflow_monitoring.py`
```python
class WorkflowApproval(Base):
    __tablename__ = "legacy_workflow_approvals"
```

**File 2:** `/Users/greenmachine2.0/Craigslist/backend/app/models/n8n_workflows.py`
```python
class WorkflowApproval(Base):
    __tablename__ = "workflow_approvals"
```

**Analysis:**
- ⚠️ Same class name: `WorkflowApproval`
- ✅ Different table names: `legacy_workflow_approvals` vs `workflow_approvals`
- ⚠️ Both could conflict if imported together
- ✅ Only `n8n_workflows.WorkflowApproval` is imported in `__init__.py`
- ✅ `legacy_workflow_approvals` naming indicates intentional deprecation

**Impact:**
- `workflow_monitoring.WorkflowApproval` is **NOT imported** - ✅ No runtime conflict
- Legacy table `legacy_workflow_approvals` exists but model is not accessible
- This appears to be intentional migration from old to new system

---

### Table Name Uniqueness Check

All table names are UNIQUE across the codebase:

```
workflow_execution_monitoring    (workflow_monitoring.py - NOT IMPORTED)
workflow_executions              (n8n_workflows.py - IMPORTED)
legacy_workflow_approvals        (workflow_monitoring.py - NOT IMPORTED)
workflow_approvals               (n8n_workflows.py - IMPORTED)
workflow_metrics                 (workflow_monitoring.py - NOT IMPORTED)
workflow_alerts                  (workflow_monitoring.py - NOT IMPORTED)
ab_test_results                  (workflow_monitoring.py - NOT IMPORTED)
workflow_reports                 (workflow_monitoring.py - NOT IMPORTED)
n8n_workflows                    (n8n_workflows.py - IMPORTED)
n8n_webhook_queue                (n8n_workflows.py - IMPORTED as WebhookQueue)
workflow_monitoring              (n8n_workflows.py - IMPORTED)
```

**Status:** ⚠️ **WARNING** - Class name conflicts exist but are mitigated by selective imports

---

## 4. Foreign Key Relationship Validation

### AutoResponse Foreign Keys
✅ `lead_id` → `leads.id`
- Target table exists: YES
- Target model: `Lead` in `app/models/leads.py`
- Relationship configured: YES (backref: auto_responses)

✅ `template_id` → `response_templates.id`
- Target table exists: YES
- Target model: `ResponseTemplate` in `app/models/response_templates.py`
- Relationship configured: YES (backref: auto_responses)

### CampaignMetrics Foreign Keys
✅ `campaign_id` → `campaigns.id`
- Target table exists: YES
- Target model: `Campaign` in `app/models/campaigns.py`
- Relationship configured: YES (backref: metrics)
- Constraint: UNIQUE (one-to-one relationship)

### CampaignMetricsSnapshot Foreign Keys
✅ `campaign_id` → `campaigns.id`
- Target table exists: YES
- Relationship configured: YES (backref: metrics_snapshots)

✅ `metrics_id` → `campaign_metrics.id`
- Target table exists: YES (will exist after migration)
- Relationship: Not explicitly defined (can be added if needed)

**Status:** ✅ **PASS** - All foreign key relationships are valid

---

## 5. Migration Files Analysis

### Existing Migrations

#### Migration 007: Response Templates
- **File:** `007_response_templates.py`
- **Creates Table:** `response_templates`
- **Status:** ✅ EXISTS

**Schema Mismatch:**
The migration creates different columns than the current model:
- Migration has: `subject`, `body`, `template_type`, `communication_method`, `required_variables`, `optional_variables`
- Model has: `subject_template`, `body_template`, `category`, `variables` (with properties for backward compatibility)

⚠️ **Schema drift detected** - Model has evolved beyond migration

#### Migration 021: Campaign Management Tables
- **File:** `021_create_campaign_management_tables.py`
- **Creates Tables:** `campaigns`, `campaign_recipients`, `email_tracking`
- **Status:** ✅ EXISTS

**Does NOT create:**
- `campaign_metrics` table
- `campaign_metrics_snapshots` table

#### Migration 022: N8N Workflow System
- **File:** `022_create_n8n_workflow_system.py`
- **Creates Tables:**
  - `n8n_workflows`
  - `workflow_executions`
  - `workflow_approvals`
  - `n8n_webhook_queue` (model calls it `webhook_queue`)
  - `workflow_monitoring`
- **Status:** ✅ EXISTS

**Does NOT create:**
- `workflow_execution_monitoring` table
- `legacy_workflow_approvals` table
- `workflow_metrics` table
- `workflow_alerts` table
- `ab_test_results` table
- `workflow_reports` table

### ❌ Missing Migrations

#### 1. Auto-Response Tables
**Missing Migration:** `auto_responses` and `response_variables` tables

**Required Migration Actions:**
```sql
CREATE TABLE auto_responses (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id),
    template_id INTEGER REFERENCES response_templates(id),
    -- ... (all columns from AutoResponse model)
);

CREATE TABLE response_variables (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    -- ... (all columns from ResponseVariable model)
);
```

#### 2. Campaign Metrics Tables
**Missing Migration:** `campaign_metrics` and `campaign_metrics_snapshots` tables

**Required Migration Actions:**
```sql
CREATE TABLE campaign_metrics (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER UNIQUE REFERENCES campaigns(id),
    -- ... (all columns from CampaignMetrics model)
);

CREATE TABLE campaign_metrics_snapshots (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id),
    metrics_id INTEGER REFERENCES campaign_metrics(id),
    -- ... (all columns from CampaignMetricsSnapshot model)
);
```

#### 3. Legacy Workflow Monitoring Tables
**Missing Migration:** Tables from `workflow_monitoring.py` that are not in migration 022

**Note:** These tables appear to be legacy/deprecated since the models are not imported. However, if historical data exists or if there's a migration path needed, migrations should be created.

**Status:** ❌ **FAIL** - Critical migrations are missing

---

## 6. Recommendations

### CRITICAL (P0) - Must Address Immediately

1. **Create Missing Migration: Auto-Response Tables**
   - File: `023_create_auto_response_tables.py`
   - Tables: `auto_responses`, `response_variables`
   - Estimated Time: 30 minutes

2. **Create Missing Migration: Campaign Metrics Tables**
   - File: `024_create_campaign_metrics_tables.py`
   - Tables: `campaign_metrics`, `campaign_metrics_snapshots`
   - Estimated Time: 30 minutes

3. **Fix Response Template Schema Drift**
   - File: `025_update_response_templates_schema.py`
   - Action: Migrate old columns to new schema or add compatibility
   - Estimated Time: 45 minutes

### HIGH (P1) - Should Address Soon

4. **Clarify Workflow Model Strategy**
   - Decision needed: Are `workflow_monitoring.py` models deprecated?
   - If YES: Remove file or mark as deprecated
   - If NO: Rename classes to avoid confusion (e.g., `LegacyWorkflowExecution`)
   - Estimated Time: 1 hour

5. **Add Database Migration Testing**
   - Create test script to validate all migrations
   - Test upgrade and downgrade paths
   - Estimated Time: 2 hours

6. **Add Model Registry Validation**
   - Create script to detect class name conflicts
   - Add to CI/CD pipeline
   - Estimated Time: 1 hour

### MEDIUM (P2) - Nice to Have

7. **Add Relationship Validation Tests**
   - Test all foreign key relationships
   - Verify cascade behaviors
   - Estimated Time: 2 hours

8. **Document Migration Strategy**
   - Create migration naming convention
   - Document rollback procedures
   - Estimated Time: 1 hour

9. **Add Index Performance Analysis**
   - Review query patterns
   - Optimize indexes based on actual usage
   - Estimated Time: 3 hours

---

## 7. Migration Creation Scripts

### Migration 023: Auto-Response Tables

**File:** `/Users/greenmachine2.0/Craigslist/backend/migrations/versions/023_create_auto_response_tables.py`

```python
"""Create auto-response tables for template-based responses

Revision ID: 023
Revises: 022
Create Date: 2025-11-05

Creates:
- auto_responses: Generated responses with delivery tracking
- response_variables: Template variable definitions
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision = '023'
down_revision = '022'

def upgrade():
    # Create auto_responses table
    op.create_table(
        'auto_responses',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('lead_id', sa.Integer(), sa.ForeignKey('leads.id'), nullable=False, index=True),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('response_templates.id'), nullable=False, index=True),
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('personalization_data', JSON, default={}),
        sa.Column('variables_used', JSON, default=[]),
        sa.Column('delay_minutes', sa.Integer(), default=0),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True, index=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True, index=True),
        sa.Column('status', sa.String(50), default='pending', index=True),
        sa.Column('delivery_status', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('email_opened', sa.Boolean(), default=False),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('open_count', sa.Integer(), default=0),
        sa.Column('email_clicked', sa.Boolean(), default=False),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('click_count', sa.Integer(), default=0),
        sa.Column('lead_responded', sa.Boolean(), default=False),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.Column('response_content', sa.Text(), nullable=True),
        sa.Column('variant_id', sa.String(100), nullable=True, index=True),
        sa.Column('ai_enhanced', sa.Boolean(), default=False),
        sa.Column('ai_model_used', sa.String(100), nullable=True),
        sa.Column('ai_enhancement_cost', sa.Float(), nullable=True),
        sa.Column('message_id', sa.String(255), unique=True, index=True),
        sa.Column('from_address', sa.String(255)),
        sa.Column('to_address', sa.String(255)),
        sa.Column('cc_addresses', JSON, default=[]),
        sa.Column('bcc_addresses', JSON, default=[]),
        sa.Column('tracking_token', sa.String(255), unique=True, index=True),
        sa.Column('unsubscribe_token', sa.String(255), unique=True, index=True),
        sa.Column('send_duration_ms', sa.Integer(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create indexes
    op.create_index('idx_auto_response_lead_template', 'auto_responses', ['lead_id', 'template_id'])
    op.create_index('idx_auto_response_status_scheduled', 'auto_responses', ['status', 'scheduled_at'])
    op.create_index('idx_auto_response_engagement', 'auto_responses', ['email_opened', 'email_clicked', 'lead_responded'])
    op.create_index('idx_auto_response_variant', 'auto_responses', ['variant_id', 'status'])

    # Create response_variables table
    op.create_table(
        'response_variables',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('variable_type', sa.String(50), default='text', nullable=False),
        sa.Column('format_hint', sa.String(100), nullable=True),
        sa.Column('default_value', sa.Text(), nullable=True),
        sa.Column('fallback_value', sa.Text(), nullable=True),
        sa.Column('source_field', sa.String(100), nullable=True),
        sa.Column('source_path', sa.String(255), nullable=True),
        sa.Column('extraction_function', sa.String(100), nullable=True),
        sa.Column('required', sa.Boolean(), default=False),
        sa.Column('validation_regex', sa.String(500), nullable=True),
        sa.Column('min_length', sa.Integer(), nullable=True),
        sa.Column('max_length', sa.Integer(), nullable=True),
        sa.Column('transform', sa.String(50), nullable=True),
        sa.Column('truncate_at', sa.Integer(), nullable=True),
        sa.Column('sanitize_html', sa.Boolean(), default=True),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('category', sa.String(100), default='general', index=True),
        sa.Column('is_system', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True, index=True),
        sa.Column('example_value', sa.String(500), nullable=True),
        sa.Column('variable_metadata', JSON, default={}),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create indexes
    op.create_index('idx_variable_category_active', 'response_variables', ['category', 'is_active'])

def downgrade():
    op.drop_table('response_variables')
    op.drop_table('auto_responses')
```

### Migration 024: Campaign Metrics Tables

**File:** `/Users/greenmachine2.0/Craigslist/backend/migrations/versions/024_create_campaign_metrics_tables.py`

```python
"""Create campaign metrics tables for performance tracking

Revision ID: 024
Revises: 023
Create Date: 2025-11-05

Creates:
- campaign_metrics: Aggregated campaign performance statistics
- campaign_metrics_snapshots: Point-in-time metric snapshots
"""

from alembic import op
import sqlalchemy as sa

revision = '024'
down_revision = '023'

def upgrade():
    # Create campaign_metrics table
    op.create_table(
        'campaign_metrics',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id'), unique=True, nullable=False, index=True),

        # Send metrics
        sa.Column('total_recipients', sa.Integer(), default=0),
        sa.Column('total_sent', sa.Integer(), default=0),
        sa.Column('total_queued', sa.Integer(), default=0),
        sa.Column('total_sending', sa.Integer(), default=0),
        sa.Column('total_failed', sa.Integer(), default=0),

        # Delivery metrics
        sa.Column('total_delivered', sa.Integer(), default=0),
        sa.Column('total_bounced', sa.Integer(), default=0),
        sa.Column('total_rejected', sa.Integer(), default=0),
        sa.Column('hard_bounces', sa.Integer(), default=0),
        sa.Column('soft_bounces', sa.Integer(), default=0),

        # Engagement metrics
        sa.Column('total_opened', sa.Integer(), default=0),
        sa.Column('unique_opens', sa.Integer(), default=0),
        sa.Column('total_clicked', sa.Integer(), default=0),
        sa.Column('unique_clicks', sa.Integer(), default=0),
        sa.Column('total_replied', sa.Integer(), default=0),
        sa.Column('total_unsubscribed', sa.Integer(), default=0),
        sa.Column('total_spam_reports', sa.Integer(), default=0),

        # Conversion metrics
        sa.Column('total_conversions', sa.Integer(), default=0),
        sa.Column('conversion_value', sa.Float(), default=0.0),
        sa.Column('total_revenue', sa.Float(), default=0.0),

        # Calculated rates
        sa.Column('delivery_rate', sa.Float(), default=0.0),
        sa.Column('bounce_rate', sa.Float(), default=0.0),
        sa.Column('open_rate', sa.Float(), default=0.0),
        sa.Column('click_rate', sa.Float(), default=0.0),
        sa.Column('click_to_open_rate', sa.Float(), default=0.0),
        sa.Column('reply_rate', sa.Float(), default=0.0),
        sa.Column('unsubscribe_rate', sa.Float(), default=0.0),
        sa.Column('spam_rate', sa.Float(), default=0.0),
        sa.Column('conversion_rate', sa.Float(), default=0.0),

        # Time-based metrics
        sa.Column('first_open_at', sa.DateTime(), nullable=True),
        sa.Column('last_open_at', sa.DateTime(), nullable=True),
        sa.Column('first_click_at', sa.DateTime(), nullable=True),
        sa.Column('last_click_at', sa.DateTime(), nullable=True),
        sa.Column('average_time_to_open', sa.Integer(), nullable=True),
        sa.Column('average_time_to_click', sa.Integer(), nullable=True),

        # Cost and ROI
        sa.Column('total_cost', sa.Float(), default=0.0),
        sa.Column('cost_per_send', sa.Float(), default=0.0),
        sa.Column('cost_per_open', sa.Float(), default=0.0),
        sa.Column('cost_per_click', sa.Float(), default=0.0),
        sa.Column('cost_per_conversion', sa.Float(), default=0.0),
        sa.Column('roi', sa.Float(), default=0.0),

        # Quality scores
        sa.Column('sender_reputation_score', sa.Float(), nullable=True),
        sa.Column('content_quality_score', sa.Float(), nullable=True),
        sa.Column('engagement_quality_score', sa.Float(), nullable=True),

        # A/B Testing
        sa.Column('is_test_campaign', sa.Boolean(), default=False),
        sa.Column('test_group', sa.String(50), nullable=True),
        sa.Column('statistical_significance', sa.Float(), nullable=True),

        # Timestamps
        sa.Column('metrics_started_at', sa.DateTime(), nullable=True),
        sa.Column('metrics_updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_activity_at', sa.DateTime(), nullable=True),
    )

    # Create indexes
    op.create_index('idx_metrics_rates', 'campaign_metrics', ['delivery_rate', 'open_rate', 'click_rate'])
    op.create_index('idx_metrics_roi', 'campaign_metrics', ['roi', 'conversion_rate'])

    # Create campaign_metrics_snapshots table
    op.create_table(
        'campaign_metrics_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('campaign_id', sa.Integer(), sa.ForeignKey('campaigns.id'), nullable=False, index=True),
        sa.Column('metrics_id', sa.Integer(), sa.ForeignKey('campaign_metrics.id'), nullable=False, index=True),
        sa.Column('snapshot_at', sa.DateTime(), default=sa.func.now(), nullable=False, index=True),
        sa.Column('snapshot_type', sa.String(50), default='auto', index=True),

        # Snapshot data
        sa.Column('total_sent', sa.Integer(), default=0),
        sa.Column('total_delivered', sa.Integer(), default=0),
        sa.Column('unique_opens', sa.Integer(), default=0),
        sa.Column('unique_clicks', sa.Integer(), default=0),
        sa.Column('open_rate', sa.Float(), default=0.0),
        sa.Column('click_rate', sa.Float(), default=0.0),
        sa.Column('total_conversions', sa.Integer(), default=0),
        sa.Column('conversion_rate', sa.Float(), default=0.0),
    )

    # Create indexes
    op.create_index('idx_snapshot_campaign_time', 'campaign_metrics_snapshots', ['campaign_id', 'snapshot_at'])

def downgrade():
    op.drop_table('campaign_metrics_snapshots')
    op.drop_table('campaign_metrics')
```

---

## 8. Backup and Recovery Considerations

### Pre-Migration Backup Strategy

Before running migrations 023 and 024:

1. **Full Database Backup**
   ```bash
   pg_dump -h localhost -U postgres -d craigslist_db -F c -f backup_pre_migration_023_024.dump
   ```

2. **Schema-Only Backup**
   ```bash
   pg_dump -h localhost -U postgres -d craigslist_db -s -f backup_schema_pre_migration.sql
   ```

3. **Test Migration on Development Copy**
   ```bash
   # Create test database
   createdb -U postgres craigslist_test
   pg_restore -h localhost -U postgres -d craigslist_test backup_pre_migration_023_024.dump

   # Test migrations
   cd /Users/greenmachine2.0/Craigslist/backend
   alembic upgrade head
   ```

### Recovery Plan (RTO/RPO)

- **RTO (Recovery Time Objective):** 15 minutes
- **RPO (Recovery Point Objective):** 0 data loss (pre-migration backup)

**Rollback Procedure:**
```bash
# If migrations fail, rollback to previous version
alembic downgrade 022

# If catastrophic failure, restore from backup
pg_restore -h localhost -U postgres -d craigslist_db -c backup_pre_migration_023_024.dump
```

---

## 9. Performance Monitoring

### Key Metrics to Monitor

After applying migrations:

1. **Table Sizes**
   ```sql
   SELECT
       schemaname,
       tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
   FROM pg_tables
   WHERE tablename IN ('auto_responses', 'response_variables', 'campaign_metrics', 'campaign_metrics_snapshots')
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
   ```

2. **Index Usage**
   ```sql
   SELECT
       schemaname,
       tablename,
       indexname,
       idx_scan,
       idx_tup_read,
       idx_tup_fetch
   FROM pg_stat_user_indexes
   WHERE tablename IN ('auto_responses', 'response_variables', 'campaign_metrics', 'campaign_metrics_snapshots')
   ORDER BY idx_scan DESC;
   ```

3. **Query Performance**
   ```sql
   -- Monitor slow queries on new tables
   SELECT query, mean_exec_time, calls
   FROM pg_stat_statements
   WHERE query LIKE '%auto_responses%'
      OR query LIKE '%campaign_metrics%'
   ORDER BY mean_exec_time DESC
   LIMIT 10;
   ```

---

## 10. Conclusion

### Summary of Findings

1. ✅ **Base Imports:** All models correctly use `app.models.base.Base`
2. ⚠️ **Class Name Conflicts:** WorkflowExecution and WorkflowApproval classes are duplicated but mitigated through selective imports
3. ✅ **Foreign Key Relationships:** All relationships are valid and properly configured
4. ❌ **Migration Files:** Critical migrations are missing for auto_responses and campaign_metrics tables

### Critical Actions Required

1. Create migration 023_create_auto_response_tables.py
2. Create migration 024_create_campaign_metrics_tables.py
3. Test migrations in development environment
4. Apply migrations to production with full backup

### Estimated Time to Resolution

- Migration creation: 1 hour
- Testing: 1 hour
- Backup and deployment: 30 minutes
- **Total: 2.5 hours**

### Risk Assessment

- **Risk Level:** MEDIUM
- **Impact if not addressed:** Auto-response and campaign metrics features will fail at runtime
- **Mitigation:** Migrations provided in this report are ready for implementation

---

**Report Generated By:** Database DBA Agent
**Report Version:** 1.0
**Next Review Date:** After migration deployment

---
