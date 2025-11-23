## N8N Workflow Automation Guide
# Phase 6: N8N Workflow Automation System

Complete guide for the N8N workflow automation integration system for the Craigslist Lead Generation Platform.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup & Configuration](#setup--configuration)
4. [Core Features](#core-features)
5. [API Reference](#api-reference)
6. [Workflow Templates](#workflow-templates)
7. [Approval System](#approval-system)
8. [Monitoring & Debugging](#monitoring--debugging)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The N8N Workflow Automation system provides a comprehensive integration between the lead generation platform and N8N for orchestrating complex multi-step workflows.

### Key Features

- **Webhook System**: Receive and process webhooks from N8N workflows
- **Workflow Management**: Create, update, and manage workflow configurations
- **Approval Gates**: Manual and AI-powered automatic approvals for sensitive actions
- **Error Handling**: Robust retry logic and error tracking
- **Monitoring**: Real-time event logging and performance metrics
- **Background Processing**: Celery-based async workflow execution

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     N8N WORKFLOW SYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Webhook    │───▶│  Webhook     │───▶│   Workflow   │  │
│  │   Receiver   │    │   Queue      │    │   Executor   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                    │                    │         │
│         ▼                    ▼                    ▼         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Workflow Monitoring & Logging             │  │
│  └──────────────────────────────────────────────────────┘  │
│         │                                         │         │
│         ▼                                         ▼         │
│  ┌──────────────┐                         ┌──────────────┐ │
│  │   Approval   │                         │     N8N      │ │
│  │   System     │                         │   Client     │ │
│  └──────────────┘                         └──────────────┘ │
│         │                                         │         │
│         ▼                                         ▼         │
│  ┌──────────────┐                         ┌──────────────┐ │
│  │Auto-Approval │                         │  N8N Cloud/  │ │
│  │  (AI-based)  │                         │  Self-hosted │ │
│  └──────────────┘                         └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture

### Database Schema

The system uses 5 core tables:

**1. n8n_workflows**
```sql
- id: Primary key
- workflow_name: Unique workflow name
- n8n_workflow_id: N8N workflow ID
- webhook_url: Webhook URL for triggering
- trigger_events: JSON array of trigger events
- is_active: Active status
- requires_approval: Approval requirement flag
- auto_approval_enabled: Auto-approval flag
- execution_count, success_count, failure_count: Statistics
```

**2. workflow_executions**
```sql
- id: Primary key
- workflow_id: Foreign key to n8n_workflows
- n8n_execution_id: N8N execution ID
- status: pending|running|completed|failed|cancelled
- input_data, output_data: JSON data
- duration_seconds: Execution duration
- error_message: Error details if failed
```

**3. workflow_approvals**
```sql
- id: Primary key
- execution_id: Foreign key to workflow_executions
- approval_type: Type of approval (email_send, video_create, etc.)
- status: pending|approved|rejected|expired
- priority: high|medium|low
- auto_approval_confidence: AI confidence score (0-100)
- expires_at: Expiration timestamp
```

**4. webhook_queue**
```sql
- id: Primary key
- workflow_id: Optional foreign key
- webhook_payload: JSON payload
- status: queued|processing|completed|failed
- retry_count: Number of retries
- next_retry_at: Next retry timestamp
```

**5. workflow_monitoring**
```sql
- id: Primary key
- workflow_id, execution_id: Foreign keys
- event_type: Event type (started, completed, error, etc.)
- severity: info|warning|error|critical
- event_data: JSON event data
- timestamp: Event timestamp
```

### Service Architecture

**Services** (`backend/app/services/workflows/`):

- **n8n_client.py**: N8N API client for triggering workflows
- **webhook_handler.py**: Webhook queue management
- **workflow_executor.py**: Workflow execution lifecycle
- **approval_system.py**: Approval request management
- **auto_approval.py**: AI-powered automatic approval
- **workflow_monitor.py**: Event logging and monitoring

---

## Setup & Configuration

### 1. Environment Variables

Add to `.env`:

```bash
# N8N Integration
N8N_API_URL=https://your-n8n-instance.com/api/v1
N8N_API_KEY=your_api_key_here
N8N_WEBHOOK_SECRET=your_webhook_secret

# Workflow Settings
WORKFLOW_MAX_RETRIES=3
WORKFLOW_RETRY_DELAY_SECONDS=60
WORKFLOW_EXECUTION_TIMEOUT_SECONDS=300
WORKFLOW_APPROVAL_TIMEOUT_HOURS=24

# Auto-Approval Settings
AUTO_APPROVAL_ENABLED=true
AUTO_APPROVAL_CONFIDENCE_THRESHOLD=90
AUTO_APPROVAL_MAX_DAILY_LIMIT=100
```

### 2. Database Migration

Run the migration to create tables:

```bash
cd backend
alembic upgrade head
```

### 3. Start Background Workers

Start Celery workers for async processing:

```bash
# Start worker
celery -A celery_app worker --loglevel=info

# Start beat scheduler (for periodic tasks)
celery -A celery_app beat --loglevel=info
```

### 4. Configure N8N

In your N8N instance, configure webhooks to point to:

```
https://your-backend.com/api/v1/webhooks/n8n/{workflow_id}
```

Add webhook secret to N8N workflow:
- Header: `X-N8N-Signature`
- Value: Your webhook secret

---

## Core Features

### 1. Workflow Management

**Create Workflow**:
```python
from backend.app.schemas.workflows import N8NWorkflowCreate

workflow_data = N8NWorkflowCreate(
    workflow_name="Lead Processing",
    workflow_description="Process new leads",
    n8n_workflow_id="wf-123abc",
    trigger_events=["lead_created"],
    is_active=True,
    requires_approval=True,
    auto_approval_enabled=True
)

# POST /api/v1/workflows
```

**Trigger Workflow**:
```python
from backend.app.schemas.workflows import WorkflowTrigger

trigger = WorkflowTrigger(
    trigger_event="lead_created",
    input_data={"lead_id": 123, "score": 85},
    trigger_source="api"
)

# POST /api/v1/workflows/{workflow_id}/trigger
```

### 2. Webhook Processing

Webhooks are automatically queued and processed asynchronously:

```python
# N8N sends webhook to:
# POST /api/v1/webhooks/n8n/{workflow_id}

# Webhook is queued and processed by Celery worker
# Processing includes:
# 1. Signature validation
# 2. Workflow lookup
# 3. Async execution
# 4. Error handling with retry logic
```

### 3. Approval System

**Create Approval Request**:
```python
from backend.app.services.workflows import ApprovalSystem

approval_system = ApprovalSystem(db)

approval = await approval_system.create_approval_request(
    execution_id=execution.id,
    approval_type="email_send",
    approval_title="Send email to 500 leads",
    approval_description="Marketing campaign",
    priority=ApprovalPriority.HIGH,
    auto_approval_enabled=True
)
```

**Manual Approval**:
```python
# Approve
await approval_system.approve(
    approval_id=approval.id,
    approver_name="John Doe",
    reason="Campaign approved"
)

# Reject
await approval_system.reject(
    approval_id=approval.id,
    approver_name="John Doe",
    reason="Budget exceeded"
)
```

**Auto-Approval**:

The system uses OpenRouter AI to automatically evaluate approvals:

```python
# Auto-approval evaluates:
# - Confidence score (0-100)
# - Lead quality score
# - Email verification status
# - Suspicious pattern detection

# Auto-approves if:
# - Confidence >= 90%
# - No red flags detected
# - Within daily limits
```

### 4. Error Handling

**Retry Logic**:
- Exponential backoff: 60s, 120s, 240s
- Max retries: 3 (configurable)
- Failed webhooks automatically retried

**Error Monitoring**:
```python
# Get recent errors
errors = monitor.get_error_logs(hours=24, limit=50)

# Log custom error
await monitor.log_error(
    workflow_id=workflow.id,
    execution_id=execution.id,
    error_message="API timeout",
    severity="error"
)
```

---

## API Reference

### Webhook Endpoints (PUBLIC)

**POST /api/v1/webhooks/n8n/{workflow_id}**
- Receive webhook from N8N workflow
- Returns immediate 200 OK
- Processes async in background

**POST /api/v1/webhooks/n8n/generic**
- Generic webhook receiver
- Body: `{"event": "...", "data": {...}}`

**GET /api/v1/webhooks/n8n/test**
- Test webhook connectivity

### Workflow Endpoints

**GET /api/v1/workflows**
- List all workflows
- Query params: `is_active`, `page`, `page_size`

**POST /api/v1/workflows**
- Create new workflow
- Body: `N8NWorkflowCreate` schema

**GET /api/v1/workflows/{id}**
- Get workflow details

**PUT /api/v1/workflows/{id}**
- Update workflow
- Body: `N8NWorkflowUpdate` schema

**DELETE /api/v1/workflows/{id}**
- Delete workflow

**POST /api/v1/workflows/{id}/trigger**
- Manually trigger workflow
- Body: `WorkflowTrigger` schema

**GET /api/v1/workflows/{id}/executions**
- Get execution history

**GET /api/v1/workflows/{id}/stats**
- Get workflow statistics

### Execution Endpoints

**GET /api/v1/executions**
- List all executions
- Query params: `workflow_id`, `status`, `page`, `page_size`

**GET /api/v1/executions/{id}**
- Get execution details

**POST /api/v1/executions/{id}/retry**
- Retry failed execution

**POST /api/v1/executions/{id}/cancel**
- Cancel running execution

### Approval Endpoints

**GET /api/v1/approvals**
- List approval requests
- Query params: `status`, `priority`, `page`, `page_size`

**GET /api/v1/approvals/{id}**
- Get approval details

**POST /api/v1/approvals/{id}/approve**
- Approve request
- Body: `{"approver_name": "...", "reason": "..."}`

**POST /api/v1/approvals/{id}/reject**
- Reject request

**GET /api/v1/approvals/stats**
- Get approval statistics

**POST /api/v1/approvals/bulk-action**
- Bulk approve/reject
- Body: `{"approval_ids": [...], "action": "approved|rejected"}`

### Monitoring Endpoints

**GET /api/v1/monitoring/events**
- Get monitoring events
- Query params: `workflow_id`, `execution_id`, `severity`, `limit`

**GET /api/v1/monitoring/errors**
- Get recent errors
- Query params: `hours`, `limit`

**GET /api/v1/monitoring/dashboard**
- Get dashboard data

**GET /api/v1/health**
- System health check

---

## Workflow Templates

### 1. Lead Qualification Workflow

**Purpose**: Automatically qualify leads and route to appropriate workflows

**Trigger Events**: `lead_created`, `lead_updated`

**Steps**:
1. Analyze lead website
2. Calculate lead score
3. Route based on score:
   - Score >= 80: Trigger video + demo workflow
   - Score 60-79: Trigger email nurture
   - Score < 60: Queue for manual review

**Configuration**:
```json
{
  "workflow_name": "Lead Qualification",
  "trigger_events": ["lead_created"],
  "requires_approval": false,
  "auto_approval_enabled": true
}
```

### 2. Video + Demo Site Workflow

**Purpose**: Generate personalized video and demo site for qualified leads

**Trigger Events**: `lead_approved`, `high_score_lead`

**Steps**:
1. Generate AI script
2. Create voiceover
3. Record screen
4. Compose video
5. Generate demo site
6. Deploy to Vercel
7. Send email with links

**Approval Criteria**:
- Auto-approve if lead score >= 85
- Require manual approval if score < 70

### 3. Follow-up Automation Workflow

**Purpose**: Send automated follow-ups based on engagement

**Trigger Events**: `email_opened_no_reply`

**Steps**:
1. Check engagement level
2. Determine follow-up type
3. Generate follow-up content with AI
4. Send follow-up email
5. Schedule next follow-up if needed

**Send Rate Limits**:
- Max 2 emails per lead per week
- Min 48 hours between emails

---

## Approval System

### Approval Types

1. **workflow_execution**: Workflow trigger approval
2. **email_send**: Bulk email approval
3. **video_create**: Video generation approval
4. **demo_deploy**: Demo site deployment approval

### Priority Levels

- **HIGH**: Requires immediate attention
- **MEDIUM**: Normal priority (default)
- **LOW**: Can wait for batch processing

### Auto-Approval Logic

AI evaluates approvals based on:

**Scoring Factors**:
- Lead quality score (0-100)
- Email verification status
- Website activity
- Suspicious pattern detection

**Auto-approve if**:
- Confidence >= 90%
- Lead score >= 80
- Email verified
- No suspicious patterns

**Require manual approval if**:
- Confidence < 90%
- Lead score < 70
- Suspicious patterns detected
- High-value action (e.g., >1000 emails)

### Approval Expiration

- Default: 24 hours
- Configurable per approval
- Auto-rejected after expiration
- Periodic cleanup task runs hourly

---

## Monitoring & Debugging

### Event Types

- `execution_created`: Workflow execution started
- `execution_started`: Execution running in N8N
- `execution_completed`: Execution finished successfully
- `execution_failed`: Execution failed
- `approval_required`: Approval gate reached
- `approval_granted`: Approval approved
- `error`: Error occurred

### Severity Levels

- **INFO**: Normal operations
- **WARNING**: Non-critical issues
- **ERROR**: Errors requiring attention
- **CRITICAL**: Critical system failures

### Dashboard Metrics

Access via `/api/v1/monitoring/dashboard`:

- Total workflows (active/inactive)
- Executions today (success/failed)
- Pending approvals
- Recent errors
- Average execution time

### Debugging Tips

1. **Check execution logs**:
```bash
GET /api/v1/executions/{id}
# Review execution_log field
```

2. **Monitor webhook queue**:
```bash
GET /api/v1/webhooks/queue/status
# Check for stuck webhooks
```

3. **Review error logs**:
```bash
GET /api/v1/monitoring/errors?hours=24
```

4. **Enable debug logging**:
```python
import logging
logging.getLogger('backend.app.services.workflows').setLevel(logging.DEBUG)
```

---

## Best Practices

### 1. Workflow Design

- Keep workflows focused on single responsibility
- Use descriptive workflow names
- Set appropriate timeouts
- Configure max retries conservatively

### 2. Approval Gates

- Use approvals for sensitive actions
- Enable auto-approval for low-risk operations
- Set appropriate expiration times
- Monitor approval queue regularly

### 3. Error Handling

- Implement proper error logging
- Set up error notifications
- Use retry logic for transient failures
- Monitor failed executions

### 4. Performance

- Use webhook queues for async processing
- Batch similar operations
- Clean up old monitoring events
- Monitor execution duration

### 5. Security

- Validate webhook signatures
- Use secrets for sensitive data
- Implement rate limiting
- Audit approval decisions

---

## Troubleshooting

### Webhook Not Received

**Symptoms**: N8N sends webhook but backend doesn't receive it

**Solutions**:
1. Check N8N webhook URL is correct
2. Verify firewall allows incoming webhooks
3. Check webhook signature validation
4. Review N8N execution logs

### Execution Stuck in Pending

**Symptoms**: Execution stays in pending status

**Solutions**:
1. Check if approval required
2. Verify N8N workflow is active
3. Review execution logs
4. Check N8N API connectivity

### Auto-Approval Not Working

**Symptoms**: Approvals not auto-approved despite high confidence

**Solutions**:
1. Check `AUTO_APPROVAL_ENABLED=true`
2. Verify confidence threshold setting
3. Review approval criteria
4. Check daily limit not exceeded

### High Error Rate

**Symptoms**: Many failed executions

**Solutions**:
1. Review error logs for patterns
2. Check N8N API status
3. Verify network connectivity
4. Increase timeout if needed

### Slow Processing

**Symptoms**: Webhooks processed slowly

**Solutions**:
1. Scale Celery workers
2. Check database performance
3. Review webhook queue size
4. Optimize workflow steps

---

## Support

For issues or questions:
- Check logs: `backend/logs/workflows.log`
- Review monitoring dashboard
- Contact support: support@craigleadspro.com

---

**Last Updated**: 2025-01-05
**Version**: 1.0.0
**Phase**: 6 - N8N Workflow Automation
