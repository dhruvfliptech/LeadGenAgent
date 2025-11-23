# Workflow Approvals API Documentation

## Overview

The Workflow Approvals API enables human-in-the-loop approval workflows for n8n automation. Pause workflows to request approval, auto-approve based on rules, and track approval history with comprehensive audit logging.

**Base URL:** `/api/v1/approvals`

## Key Features

- Flexible approval request system for n8n workflows
- Auto-approval engine with configurable rules
- Approval queue management with SLA tracking
- Escalation workflow for high-priority items
- Comprehensive audit logging
- Slack/Email notifications
- Webhook integration with n8n

## Authentication

All endpoints require authentication:

```
Authorization: Bearer YOUR_API_TOKEN
```

---

## Core Endpoints

### 1. Create Approval Request

Create a new approval request and pause workflow.

**Endpoint:** `POST /create`

**Request Schema:**

```json
{
  "approval_type": "lead_qualification",
  "resource_id": 42,
  "resource_data": {
    "company_name": "Acme Corp",
    "opportunity_value": 50000,
    "qualification_score": 0.85
  },
  "workflow_execution_id": "exec_abc123",
  "timeout_minutes": 60,
  "approvers": ["manager@example.com", "director@example.com"],
  "metadata": {
    "campaign_id": 1,
    "source": "linkedin"
  },
  "resume_webhook_url": "https://n8n.example.com/webhook/resume-workflow"
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| approval_type | string | Yes | lead_qualification, response_review, export_approval, campaign_approval |
| resource_id | integer | Yes | ID of resource to approve |
| resource_data | object | Yes | Data about the resource |
| workflow_execution_id | string | Yes | n8n execution ID |
| timeout_minutes | integer | No | Minutes before auto-reject (5-1440, default: 60) |
| approvers | array | No | Email addresses of approvers |
| metadata | object | No | Additional context data |
| resume_webhook_url | string | No | n8n webhook to resume workflow |

**Valid Approval Types:**

| Type | Description |
|------|-------------|
| lead_qualification | Lead quality review |
| response_review | Auto-response content review |
| export_approval | Bulk export approval |
| campaign_approval | Campaign launch approval |
| custom | Custom approval type |

**Response Schema:**

```json
{
  "success": true,
  "approval_id": 1001,
  "message": "Approval request created successfully",
  "timeout_minutes": 60
}
```

**Example Request:**

```bash
curl -X POST "https://api.example.com/api/v1/approvals/create" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approval_type": "lead_qualification",
    "resource_id": 42,
    "resource_data": {
      "company_name": "Acme Corp",
      "opportunity_value": 50000
    },
    "workflow_execution_id": "exec_abc123",
    "timeout_minutes": 60,
    "approvers": ["manager@example.com"],
    "resume_webhook_url": "https://n8n.example.com/webhook/resume"
  }'
```

**Error Responses:**

| Code | Message | Description |
|------|---------|-------------|
| 400 | Invalid approval type | Approval type not recognized |
| 400 | Invalid webhook URL | Webhook URL failed security check |
| 500 | Failed to create approval | Database or service error |

---

### 2. Get Pending Approvals

Retrieve pending approvals for review.

**Endpoint:** `GET /pending`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| approver_email | string | No | Filter by approver email |
| approval_type | string | No | Filter by approval type |
| limit | integer | No | Maximum results (default: 50, max: 200) |

**Response Schema:**

```json
{
  "count": 15,
  "approvals": [
    {
      "id": 1001,
      "approval_type": "lead_qualification",
      "resource_id": 42,
      "resource_data": {
        "company_name": "Acme Corp",
        "opportunity_value": 50000
      },
      "status": "pending",
      "workflow_execution_id": "exec_abc123",
      "created_at": "2024-01-15T10:30:00Z",
      "timeout_at": "2024-01-15T11:30:00Z",
      "approvers": ["manager@example.com"],
      "metadata": {"campaign_id": 1}
    }
  ]
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/v1/approvals/pending?approver_email=manager@example.com" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 3. Get Approval Details

Retrieve detailed information about a specific approval.

**Endpoint:** `GET /{approval_id}`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| approval_id | integer | Yes | Approval ID |

**Response Schema:**

```json
{
  "approval": {
    "id": 1001,
    "approval_type": "lead_qualification",
    "resource_id": 42,
    "resource_type": "lead",
    "resource_data": {
      "company_name": "Acme Corp",
      "opportunity_value": 50000,
      "qualification_score": 0.85
    },
    "status": "pending",
    "workflow_execution_id": "exec_abc123",
    "created_at": "2024-01-15T10:30:00Z",
    "timeout_at": "2024-01-15T11:30:00Z",
    "decided_at": null,
    "reviewer_email": null,
    "reviewer_comments": null,
    "approved": null,
    "approval_method": null,
    "auto_approval_score": null,
    "auto_approval_reason": null,
    "escalation_level": 0,
    "escalated_to": null,
    "metadata": {"campaign_id": 1}
  },
  "queue": {
    "priority": 2,
    "assigned_to": "manager@example.com",
    "sla_deadline": "2024-01-15T12:00:00Z",
    "sla_status": "on_track"
  },
  "history": [
    {
      "action": "created",
      "actor_email": "system@example.com",
      "action_data": {},
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/v1/approvals/1001" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 4. Submit Decision

Approve or reject an approval request.

**Endpoint:** `POST /{approval_id}/decide`

**Request Schema:**

```json
{
  "approved": true,
  "reviewer_email": "manager@example.com",
  "comments": "Looks good. Approved for processing.",
  "modified_data": {
    "opportunity_value": 55000,
    "priority": "high"
  }
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| approved | boolean | Yes | true to approve, false to reject |
| reviewer_email | string | Yes | Email of reviewer |
| comments | string | No | Reviewer notes (max: 2000 chars) |
| modified_data | object | No | Updated resource data |

**Response Schema:**

```json
{
  "success": true,
  "approval_id": 1001,
  "status": "approved",
  "decided_at": "2024-01-15T10:45:00Z",
  "webhook_triggered": true,
  "message": "Approval submitted and workflow resumed"
}
```

**Example Request:**

```bash
curl -X POST "https://api.example.com/api/v1/approvals/1001/decide" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approved": true,
    "reviewer_email": "manager@example.com",
    "comments": "Approved for processing"
  }'
```

**Webhook Trigger:**

After decision, triggers webhook to resume n8n workflow:

```json
{
  "approval_id": 1001,
  "approved": true,
  "reviewer_email": "manager@example.com",
  "comments": "Approved for processing",
  "resource_data": {
    "company_name": "Acme Corp",
    "opportunity_value": 50000
  }
}
```

---

### 5. Escalate Approval

Escalate an approval to higher authority.

**Endpoint:** `POST /{approval_id}/escalate`

**Request Schema:**

```json
{
  "escalation_level": 1,
  "escalated_to": "director@example.com",
  "reason": "High-value opportunity requiring director approval"
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| escalation_level | integer | No | Escalation level (1-5, default: 1) |
| escalated_to | string | No | Email of escalated reviewer |
| reason | string | No | Reason for escalation |

**Response Schema:**

```json
{
  "success": true,
  "approval_id": 1001,
  "escalation_level": 1,
  "message": "Approval escalated successfully"
}
```

**Example Request:**

```bash
curl -X POST "https://api.example.com/api/v1/approvals/1001/escalate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "escalation_level": 1,
    "escalated_to": "director@example.com",
    "reason": "High-value opportunity"
  }'
```

---

### 6. Bulk Approval

Approve multiple requests at once.

**Endpoint:** `POST /bulk-approve`

**Request Schema:**

```json
{
  "approval_ids": [1001, 1002, 1003],
  "reviewer_email": "manager@example.com",
  "comments": "Batch approved"
}
```

**Field Descriptions:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-----------|-------------|
| approval_ids | array | Yes | 1-50 items | Approval IDs to approve |
| reviewer_email | string | Yes | - | Email of reviewer |
| comments | string | No | Max: 2000 chars | Approval comments |

**Response Schema:**

```json
{
  "success": true,
  "approved_count": 3,
  "failed_count": 0,
  "results": {
    "approved": [1001, 1002, 1003],
    "failed": []
  }
}
```

**Example Request:**

```bash
curl -X POST "https://api.example.com/api/v1/approvals/bulk-approve" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approval_ids": [1001, 1002, 1003],
    "reviewer_email": "manager@example.com",
    "comments": "Batch approved"
  }'
```

---

### 7. Get Approval Statistics

Get system-wide approval statistics.

**Endpoint:** `GET /stats`

**Response Schema:**

```json
{
  "total_approvals": 1500,
  "pending_count": 45,
  "approved_count": 1200,
  "rejected_count": 150,
  "auto_approved_count": 105,
  "average_approval_time_minutes": 30,
  "approval_rate_percentage": 80.0,
  "auto_approval_rate_percentage": 7.0,
  "pending_by_type": {
    "lead_qualification": 20,
    "response_review": 15,
    "export_approval": 10
  },
  "pending_by_approver": {
    "manager@example.com": 20,
    "director@example.com": 25
  },
  "overdue_count": 5
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/v1/approvals/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 8. Check Approval Timeouts

Background job to handle timed-out approvals.

**Endpoint:** `POST /check-timeouts`

**Response Schema:**

```json
{
  "success": true,
  "timed_out_count": 3,
  "message": "Processed 3 timed out approvals"
}
```

**Details:**

- Automatically rejects approvals that exceed timeout_minutes
- Triggers webhook to notify n8n workflow of rejection
- Records timeout in approval history

**Typical Setup:**

Configure a cron job to call this endpoint every 5 minutes:

```bash
# Every 5 minutes
*/5 * * * * curl -X POST "https://api.example.com/api/v1/approvals/check-timeouts" \
  -H "Authorization: Bearer CRON_TOKEN"
```

---

## Auto-Approval Rules Endpoints

### 9. Get Auto-Approval Rules

Retrieve all auto-approval rules.

**Endpoint:** `GET /auto-approval/rules`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| active_only | boolean | No | Only active rules (default: true) |

**Response Schema:**

```json
{
  "count": 5,
  "rules": [
    {
      "id": 1,
      "name": "High-Quality Leads",
      "description": "Auto-approve high-quality leads from LinkedIn",
      "approval_types": ["lead_qualification"],
      "auto_approve_threshold": 0.85,
      "min_qualification_score": 0.80,
      "required_keywords": ["CEO", "CTO", "VP"],
      "excluded_keywords": ["spam", "bot"],
      "lead_categories": ["enterprise"],
      "priority": 100,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/v1/approvals/auto-approval/rules?active_only=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 10. Create Auto-Approval Rule

Create a new auto-approval rule.

**Endpoint:** `POST /auto-approval/rules`

**Request Schema:**

```json
{
  "name": "High-Quality Leads",
  "description": "Auto-approve high-quality leads from LinkedIn",
  "approval_types": ["lead_qualification"],
  "auto_approve_threshold": 0.85,
  "min_qualification_score": 0.80,
  "required_keywords": ["CEO", "CTO", "VP"],
  "excluded_keywords": ["spam", "bot"],
  "lead_categories": ["enterprise"],
  "priority": 100
}
```

**Field Descriptions:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-----------|-------------|
| name | string | Yes | 1-255 chars | Rule name |
| description | string | Yes | - | Rule description |
| approval_types | array | Yes | - | Applicable approval types |
| auto_approve_threshold | number | No | 0.5-1.0, default: 0.85 | Confidence threshold for auto-approval |
| min_qualification_score | number | No | 0.0-1.0 | Minimum qualification score |
| required_keywords | array | No | - | Keywords that must be present |
| excluded_keywords | array | No | - | Keywords that prevent approval |
| lead_categories | array | No | - | Lead categories to apply rule to |
| priority | integer | No | 0-1000, default: 0 | Rule evaluation order |

**Response Schema:**

```json
{
  "success": true,
  "rule": {
    "id": 10,
    "name": "High-Quality Leads",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Example Request:**

```bash
curl -X POST "https://api.example.com/api/v1/approvals/auto-approval/rules" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High-Quality Leads",
    "description": "Auto-approve high-quality leads",
    "approval_types": ["lead_qualification"],
    "auto_approve_threshold": 0.85,
    "priority": 100
  }'
```

---

### 11. Get Rule Performance

Get performance metrics for an auto-approval rule.

**Endpoint:** `GET /auto-approval/rules/{rule_id}/performance`

**Response Schema:**

```json
{
  "rule_id": 10,
  "rule_name": "High-Quality Leads",
  "total_evaluations": 500,
  "auto_approved": 425,
  "auto_rejected": 75,
  "approval_rate": 0.85,
  "false_positive_rate": 0.05,
  "avg_confidence_score": 0.92,
  "created_at": "2024-01-01T00:00:00Z",
  "last_evaluated": "2024-01-15T10:30:00Z"
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/v1/approvals/auto-approval/rules/10/performance" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 12. Optimize Rule Threshold

Automatically optimize rule threshold based on target approval rate.

**Endpoint:** `POST /auto-approval/rules/{rule_id}/optimize`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| target_approval_rate | float | No | Target approval rate (0.5-0.95, default: 0.8) |

**Response Schema:**

```json
{
  "success": true,
  "rule_id": 10,
  "old_threshold": 0.85,
  "new_threshold": 0.82,
  "target_approval_rate": 0.80
}
```

**Example Request:**

```bash
curl -X POST "https://api.example.com/api/v1/approvals/auto-approval/rules/10/optimize?target_approval_rate=0.80" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 13. Get Rule Templates

Get predefined auto-approval rule templates.

**Endpoint:** `GET /auto-approval/templates`

**Response Schema:**

```json
{
  "count": 3,
  "templates": [
    {
      "name": "Enterprise Leads Only",
      "description": "Auto-approve enterprise-tier leads with high qualification scores",
      "approval_types": ["lead_qualification"],
      "auto_approve_threshold": 0.90,
      "min_qualification_score": 0.85,
      "lead_categories": ["enterprise"],
      "priority": 200
    },
    {
      "name": "Mid-Market Qualified",
      "description": "Auto-approve mid-market leads meeting basic criteria",
      "approval_types": ["lead_qualification"],
      "auto_approve_threshold": 0.75,
      "min_qualification_score": 0.70,
      "lead_categories": ["mid_market"],
      "priority": 100
    },
    {
      "name": "High-Value Contacts",
      "description": "Auto-approve C-level contacts from target industries",
      "approval_types": ["lead_qualification"],
      "auto_approve_threshold": 0.88,
      "required_keywords": ["CEO", "CTO", "VP"],
      "priority": 150
    }
  ]
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/v1/approvals/auto-approval/templates" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 14. Apply Rule Template

Apply a predefined template as a new rule.

**Endpoint:** `POST /auto-approval/templates/{template_index}/apply`

**Response Schema:**

```json
{
  "success": true,
  "message": "Applied template: Enterprise Leads Only",
  "rule": {
    "id": 11,
    "name": "Enterprise Leads Only",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Example Request:**

```bash
curl -X POST "https://api.example.com/api/v1/approvals/auto-approval/templates/0/apply" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## n8n Integration Guide

### Setup Approval Workflow in n8n

1. **Create Pause Node:**
   - Use Webhook node to receive approval requests
   - Call FlipTech Approvals API to create request

2. **Resume Workflow:**
   - Configure resume_webhook_url in approval request
   - Approval system calls webhook with decision

3. **Example n8n Workflow:**

```
Lead Processing → Qualification →
  [Pause for Approval] →
    Approval Endpoint (POST /create) →
    [Wait for webhook callback] →
  [Resume Processing] →
Send Email
```

**n8n HTTP Node Configuration:**

```json
{
  "method": "POST",
  "url": "https://api.example.com/api/v1/approvals/create",
  "headers": {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
  },
  "body": {
    "approval_type": "lead_qualification",
    "resource_id": "{{ $node.Lead.data.id }}",
    "resource_data": {
      "company_name": "{{ $node.Lead.data.company }}",
      "opportunity_value": "{{ $node.Lead.data.value }}"
    },
    "workflow_execution_id": "{{ $execution.id }}",
    "resume_webhook_url": "{{ $env.N8N_WEBHOOK_URL }}/resume-workflow",
    "timeout_minutes": 60
  }
}
```

---

## Use Cases

### Use Case 1: Auto-Approve High-Quality Leads

```bash
# 1. Create auto-approval rule
RULE=$(curl -X POST "https://api.example.com/api/v1/approvals/auto-approval/rules" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "name": "Auto-Approve Enterprise Leads",
    "approval_types": ["lead_qualification"],
    "auto_approve_threshold": 0.85,
    "min_qualification_score": 0.80,
    "lead_categories": ["enterprise"]
  }')

# 2. Create approval (auto-approved if rule matches)
curl -X POST "https://api.example.com/api/v1/approvals/create" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "approval_type": "lead_qualification",
    "resource_id": 42,
    "resource_data": {
      "company_name": "Acme",
      "qualification_score": 0.92
    }
  }'
# Returns: approval_id = 1001, auto_approved = true
```

### Use Case 2: Manual Approval Workflow

```bash
# 1. Create approval (pauses workflow)
APPROVAL=$(curl -X POST "https://api.example.com/api/v1/approvals/create" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "approval_type": "response_review",
    "resource_id": 123,
    "workflow_execution_id": "exec_xyz"
  }')

# 2. Manager reviews (GET /pending)
curl "https://api.example.com/api/v1/approvals/pending?approver_email=manager@example.com" \
  -H "Authorization: Bearer TOKEN"

# 3. Manager approves
curl -X POST "https://api.example.com/api/v1/approvals/1001/decide" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "approved": true,
    "reviewer_email": "manager@example.com",
    "comments": "Looks good"
  }'
# Webhook called to resume n8n workflow
```

---

## Error Codes

| Code | Status | Description | Solution |
|------|--------|-------------|----------|
| 400 | Bad Request | Invalid approval type | Check valid types |
| 400 | Bad Request | Invalid webhook URL | Validate URL security |
| 404 | Not Found | Approval not found | Verify approval ID |
| 500 | Server Error | Failed to create | Check server logs |

---

## Best Practices

1. **Set Appropriate Timeouts** - Use 60-120 minutes for most workflows
2. **Monitor Auto-Approval Rates** - Adjust thresholds based on performance
3. **Create Rule Templates** - Use templates for consistent rules
4. **Log Decisions** - Always include reviewer comments
5. **Escalate High-Value Items** - Ensure important items get proper review
6. **Test Webhooks** - Verify n8n integration before production
7. **Monitor SLA** - Check approval queue for bottlenecks

---

## Support

For issues:
- Email: support@example.com
- Docs: https://docs.example.com
- Status: https://status.example.com
