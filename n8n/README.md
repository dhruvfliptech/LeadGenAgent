# n8n Workflow Automation for CraigLeads Pro

Complete guide for setting up and using n8n workflow automation in the CraigLeads Pro lead generation system.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Custom Nodes](#custom-nodes)
5. [Workflow Templates](#workflow-templates)
6. [Webhook Integration](#webhook-integration)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Overview

n8n is the workflow automation engine that connects all components of CraigLeads Pro into a fully automated lead-to-customer pipeline.

### Architecture

```
┌─────────────┐      ┌──────────┐      ┌──────────────┐
│   Backend   │ ──→  │   n8n    │ ──→  │   Actions    │
│  (FastAPI)  │      │ Workflows│      │ (Demo/Video) │
└─────────────┘      └──────────┘      └──────────────┘
       ↑                   │                    │
       │                   ↓                    │
       │            ┌──────────────┐           │
       └────────────│   Webhooks   │←──────────┘
                    └──────────────┘
```

### Key Features

- **Lead Processing Pipeline**: Automated workflow from scrape to email
- **Human Approval Gates**: Manual review checkpoints
- **Demo Site Generation**: Automatic demo creation
- **Video Generation**: Personalized video creation
- **Email Automation**: Scheduled outreach campaigns
- **Error Handling**: Automatic retry and alerting
- **Analytics**: Execution tracking and reporting

---

## Installation

### Quick Start

```bash
# From project root
./scripts/start_n8n.sh
```

This script will:
1. Check Docker availability
2. Create necessary directories
3. Pull Docker images
4. Start n8n, PostgreSQL, and Redis
5. Wait for health checks
6. Display access information

### Manual Installation

#### Using Docker Compose (Recommended)

```bash
cd /Users/greenmachine2.0/Craigslist
docker-compose -f docker-compose.n8n.yml up -d
```

#### Using npm (Development)

```bash
npm install -g n8n
n8n start --tunnel
```

### Access n8n

After installation, access n8n at:
- **URL**: http://localhost:5678
- **Username**: admin
- **Password**: changeme (CHANGE THIS!)

---

## Configuration

### Environment Variables

All configuration is in `.env.n8n`:

```bash
# Core settings
N8N_URL=http://localhost:5678
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your_secure_password

# Database
N8N_DB_TYPE=postgresdb
N8N_DB_HOST=postgres
N8N_DB_DATABASE=n8n

# Backend integration
BACKEND_API_URL=http://host.docker.internal:8000/api/v1
CRAIGLEADS_API_KEY=your_api_key
```

### Important: Change Default Credentials

```bash
# Generate secure encryption key
openssl rand -hex 32

# Update .env.n8n with:
N8N_ENCRYPTION_KEY=<your_generated_key>
N8N_BASIC_AUTH_PASSWORD=<your_secure_password>
```

### Database Setup

n8n uses PostgreSQL for persistence. The database is automatically initialized on first run.

**Backup database:**
```bash
docker-compose -f docker-compose.n8n.yml exec postgres pg_dump -U n8n n8n > n8n_backup.sql
```

**Restore database:**
```bash
docker-compose -f docker-compose.n8n.yml exec -T postgres psql -U n8n n8n < n8n_backup.sql
```

---

## Custom Nodes

### CraigLeads Pro Node

Custom node for interacting with CraigLeads Pro API.

**Location**: `/n8n/custom-nodes/CraigleadsPro.node.ts`

#### Resources and Operations

**Lead Resource:**
- Get Lead by ID
- Get All Leads (with filters)
- Update Lead
- Update Lead Status

**Demo Site Resource:**
- Create Demo Site
- Get Demo Site
- Deploy Demo Site

**Video Resource:**
- Create Video
- Get Video
- Get Video Status

**Email Resource:**
- Send Outreach Email

**Analytics Resource:**
- Get Overview
- Get Conversion Stats

#### Example Usage

1. **Get Approved Leads**
```json
{
  "resource": "lead",
  "operation": "getAll",
  "filters": {
    "status": "approved",
    "min_score": 70
  }
}
```

2. **Create Demo Site**
```json
{
  "resource": "demoSite",
  "operation": "create",
  "leadId": "{{$json.lead_id}}",
  "businessName": "{{$json.business_name}}",
  "industry": "{{$json.category}}"
}
```

3. **Generate Video**
```json
{
  "resource": "video",
  "operation": "create",
  "demoSiteId": "{{$json.demo_id}}",
  "businessName": "{{$json.business_name}}"
}
```

### Installing Custom Nodes

Custom nodes are automatically loaded from `/n8n/custom-nodes/` directory.

**Build custom node:**
```bash
cd n8n/custom-nodes
npm install
npm run build
```

**Restart n8n to load:**
```bash
docker-compose -f docker-compose.n8n.yml restart n8n
```

---

## Workflow Templates

### 1. Lead Processing Pipeline

**Trigger**: Webhook on new lead scraped

**Steps**:
1. Receive lead data via webhook
2. Score lead (ML model)
3. If score > threshold → Auto-approve
4. If score in range → Manual approval gate
5. If approved → Trigger demo generation
6. Update lead status

**Import**: `workflows/lead-processing-pipeline.json`

### 2. Demo Generation Workflow

**Trigger**: Webhook on lead approved

**Steps**:
1. Get lead details
2. Create demo site (CraigLeads Pro API)
3. Wait for deployment
4. Get demo URL
5. Trigger video creation webhook
6. Update lead with demo URL

**Import**: `workflows/demo-generation-workflow.json`

### 3. Video Creation Workflow

**Trigger**: Webhook on demo completed

**Steps**:
1. Get demo site details
2. Generate video script
3. Create video (Remotion)
4. Wait for rendering
5. Get video URL
6. Trigger email workflow
7. Update lead with video URL

**Import**: `workflows/video-creation-workflow.json`

### 4. Email Outreach Workflow

**Trigger**: Webhook on video completed

**Steps**:
1. Get lead contact info
2. Build personalized email
3. Attach demo and video links
4. Send email
5. Log email sent
6. Schedule follow-up (7 days)
7. Update lead status

**Import**: `workflows/email-outreach-workflow.json`

### 5. Follow-up Campaign

**Trigger**: Schedule (daily at 9 AM)

**Steps**:
1. Get leads with "email_sent" status
2. Filter by last_contact_date > 7 days
3. Check if no response
4. Send follow-up email
5. Update last_contact_date

**Import**: `workflows/follow-up-campaign.json`

### Importing Workflows

1. Open n8n at http://localhost:5678
2. Click "Workflows" → "Import from File"
3. Select JSON file from `n8n/workflows/`
4. Configure credentials
5. Activate workflow

---

## Webhook Integration

### Backend Webhooks

The backend exposes webhooks for n8n to call:

**Endpoint**: `http://localhost:8000/api/v1/n8n-webhooks`

#### Available Webhooks

1. **Lead Scraped**
   - Path: `/webhook/lead-scraped`
   - Trigger: New lead discovered
   - Payload: Lead data

2. **Demo Completed**
   - Path: `/webhook/demo-completed`
   - Trigger: Demo site deployed
   - Payload: Demo site data

3. **Video Completed**
   - Path: `/webhook/video-completed`
   - Trigger: Video generated
   - Payload: Video data

4. **Approval Decision**
   - Path: `/webhook/approval-decision`
   - Trigger: Human approval/rejection
   - Payload: Approval decision

5. **Email Sent**
   - Path: `/webhook/email-sent`
   - Trigger: Email successfully sent
   - Payload: Email metadata

6. **Error**
   - Path: `/webhook/error`
   - Trigger: Workflow error
   - Payload: Error details

### n8n Webhooks

n8n exposes webhooks for the backend to call:

**Base URL**: `http://localhost:5678/webhook`

#### Webhook Configuration

In n8n workflow:
1. Add "Webhook" node
2. Set HTTP Method: POST
3. Set Path: `/lead-processing`
4. Authentication: None (or Header Auth)
5. Respond: Immediately
6. Response Data: First Entry JSON

### Testing Webhooks

**Test backend webhook:**
```bash
curl -X POST http://localhost:8000/api/v1/n8n-webhooks/webhook/lead-scraped \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": "123",
    "business_name": "Test Corp",
    "category": "contractors",
    "score": 85
  }'
```

**Test n8n webhook:**
```bash
curl -X POST http://localhost:5678/webhook/lead-processing \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": "123",
    "business_name": "Test Corp"
  }'
```

---

## Troubleshooting

### Common Issues

#### 1. n8n Won't Start

**Symptoms**: Container exits immediately

**Solutions**:
```bash
# Check logs
docker-compose -f docker-compose.n8n.yml logs n8n

# Check database connection
docker-compose -f docker-compose.n8n.yml exec postgres pg_isready -U n8n

# Reset database
docker-compose -f docker-compose.n8n.yml down -v
docker-compose -f docker-compose.n8n.yml up -d
```

#### 2. Webhooks Not Working

**Symptoms**: Workflows not triggering

**Solutions**:
- Check webhook URL is accessible
- Verify webhook path matches workflow
- Check n8n logs for webhook calls
- Test webhook with curl
- Ensure backend is running

```bash
# Check webhook registration
docker-compose -f docker-compose.n8n.yml exec n8n n8n webhook:list
```

#### 3. Credentials Not Working

**Symptoms**: API calls fail with auth errors

**Solutions**:
- Re-enter credentials in n8n UI
- Check API key is correct
- Verify backend API is accessible
- Test API endpoint manually

```bash
# Test CraigLeads Pro API
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/api/v1/leads
```

#### 4. Workflows Timing Out

**Symptoms**: Executions stuck in "Running"

**Solutions**:
- Increase timeout in `.env.n8n`:
  ```
  EXECUTIONS_TIMEOUT=7200
  EXECUTIONS_TIMEOUT_MAX=14400
  ```
- Check if external service is slow
- Add timeout to HTTP Request nodes
- Use "Wait" node for long operations

#### 5. High Memory Usage

**Symptoms**: n8n container crashes or restarts

**Solutions**:
- Increase Node.js memory:
  ```
  NODE_OPTIONS=--max-old-space-size=4096
  ```
- Reduce concurrent executions:
  ```
  N8N_CONCURRENCY_PRODUCTION_LIMIT=5
  ```
- Enable data pruning:
  ```
  EXECUTIONS_DATA_PRUNE=true
  EXECUTIONS_DATA_MAX_AGE=168
  ```

### Logs and Debugging

**View all logs:**
```bash
docker-compose -f docker-compose.n8n.yml logs -f
```

**View n8n logs only:**
```bash
docker-compose -f docker-compose.n8n.yml logs -f n8n
```

**View database logs:**
```bash
docker-compose -f docker-compose.n8n.yml logs -f postgres
```

**Enable debug mode:**
```bash
# In .env.n8n
N8N_LOG_LEVEL=debug
```

### Database Queries

**Check workflow status:**
```sql
docker-compose -f docker-compose.n8n.yml exec postgres psql -U n8n -d n8n -c "
  SELECT id, name, active, created_at FROM workflow_entity ORDER BY created_at DESC LIMIT 10;
"
```

**Check recent executions:**
```sql
docker-compose -f docker-compose.n8n.yml exec postgres psql -U n8n -d n8n -c "
  SELECT id, workflow_id, mode, finished, started_at FROM execution_entity ORDER BY started_at DESC LIMIT 20;
"
```

---

## Best Practices

### 1. Error Handling

**Always add error workflows:**
- Catch errors with "Error Trigger" node
- Log errors to database
- Send alerts to Slack/email
- Retry failed operations

**Example error handler:**
```json
{
  "node": "Error Trigger",
  "action": "Log to database",
  "then": "Send Slack notification",
  "retry": "Original workflow after 5 minutes"
}
```

### 2. Testing

**Test workflows before activation:**
1. Use manual trigger for testing
2. Test with sample data
3. Verify all branches
4. Check error handling
5. Monitor first 10 executions

### 3. Credentials Management

**Security best practices:**
- Never commit credentials to Git
- Use environment variables
- Rotate API keys regularly
- Use separate credentials for dev/prod
- Enable credential encryption

### 4. Performance Optimization

**For high-volume workflows:**
- Use batch processing (50-100 items)
- Add delays between API calls
- Implement queue system
- Use Redis for caching
- Monitor execution times

### 5. Monitoring

**Set up monitoring:**
- Enable n8n metrics (Prometheus)
- Track execution success rate
- Monitor webhook response times
- Set up alerts for failures
- Review logs daily

**Metrics endpoint:**
```bash
curl http://localhost:5678/metrics
```

### 6. Backup Strategy

**Regular backups:**
```bash
# Backup workflows
docker-compose -f docker-compose.n8n.yml exec n8n n8n export:workflow --all --output=/backup

# Backup database
docker-compose -f docker-compose.n8n.yml exec postgres pg_dump -U n8n n8n > backup_$(date +%Y%m%d).sql

# Backup credentials (encrypted)
docker-compose -f docker-compose.n8n.yml exec n8n n8n export:credentials --all --output=/backup
```

**Automated backup script:**
```bash
# Add to cron: 0 2 * * * /path/to/backup_n8n.sh
./scripts/backup_n8n.sh
```

### 7. Versioning Workflows

**Version control best practices:**
- Export workflows to JSON
- Commit to Git repository
- Tag releases (v1.0, v1.1, etc.)
- Document changes in workflow notes
- Test before deploying to production

### 8. Scaling

**For production scaling:**
- Use n8n queue mode (separate workers)
- Deploy multiple n8n instances
- Use external Redis for queue
- Implement rate limiting
- Use webhook authentication

---

## API Integration

### CraigLeads Pro API Credentials

1. **Add Credential in n8n:**
   - Go to "Credentials" menu
   - Click "New"
   - Select "CraigLeads Pro API"
   - Enter API URL and API Key

2. **Generate API Key:**
```bash
# In backend
curl -X POST http://localhost:8000/api/v1/auth/api-keys \
  -H "Authorization: Bearer YOUR_JWT" \
  -d '{"name": "n8n Integration"}'
```

### Webhook Authentication

**Secure webhooks with tokens:**
```javascript
// In webhook node
if (headers['x-webhook-token'] !== 'your_secret_token') {
  return { error: 'Unauthorized' };
}
```

---

## Advanced Features

### 1. Conditional Workflows

**Use IF nodes for branching:**
```json
{
  "condition": "{{$json.score}} > 80",
  "true": "Auto-approve path",
  "false": "Manual review path"
}
```

### 2. Loops and Iterations

**Process multiple items:**
```json
{
  "node": "Split In Batches",
  "batchSize": 10,
  "options": {
    "reset": false
  }
}
```

### 3. Sub-Workflows

**Call other workflows:**
```json
{
  "node": "Execute Workflow",
  "workflowId": "lead-scoring-workflow",
  "input": "{{$json}}"
}
```

### 4. Scheduled Workflows

**Cron expressions:**
- Every hour: `0 * * * *`
- Daily at 9 AM: `0 9 * * *`
- Every Monday: `0 0 * * 1`
- First of month: `0 0 1 * *`

### 5. Custom Functions

**Use Function nodes:**
```javascript
// Transform lead data
const items = $input.all();
return items.map(item => ({
  json: {
    ...item.json,
    full_name: `${item.json.business_name} - ${item.json.location}`,
    priority: item.json.score > 80 ? 'high' : 'normal'
  }
}));
```

---

## Support and Resources

### Documentation
- n8n Official Docs: https://docs.n8n.io
- CraigLeads Pro API Docs: `/backend/API_TECHNICAL_REFERENCE.md`

### Community
- n8n Community: https://community.n8n.io
- CraigLeads Pro GitHub: [Repository URL]

### Getting Help
1. Check this README
2. Review workflow logs
3. Check n8n community forum
4. Open GitHub issue

---

## Appendix

### Useful Commands

```bash
# Start n8n
./scripts/start_n8n.sh

# Stop n8n
./scripts/stop_n8n.sh

# View logs
docker-compose -f docker-compose.n8n.yml logs -f n8n

# Restart n8n
docker-compose -f docker-compose.n8n.yml restart n8n

# Execute workflow manually
docker-compose -f docker-compose.n8n.yml exec n8n n8n execute --id=1

# Export all workflows
docker-compose -f docker-compose.n8n.yml exec n8n n8n export:workflow --all --output=/backup

# Import workflow
docker-compose -f docker-compose.n8n.yml exec n8n n8n import:workflow --input=/backup/workflow.json

# Database backup
docker-compose -f docker-compose.n8n.yml exec postgres pg_dump -U n8n n8n > backup.sql

# Database restore
docker-compose -f docker-compose.n8n.yml exec -T postgres psql -U n8n n8n < backup.sql

# Check n8n version
docker-compose -f docker-compose.n8n.yml exec n8n n8n --version

# Update n8n
docker-compose -f docker-compose.n8n.yml pull n8n
docker-compose -f docker-compose.n8n.yml up -d n8n
```

### Environment Variables Reference

See `.env.n8n` for complete list of configuration options.

### Workflow Templates

All workflow templates are in `/n8n/workflows/` directory:
- `lead-processing-pipeline.json`
- `demo-generation-workflow.json`
- `video-creation-workflow.json`
- `email-outreach-workflow.json`
- `follow-up-campaign.json`

---

**Last Updated**: 2024-01-15
**Version**: 1.0.0
**Author**: CraigLeads Pro Team
