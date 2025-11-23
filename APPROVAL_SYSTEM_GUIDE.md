# Human-in-the-Loop Approval System Guide

## Overview

The Approval System provides comprehensive human-in-the-loop decision making for n8n workflow automation. It pauses workflows at critical points, requests human approval, and resumes execution based on the decision.

## Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Approval Types](#approval-types)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Auto-Approval Rules](#auto-approval-rules)
- [Frontend Integration](#frontend-integration)
- [n8n Integration](#n8n-integration)
- [Notifications](#notifications)
- [Best Practices](#best-practices)

---

## Architecture

### Components

1. **ApprovalSystem Service** (`approval_system.py`)
   - Core approval orchestration
   - Workflow pause/resume
   - Timeout management
   - Notification handling

2. **AutoApprovalEngine** (`auto_approval.py`)
   - Rule-based auto-approval
   - Score calculation
   - Threshold optimization

3. **API Endpoints** (`workflow_approvals.py`)
   - RESTful approval API
   - Decision submission
   - Bulk operations

4. **Database Models** (`approvals.py`)
   - ResponseApproval: Main approval records
   - ApprovalRule: Auto-approval rules
   - ApprovalQueue: Queue management
   - ApprovalHistory: Audit trail
   - ApprovalSettings: System configuration

5. **Integrations**
   - Slack notifications (`slack_approvals.py`)
   - Email notifications (templates)
   - n8n webhook callbacks

### Data Flow

```
┌─────────────┐
│   n8n       │
│  Workflow   │
└──────┬──────┘
       │
       │ 1. Create Approval Request
       ▼
┌──────────────────┐
│ Approval System  │◄────── Auto-Approval
└──────┬───────────┘        Rules Engine
       │
       │ 2. Check Auto-Approval
       │
       ├─────► Auto-Approve? ────► Resume Workflow
       │                            (webhook)
       │
       │ 3. Manual Review Needed
       ▼
┌──────────────────┐
│  Notifications   │
│  (Email/Slack)   │
└──────────────────┘
       │
       │ 4. Human Decision
       ▼
┌──────────────────┐
│  Frontend UI     │
│  /approvals      │
└──────┬───────────┘
       │
       │ 5. Submit Decision
       ▼
┌──────────────────┐
│ Decision Handler │────► Resume Workflow
│  (API Endpoint)  │       (webhook)
└──────────────────┘
```

---

## Features

### Core Features

- ✅ **Workflow Pause/Resume**: Pause n8n workflows for human approval
- ✅ **Multiple Approval Types**: Demo sites, videos, emails, plans, leads
- ✅ **Auto-Approval Rules**: Intelligent automatic approval based on criteria
- ✅ **Timeout Handling**: Automatic rejection after timeout
- ✅ **Escalation**: Escalate approvals to higher authority
- ✅ **Bulk Operations**: Approve multiple items at once
- ✅ **Audit Trail**: Complete history of all decisions
- ✅ **Notifications**: Email and Slack notifications
- ✅ **Statistics**: Performance metrics and analytics

### Advanced Features

- **Smart Scoring**: Multi-factor scoring algorithm
- **Threshold Optimization**: ML-based threshold tuning
- **SLA Tracking**: Service level agreement monitoring
- **Priority Queues**: Urgent/High/Normal/Low prioritization
- **Conditional Rules**: Complex rule matching
- **Template System**: Predefined rule templates

---

## Approval Types

### 1. Demo Site Review
- **Purpose**: Review generated demo sites before deployment
- **Resource Data**:
  ```json
  {
    "site_url": "https://demo.example.com",
    "business_name": "Tech Startup",
    "quality_score": 0.85,
    "preview_url": "https://screenshots.example.com/demo.png"
  }
  ```

### 2. Video Review
- **Purpose**: Review composed videos before publishing
- **Resource Data**:
  ```json
  {
    "video_url": "https://videos.example.com/video.mp4",
    "duration": 120,
    "quality_score": 0.90,
    "thumbnail_url": "https://videos.example.com/thumb.jpg"
  }
  ```

### 3. Email Content Review
- **Purpose**: Review generated emails before sending
- **Resource Data**:
  ```json
  {
    "subject": "Partnership Opportunity",
    "body": "Email content...",
    "recipient": "lead@example.com",
    "template_name": "Partnership Outreach"
  }
  ```

### 4. Improvement Plan Review
- **Purpose**: Review AI-generated improvement plans
- **Resource Data**:
  ```json
  {
    "lead_id": 123,
    "improvements": [...],
    "estimated_impact": "high",
    "quality_score": 0.88
  }
  ```

### 5. Lead Qualification
- **Purpose**: Review lead qualification decisions
- **Resource Data**:
  ```json
  {
    "lead_id": 456,
    "qualification_score": 0.75,
    "category": "software",
    "compensation": "$80k-$100k"
  }
  ```

### 6. Campaign Launch
- **Purpose**: Approve campaign launches
- **Resource Data**:
  ```json
  {
    "campaign_name": "Q4 Outreach",
    "target_count": 100,
    "budget": 5000,
    "start_date": "2025-11-15"
  }
  ```

### 7. Budget Approval
- **Purpose**: Approve budget allocations
- **Resource Data**:
  ```json
  {
    "amount": 10000,
    "category": "advertising",
    "justification": "Increase lead generation"
  }
  ```

---

## Quick Start

### 1. Create Approval Request from n8n

In your n8n workflow, add an HTTP Request node:

```json
{
  "method": "POST",
  "url": "http://backend:8000/api/v1/workflow-approvals/create",
  "body": {
    "approval_type": "demo_site_review",
    "resource_id": 123,
    "resource_data": {
      "site_url": "https://demo.example.com",
      "business_name": "Tech Startup",
      "quality_score": 0.85
    },
    "workflow_execution_id": "{{ $execution.id }}",
    "timeout_minutes": 120,
    "approvers": ["admin@example.com"],
    "resume_webhook_url": "{{ $execution.resumeUrl }}"
  }
}
```

### 2. Wait for Approval

Add a "Wait" node configured to wait for webhook:

```json
{
  "resume": "webhook",
  "options": {
    "webhookId": "{{ $json.approval_id }}"
  }
}
```

### 3. Process Decision

After approval/rejection, the workflow resumes with:

```json
{
  "approved": true,
  "approval_id": 123,
  "reviewer_email": "admin@example.com",
  "comments": "Looks great!",
  "resource_data": { ... }
}
```

---

## API Reference

### Create Approval

**Endpoint**: `POST /api/v1/workflow-approvals/create`

**Request**:
```json
{
  "approval_type": "demo_site_review",
  "resource_id": 123,
  "resource_data": {
    "quality_score": 0.85,
    "preview_url": "https://example.com/preview"
  },
  "workflow_execution_id": "exec-123",
  "timeout_minutes": 60,
  "approvers": ["admin@example.com"],
  "metadata": {
    "priority": "high"
  },
  "resume_webhook_url": "https://n8n.example.com/webhook/resume"
}
```

**Response**:
```json
{
  "success": true,
  "approval_id": 456,
  "message": "Approval request created successfully",
  "timeout_minutes": 60
}
```

### Get Pending Approvals

**Endpoint**: `GET /api/v1/workflow-approvals/pending`

**Query Parameters**:
- `approver_email`: Filter by approver
- `approval_type`: Filter by type
- `limit`: Number of results (default: 50)

**Response**:
```json
{
  "count": 5,
  "approvals": [
    {
      "id": 456,
      "approval_type": "demo_site_review",
      "resource_id": 123,
      "resource_data": { ... },
      "status": "pending",
      "created_at": "2025-11-04T12:00:00Z",
      "timeout_at": "2025-11-04T14:00:00Z"
    }
  ]
}
```

### Submit Decision

**Endpoint**: `POST /api/v1/workflow-approvals/{approval_id}/decide`

**Request**:
```json
{
  "approved": true,
  "reviewer_email": "admin@example.com",
  "comments": "Approved with minor suggestions",
  "modified_data": {
    "quality_score": 0.90
  }
}
```

**Response**:
```json
{
  "success": true,
  "approval_id": 456,
  "status": "approved",
  "approved": true,
  "webhook_triggered": true,
  "webhook_response": {
    "status_code": 200
  }
}
```

### Bulk Approve

**Endpoint**: `POST /api/v1/workflow-approvals/bulk-approve`

**Request**:
```json
{
  "approval_ids": [456, 457, 458],
  "reviewer_email": "admin@example.com",
  "comments": "Bulk approved - all look good"
}
```

### Get Statistics

**Endpoint**: `GET /api/v1/workflow-approvals/stats`

**Response**:
```json
{
  "by_status": {
    "pending": 5,
    "approved": 100,
    "rejected": 10,
    "timeout": 2
  },
  "by_type": {
    "demo_site_review": 50,
    "video_review": 40,
    "email_content_review": 27
  },
  "total_approvals": 117,
  "auto_approved_count": 80,
  "auto_approval_rate": 0.68,
  "avg_decision_time_minutes": 15.5
}
```

---

## Auto-Approval Rules

### Creating Rules

**Endpoint**: `POST /api/v1/workflow-approvals/auto-approval/rules`

**Example: High Quality Auto-Approve**:
```json
{
  "name": "High Quality Demo Sites",
  "description": "Auto-approve demo sites with quality > 85%",
  "approval_types": ["demo_site_review"],
  "auto_approve_threshold": 0.85,
  "min_qualification_score": 0.75,
  "lead_categories": ["software", "web development"],
  "priority": 100
}
```

### Scoring Algorithm

The auto-approval score is calculated using multiple factors:

```python
score = (
    quality_score * 0.4 +
    qualification_score * 0.3 +
    historical_success_rate * 0.15 +
    completeness * 0.1 +
    freshness * 0.05
)
```

**Factors**:
1. **Quality Score (40%)**: Overall quality rating
2. **Qualification Score (30%)**: Lead qualification rating
3. **Historical Success (15%)**: Past performance in category
4. **Completeness (10%)**: How complete the data is
5. **Freshness (5%)**: How recent the resource is

### Rule Templates

Apply predefined templates:

```bash
# Get templates
GET /api/v1/workflow-approvals/auto-approval/templates

# Apply template
POST /api/v1/workflow-approvals/auto-approval/templates/0/apply
```

**Available Templates**:
1. High Quality Leads (threshold: 0.85)
2. Demo Sites - Tech Categories (threshold: 0.80)
3. Short Videos (threshold: 0.75)
4. Template-Based Emails (threshold: 0.82)

### Threshold Optimization

Automatically optimize rule thresholds based on historical performance:

```bash
POST /api/v1/workflow-approvals/auto-approval/rules/{rule_id}/optimize?target_approval_rate=0.8
```

This analyzes past approvals and adjusts the threshold to achieve the target approval rate.

---

## Frontend Integration

### React Component

The Approvals page displays pending approvals and allows quick approve/reject:

```typescript
import { workflowApprovalsApi } from '@/services/api'

// Get pending approvals
const { data } = useQuery({
  queryKey: ['workflow-approvals-pending'],
  queryFn: () => workflowApprovalsApi.getPending()
})

// Approve
const approveMutation = useMutation({
  mutationFn: (id: number) =>
    workflowApprovalsApi.approve(id, 'user@example.com', 'Approved!')
})

// Reject
const rejectMutation = useMutation({
  mutationFn: ({ id, comments }: { id: number; comments: string }) =>
    workflowApprovalsApi.reject(id, 'user@example.com', comments)
})
```

### Approval Dashboard

Access at: `http://localhost:3000/approvals`

Features:
- Real-time updates (10s polling)
- Filter by type and priority
- Quick approve/reject buttons
- Bulk operations
- Editing capability
- SLA countdown

---

## n8n Integration

### Complete Workflow Example

```
┌────────────────┐
│  Trigger       │
│  (New Lead)    │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Generate      │
│  Demo Site     │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  HTTP Request  │ ──► Create Approval Request
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Wait for      │
│  Webhook       │ ◄── Approval Decision
└───────┬────────┘
        │
        ├─► Approved ──► Deploy Site
        │
        └─► Rejected ──► Log & Cleanup
```

### n8n Node Configuration

**HTTP Request Node** (Create Approval):
```json
{
  "url": "={{ $env.BACKEND_URL }}/api/v1/workflow-approvals/create",
  "method": "POST",
  "sendBody": true,
  "bodyParameters": {
    "parameters": [
      {
        "name": "approval_type",
        "value": "demo_site_review"
      },
      {
        "name": "resource_id",
        "value": "={{ $json.demo_site_id }}"
      },
      {
        "name": "resource_data",
        "value": "={{ $json }}"
      },
      {
        "name": "workflow_execution_id",
        "value": "={{ $execution.id }}"
      },
      {
        "name": "timeout_minutes",
        "value": 120
      }
    ]
  }
}
```

**Wait Node**:
```json
{
  "resume": "webhook",
  "options": {
    "resumeOnTimeout": true,
    "timeoutAction": "reject"
  }
}
```

**IF Node** (Check Decision):
```json
{
  "conditions": {
    "boolean": [
      {
        "value1": "={{ $json.approved }}",
        "operation": "equal",
        "value2": true
      }
    ]
  }
}
```

---

## Notifications

### Email Notifications

Automatically sent when approval is created. Template: `approval_request.html`

Features:
- Beautiful HTML design
- Approval/Reject buttons
- Preview links
- Timeout countdown
- Resource details

### Slack Notifications

Interactive Slack messages with action buttons:

```python
from app.integrations.slack_approvals import SlackApprovalNotifier

slack = SlackApprovalNotifier()
await slack.send_approval_request(
    approval_id=456,
    approval_data={
        'type': 'demo_site_review',
        'description': 'Review demo site for Tech Startup',
        'preview_url': 'https://example.com/preview'
    },
    channel='#approvals'
)
```

Slack message includes:
- Approve/Reject buttons
- View Details link
- Timeout warning
- Resource preview

---

## Best Practices

### 1. Set Appropriate Timeouts

```python
timeout_guidelines = {
    'lead_qualification': 15,      # Quick decisions
    'email_content_review': 30,    # Standard review
    'demo_site_review': 120,       # Thorough review
    'improvement_plan_review': 240, # Complex analysis
    'budget_approval': 720          # Management approval
}
```

### 2. Use Auto-Approval Rules

For high-volume, low-risk approvals:
- Set conservative thresholds initially (0.90+)
- Monitor performance
- Gradually optimize thresholds
- Review auto-approved items periodically

### 3. Configure Escalation Chains

```json
{
  "escalation_chain": [
    {
      "level": 1,
      "approvers": ["team-lead@example.com"],
      "timeout_hours": 4
    },
    {
      "level": 2,
      "approvers": ["manager@example.com"],
      "timeout_hours": 24
    },
    {
      "level": 3,
      "approvers": ["director@example.com"],
      "timeout_hours": 48
    }
  ]
}
```

### 4. Monitor SLAs

Track and optimize decision times:
```python
stats = await approval_system.get_approval_statistics()
avg_time = stats['avg_decision_time_minutes']

if avg_time > target_sla:
    # Consider:
    # - Increasing auto-approval
    # - Adding more approvers
    # - Simplifying review process
```

### 5. Provide Rich Context

Include comprehensive resource_data:
```json
{
  "resource_data": {
    "title": "Clear title",
    "description": "Detailed description",
    "preview_url": "Direct link to preview",
    "quality_score": 0.85,
    "metadata": {
      "business_name": "Tech Startup",
      "category": "Software",
      "estimated_value": "$10k"
    }
  }
}
```

### 6. Implement Audit Trail

Always review history:
```python
history = await get_approval_history(approval_id)

for entry in history:
    log.info(f"{entry.action} by {entry.actor_email} at {entry.created_at}")
```

### 7. Handle Timeout Gracefully

Configure timeout behavior in n8n:
- Auto-reject and notify
- Escalate to manager
- Retry with different approver
- Default to safe action

---

## Troubleshooting

### Webhook Not Triggering

**Check**:
1. Webhook URL is correctly set
2. n8n webhook endpoint is accessible
3. Network connectivity between services
4. Check logs for HTTP errors

**Solution**:
```python
# Verify webhook in logs
logger.info(f"Triggering webhook: {approval.workflow_webhook_url}")
```

### Approvals Not Auto-Approving

**Check**:
1. Rule is active: `is_active = True`
2. Approval type matches rule
3. Score meets threshold
4. All rule conditions are satisfied

**Debug**:
```python
score = await auto_approval_engine.evaluate_auto_approval(
    approval_type='demo_site_review',
    resource_data=data
)
print(f"Score: {score}, Threshold: {rule.threshold}")
```

### Slow Approval Processing

**Optimize**:
1. Add database indexes
2. Cache frequently accessed data
3. Use background tasks for notifications
4. Implement approval batching

---

## Advanced Configuration

### Custom Notification Templates

Create custom email templates in `app/templates/email/`:

```html
<!-- custom_approval.html -->
<!DOCTYPE html>
<html>
<head>
    <title>{{ approval_type }} Approval</title>
</head>
<body>
    <!-- Your custom template -->
</body>
</html>
```

### Custom Scoring Algorithms

Extend AutoApprovalEngine:

```python
class CustomAutoApprovalEngine(AutoApprovalEngine):
    async def _calculate_composite_score(self, ...):
        # Your custom scoring logic
        base_score = await super()._calculate_composite_score(...)

        # Add custom factors
        if resource_data.get('is_enterprise'):
            base_score *= 1.1

        return min(1.0, base_score)
```

### Database Optimization

Add custom indexes:

```sql
CREATE INDEX idx_approval_custom
ON response_approvals (approval_type, status, created_at)
WHERE status = 'pending';
```

---

## Support

For issues or questions:
- Check logs: `backend/logs/approval_system.log`
- Review Slack #approvals channel
- Contact: engineering@example.com

---

**Generated**: 2025-11-04
**Version**: 1.0.0
**License**: MIT
