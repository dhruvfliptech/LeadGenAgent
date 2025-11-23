# n8n Workflow Documentation

Complete documentation for all n8n automation workflows in the Craigslist Lead Generation System.

## Table of Contents

- [Overview](#overview)
- [Workflow Architecture](#workflow-architecture)
- [Workflows](#workflows)
  - [1. Master Lead Processing](#1-master-lead-processing)
  - [2. Quick Demo Workflow](#2-quick-demo-workflow)
  - [3. Video-Only Workflow](#3-video-only-workflow)
  - [4. Bulk Processing](#4-bulk-processing)
  - [5. Error Handling & Retry](#5-error-handling--retry)
  - [6. Analytics & Reporting](#6-analytics--reporting)
  - [7. Lead Nurturing](#7-lead-nurturing)
  - [8. A/B Testing](#8-ab-testing)
- [Workflow Management](#workflow-management)
- [Error Handling](#error-handling)
- [Performance Optimization](#performance-optimization)
- [Monitoring & Alerts](#monitoring--alerts)
- [Testing](#testing)

---

## Overview

The n8n workflow automation system orchestrates the entire lead-to-customer pipeline, from initial lead scraping through demo creation, video generation, and personalized outreach.

### Key Features

- **Automated Pipeline**: End-to-end automation from lead to contact
- **Approval Gates**: Human oversight at critical decision points
- **Error Recovery**: Automatic retry logic with intelligent error categorization
- **Scalability**: Handle 100+ leads/day with batch processing
- **Monitoring**: Real-time tracking and daily reports
- **A/B Testing**: Continuous optimization of outreach strategies

### System Requirements

- n8n v1.0+ (self-hosted or cloud)
- Backend API running on port 8000
- PostgreSQL database for persistence
- Valid API credentials for:
  - OpenAI (GPT-4)
  - ElevenLabs (voice generation)
  - Loom (video hosting)
  - Gmail/SMTP (email sending)
  - Vercel (demo deployment)

---

## Workflow Architecture

### Data Flow

```
Lead Scraped → Quality Filter → Analysis → Improvement Plan
                                              ↓
                                        [APPROVAL GATE 1]
                                              ↓
Demo Creation → Deployment → Video Generation
                                ↓
                          [APPROVAL GATE 2]
                                ↓
                    Email Outreach → Tracking
```

### Workflow Types

1. **Event-Driven**: Triggered by webhooks (lead scraped, demo completed)
2. **Scheduled**: Run on cron schedules (daily reports, nurturing)
3. **Manual**: Manually triggered for testing or one-off operations

### Integration Points

- **Backend API**: Primary integration for all data operations
- **Database**: Direct logging via API
- **External Services**: AI, video, email services
- **Monitoring**: Metrics and alerts

---

## Workflows

### 1. Master Lead Processing

**File**: `master-lead-processing.json`

#### Purpose

Complete end-to-end lead processing with human approval gates at critical stages.

#### Trigger

- **Type**: Webhook
- **Path**: `/webhook/lead-scraped`
- **Payload**:
  ```json
  {
    "lead_id": 123,
    "quality_score": 85
  }
  ```

#### Workflow Steps

1. **Webhook Trigger**: Receive lead_scraped event
2. **Get Lead Details**: Fetch complete lead data from API
3. **Quality Filter**: Filter leads with score > 70
4. **Analyze Website**: AI analysis of current website
5. **Generate Improvement Plan**: Create tailored improvement recommendations
6. **APPROVAL GATE 1**: Wait for human approval of plan
7. **Build Demo Site**: Create improved demo site
8. **Wait for Deployment**: Poll deployment status
9. **APPROVAL GATE 2**: Review deployed demo
10. **Generate Video Script**: AI-generated personalized script
11. **Generate Voiceover**: Text-to-speech with ElevenLabs
12. **Record Screen**: Automated browser recording of demo
13. **Compose Video**: Merge audio + video
14. **Upload to Loom**: Host video for sharing
15. **APPROVAL GATE 3**: Final video review
16. **Send Email**: Personalized outreach with demo + video
17. **Update Lead Status**: Mark as contacted
18. **Log Completion**: Record execution metrics

#### Node Configuration

**Quality Filter Node**:
```json
{
  "conditions": {
    "number": [
      {
        "value1": "={{$json.quality_score}}",
        "operation": "larger",
        "value2": 70
      }
    ]
  }
}
```

**Approval Gate Node**:
```json
{
  "parameters": {
    "httpMethod": "POST",
    "path": "approve-plan-{{$json.lead_id}}",
    "responseMode": "lastNode"
  }
}
```

#### Error Handling

- All HTTP nodes have retry enabled (3 attempts)
- Exponential backoff between retries
- Errors logged to database
- Failed executions trigger error handling workflow

#### Performance Metrics

- **Average Duration**: 15-20 minutes (with approvals)
- **Success Rate Target**: >95%
- **Throughput**: 20-30 leads/day
- **Resource Usage**: Medium (AI + video processing)

#### Customization Options

1. **Adjust Quality Threshold**: Modify quality filter value
2. **Skip Approval Gates**: Set auto_approve flag
3. **Change Voice Style**: Modify voiceover parameters
4. **Email Template**: Select different template

#### Monitoring

- Track execution duration per lead
- Monitor approval wait times
- Alert on failures > 3 consecutive
- Daily summary of processed leads

---

### 2. Quick Demo Workflow

**File**: `quick-demo-workflow.json`

#### Purpose

High-speed lead processing without approval gates for pre-qualified leads.

#### Trigger

- **Type**: Webhook
- **Path**: `/webhook/quick-demo`
- **Payload**:
  ```json
  {
    "lead_id": 123
  }
  ```

#### Key Differences from Master Workflow

- No approval gates
- Parallel video processing (voiceover + recording)
- Auto-approval enabled
- Optimized for speed

#### Workflow Steps

1. Webhook Trigger
2. Get Lead Details
3. Analyze Website
4. Generate Plan
5. Build Demo (auto-approve)
6. Wait for Demo Build
7. Generate Script
8. **[PARALLEL]** Voiceover + Screen Recording
9. Merge Video Assets
10. Compose Video
11. Upload Video
12. Send Email
13. Update Status
14. Log Completion

#### Performance Metrics

- **Average Duration**: 8-12 minutes
- **Success Rate Target**: >98%
- **Throughput**: 50+ leads/day
- **Resource Usage**: High (parallel processing)

#### Use Cases

- High-quality leads (score > 85)
- Bulk processing campaigns
- Time-sensitive outreach
- Proven industry templates

---

### 3. Video-Only Workflow

**File**: `video-only-workflow.json`

#### Purpose

Generate video for existing demo sites (when demo already exists).

#### Trigger

- **Type**: Webhook
- **Path**: `/webhook/video-only`
- **Payload**:
  ```json
  {
    "demo_id": 456
  }
  ```

#### Workflow Steps

1. Webhook Trigger
2. Get Demo Site Details
3. Get Lead Details
4. Generate Video Script
5. Generate Voiceover
6. Record Screen Demo
7. Compose Final Video
8. Upload to Loom
9. Send Email with Video
10. Update Lead Status
11. Log Completion

#### Performance Metrics

- **Average Duration**: 5-8 minutes
- **Success Rate Target**: >99%
- **Throughput**: 100+ videos/day
- **Resource Usage**: Medium (video only)

#### Use Cases

- Demo already exists, need video
- Re-record video with new voice
- Update video for existing leads
- A/B test different video styles

---

### 4. Bulk Processing

**File**: `bulk-processing.json`

#### Purpose

Process multiple leads in batches with optimized resource usage and rate limiting.

#### Trigger

- **Type**: Scheduled
- **Schedule**: Daily at 9:00 AM (0 9 * * *)
- **Cron**: `0 9 * * *`

#### Workflow Steps

1. **Daily Trigger**: Runs at 9am
2. **Get Pending Leads**: Fetch up to 100 qualified leads
3. **Split into Batches**: 10 leads per batch
4. **Set Batch Info**: Track batch number and size
5. **Prepare Leads**: Format data for processing
6. **Analyze Websites (Batch)**: Process 5 at a time
7. **Generate Plans (Batch)**: Process 5 at a time
8. **Create Demo Sites**: Sequential processing
9. **Wait for Demos**: 60 second wait for deployments
10. **Generate Video Scripts**: Batch of 3
11. **Create Complete Videos**: Full video pipeline
12. **Send Emails**: Rate-limited, 10 per batch with 5s delay
13. **Update Lead Statuses**: Mark all as contacted
14. **Aggregate Batch Results**: Calculate success metrics
15. **Check More Batches**: Loop if more leads exist
16. **Wait Between Batches**: 30 second cooldown
17. **Generate Daily Report**: Comprehensive summary
18. **Save Report**: Store in database
19. **Email Report to Admin**: Send summary email

#### Batching Strategy

```javascript
// Batch size configuration
{
  "analysis": 5 concurrent,
  "plans": 5 concurrent,
  "demos": 1 at a time (resource intensive),
  "videos": 1 at a time,
  "emails": 10 per batch, 5s delay
}
```

#### Performance Metrics

- **Average Duration**: 2-3 hours for 100 leads
- **Success Rate Target**: >90%
- **Throughput**: 100 leads/day
- **Resource Usage**: Very High

#### Rate Limiting

- **API Calls**: Batched with delays
- **Email Sending**: 10/batch with 5s delay = 2 per second
- **Video Generation**: 1 at a time (GPU intensive)
- **Demo Builds**: 1 at a time (CPU intensive)

#### Error Recovery

- Failed leads are retried individually
- Batch continues even if some leads fail
- Failed leads logged for manual review
- Automatic retry next day

---

### 5. Error Handling & Retry

**File**: `error-handling.json`

#### Purpose

Monitor failed workflow executions and automatically retry retriable errors.

#### Trigger

- **Type**: Scheduled
- **Schedule**: Every hour (0 * * * *)
- **Cron**: `0 * * * *`

#### Workflow Steps

1. **Hourly Check**: Runs every hour
2. **Get Failed Executions**: Query n8n API for errors
3. **Filter Last 24h**: Only recent failures
4. **Check Has Failures**: Skip if none found
5. **Categorize Errors**: Classify by error type
6. **Check Retriable**: Determine if retry is safe
7. **Wait Before Retry**: Exponential backoff
8. **Retry Execution**: Re-run failed workflow
9. **Log Retry**: Record retry attempt
10. **Prepare Admin Alert**: For non-retriable errors
11. **Send Alert to Admin**: API notification
12. **Email Alert**: Send email to admin
13. **Merge Results**: Combine retry + alert results
14. **Calculate Metrics**: Aggregate statistics
15. **Update Metrics**: Store in database

#### Error Categorization

```javascript
{
  "network": { retriable: true, delay: 60s },
  "rate_limit": { retriable: true, delay: 300s },
  "server_error": { retriable: true, delay: 60s },
  "auth_error": { retriable: false },
  "validation_error": { retriable: false },
  "not_found": { retriable: false }
}
```

#### Retry Logic

- **Max Retries**: 3 attempts
- **Backoff**: 60s, 120s, 240s
- **Rate Limit Backoff**: 5 minutes
- **Skip if**: Already retried 3 times

#### Alert Conditions

- Non-retriable error detected
- 3+ consecutive failures for same workflow
- Critical workflow failure
- Execution timeout

#### Performance Metrics

- **Retry Success Rate**: >70%
- **Alert Response Time**: <5 minutes
- **False Positive Rate**: <5%

---

### 6. Analytics & Reporting

**File**: `analytics-reporting.json`

#### Purpose

Generate daily performance reports with comprehensive metrics and email to admin.

#### Trigger

- **Type**: Scheduled
- **Schedule**: Daily at 9:00 AM (0 9 * * *)
- **Cron**: `0 9 * * *`

#### Metrics Collected

**Lead Metrics**:
- Leads scraped
- Qualified leads
- Processed leads
- Conversion rate

**Demo Metrics**:
- Demos created
- Demos deployed
- Average build time
- Success rate

**Video Metrics**:
- Videos generated
- Videos uploaded
- Average duration
- Total views

**Email Metrics**:
- Emails sent
- Open rate
- Click rate
- Response rate

#### Report Format

```javascript
{
  "date": "2025-01-15",
  "leads": {
    "scraped": 150,
    "qualified": 120,
    "processed": 100,
    "conversion_rate": 83.3
  },
  "demos": {
    "created": 95,
    "deployed": 92,
    "avg_build_time": 180,
    "success_rate": 96.8
  },
  "videos": {
    "generated": 90,
    "uploaded": 88,
    "avg_duration": 65,
    "views": 1250
  },
  "emails": {
    "sent": 88,
    "opened": 62,
    "clicked": 28,
    "replied": 12,
    "open_rate": 70.5,
    "click_rate": 31.8,
    "response_rate": 13.6
  },
  "roi": {
    "total_contacted": 100,
    "responses": 12,
    "response_rate": "12.00%"
  }
}
```

#### HTML Email Template

- Professional HTML layout
- Color-coded metrics
- Responsive design
- Tables and charts
- Executive summary
- Attached JSON report

---

### 7. Lead Nurturing

**File**: `lead-nurturing.json`

#### Purpose

Automatically follow up with leads who haven't responded to initial outreach.

#### Trigger

- **Type**: Scheduled
- **Schedule**: Every 3 days at 10:00 AM
- **Cron**: `0 10 */3 * *`

#### Follow-up Strategy

```
Day 0:  Initial outreach (from main workflow)
Day 3:  First follow-up (gentle reminder)
Day 7:  Second follow-up (value emphasis)
Day 14: Final follow-up (last chance)
Day 15: Mark as cold
```

#### Workflow Steps

1. **Every 3 Days Trigger**: Runs every 3 days
2. **Get Contacted Leads**: Query leads with no response
3. **Calculate Days Since Contact**: Determine follow-up type
4. **Route by Follow-up Type**: Branch based on days
5. **Send First Follow-up**: Day 3-6 leads
6. **Send Second Follow-up**: Day 7-13 leads
7. **Send Final Follow-up**: Day 14+ leads
8. **Update Lead Status**: Record follow-up
9. **Mark as Cold**: After final attempt
10. **Merge Results**: Combine all branches
11. **Summarize Results**: Generate summary

#### Email Templates

**First Follow-up**:
- Subject: "Following up on your website demo"
- Tone: Friendly reminder
- CTA: "Have you had a chance to review?"

**Second Follow-up**:
- Subject: "Last chance to see your custom demo"
- Tone: Value emphasis
- CTA: "This demo could increase your conversions by 40%"

**Final Follow-up**:
- Subject: "Keeping this available for you"
- Tone: Final offer
- CTA: "We'll keep your demo live for 7 more days"

#### Performance Metrics

- **Follow-up Response Rate**: 5-10%
- **Best Performing**: Second follow-up (day 7)
- **Unsubscribe Rate**: <1%

---

### 8. A/B Testing

**File**: `ab-testing.json`

#### Purpose

Test different variations of demos, videos, and emails to optimize conversion rates.

#### Trigger

- **Type**: Webhook
- **Path**: `/webhook/ab-test-lead`
- **Payload**:
  ```json
  {
    "lead_id": 123
  }
  ```

#### Test Variations

**Variant A**: Professional voice, formal tone
**Variant B**: Casual voice, conversational tone

#### Workflow Steps

1. **A/B Test Trigger**: Receive lead assignment
2. **Get Lead Details**: Fetch lead data
3. **Assign Test Variant**: Random 50/50 split
4. **Save Variant Assignment**: Record in database
5. **Route by Variant**: Branch A or B
6. **Variant A**: Professional voice generation
7. **Variant B**: Casual voice generation
8. **Merge Variants**: Combine branches
9. **Complete Video Creation**: Finish video
10. **Send Email**: Personalized outreach
11. **Track Test Event**: Log email sent

#### Statistical Tracking

```javascript
{
  "variant": "A",
  "metrics": {
    "email_opened": true,
    "email_clicked": true,
    "replied": false,
    "video_views": 3,
    "video_watch_duration": 45,
    "demo_visits": 2,
    "demo_time_spent": 120
  }
}
```

#### Test Parameters

- **Voice Style**: Professional vs Casual
- **Email Subject**: Direct vs Curiosity
- **Video Length**: 60s vs 90s
- **CTA Position**: Top vs Bottom
- **Demo Design**: Modern vs Classic

#### Analysis

Run for minimum 50 leads per variant before drawing conclusions.

Expected metrics:
- Open rate difference > 5% = significant
- Click rate difference > 3% = significant
- Response rate difference > 2% = significant

---

## Workflow Management

### Importing Workflows

```bash
# Import single workflow
python scripts/n8n_workflow_manager.py \
  --url http://localhost:5678 \
  --api-key YOUR_API_KEY \
  import n8n/workflows/master-lead-processing.json

# Import all workflows
python scripts/n8n_workflow_manager.py \
  --url http://localhost:5678 \
  --api-key YOUR_API_KEY \
  import-all n8n/workflows/
```

### Activating Workflows

```bash
# Activate specific workflow
python scripts/n8n_workflow_manager.py \
  --url http://localhost:5678 \
  --api-key YOUR_API_KEY \
  activate WORKFLOW_ID

# Activate all production workflows
python scripts/n8n_workflow_manager.py \
  --url http://localhost:5678 \
  --api-key YOUR_API_KEY \
  activate-all --tag production
```

### Exporting Workflows

```bash
# Export all workflows (backup)
python scripts/n8n_workflow_manager.py \
  --url http://localhost:5678 \
  --api-key YOUR_API_KEY \
  export-all backups/workflows/
```

---

## Error Handling

### Global Error Workflow

All workflows except error-handling.json reference the error-handling workflow in their settings:

```json
{
  "settings": {
    "errorWorkflow": "error-handling"
  }
}
```

### Node-Level Error Handling

```json
{
  "retryOnFail": true,
  "maxTries": 3,
  "waitBetweenTries": 5000,
  "continueOnFail": false
}
```

### Error Categorization

Errors are automatically categorized and handled appropriately:

1. **Network Errors**: Auto-retry with backoff
2. **Rate Limits**: Wait and retry
3. **Server Errors (5xx)**: Retry
4. **Auth Errors (401/403)**: Alert admin, no retry
5. **Validation Errors (400)**: Alert admin, no retry
6. **Not Found (404)**: Skip, no retry

---

## Performance Optimization

### Batching

Process multiple items together to reduce overhead:

```json
{
  "options": {
    "batching": {
      "batch": {
        "batchSize": 5,
        "batchInterval": 1000
      }
    }
  }
}
```

### Parallel Execution

Run independent operations in parallel:

```
Script Generation
      ↓
   [SPLIT]
      ↓
Voiceover ← → Screen Recording
      ↓
   [MERGE]
      ↓
Video Composition
```

### Caching

- Cache AI analysis results for similar websites
- Reuse demo templates when appropriate
- Cache video assets for faster composition

### Resource Management

- Limit concurrent video generations
- Stagger heavy operations
- Use rate limiting on API calls
- Implement cooldown periods between batches

---

## Monitoring & Alerts

### Metrics Tracked

1. **Execution Metrics**:
   - Duration
   - Success/failure rate
   - Nodes executed
   - Retry count

2. **Business Metrics**:
   - Leads processed
   - Demos created
   - Videos generated
   - Emails sent
   - Response rate

3. **Performance Metrics**:
   - Average execution time
   - Resource usage
   - API call counts
   - Error rates

### Alert Conditions

- **Critical**: Workflow failure > 3 consecutive
- **High**: Success rate < 80%
- **Medium**: Execution time > 2x average
- **Low**: Warning thresholds

### Dashboard

Access metrics via:
- n8n built-in execution view
- Backend API `/api/workflows/metrics`
- Daily email reports
- Grafana/Prometheus (optional)

---

## Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest requests

# Run all tests
cd n8n/tests
pytest test_workflows.py -v

# Run specific test category
pytest test_workflows.py -k "test_master" -v

# Run integration tests
pytest test_workflows.py -m integration -v
```

### Test Coverage

- Workflow existence checks
- Trigger functionality
- Node connections
- Error handling configuration
- Retry logic
- Authentication setup
- Integration with backend API

### Manual Testing

1. **Trigger Test Lead**:
   ```bash
   curl -X POST http://localhost:5678/webhook/lead-scraped \
     -H "Content-Type: application/json" \
     -d '{"lead_id": 1, "quality_score": 85}'
   ```

2. **Approve Plan**:
   ```bash
   curl -X POST http://localhost:5678/webhook/approve-plan-1 \
     -H "Content-Type: application/json" \
     -d '{"approved": true}'
   ```

3. **Check Execution**:
   ```bash
   python scripts/n8n_workflow_manager.py \
     --url http://localhost:5678 \
     --api-key YOUR_API_KEY \
     stats --workflow-id WORKFLOW_ID
   ```

---

## Best Practices

### 1. Idempotency

Design workflows to be safely retriable:
- Check if operation already completed
- Use unique identifiers
- Handle duplicate requests gracefully

### 2. Error Messages

Provide clear, actionable error messages:
```javascript
{
  "error": "Failed to generate video",
  "reason": "ElevenLabs API rate limit exceeded",
  "action": "Retry in 300 seconds",
  "lead_id": 123
}
```

### 3. Logging

Log at key stages:
- Workflow start
- Major milestones
- Approval decisions
- Errors
- Completion

### 4. Timeout Settings

Set appropriate timeouts:
- API calls: 30-60s
- Video generation: 5-10 minutes
- Demo builds: 5-10 minutes
- Overall workflow: 30 minutes - 2 hours

### 5. Resource Limits

Prevent resource exhaustion:
- Limit concurrent executions
- Use batch processing
- Implement rate limiting
- Add cooldown periods

---

## Troubleshooting

### Common Issues

**Issue**: Workflow not triggering
- Check webhook URL is correct
- Verify workflow is active
- Check n8n logs for errors

**Issue**: Approval gate timeout
- Increase timeout in Wait node
- Check webhook URL is accessible
- Verify approval endpoint is working

**Issue**: Video generation fails
- Check ElevenLabs API credits
- Verify video service is running
- Check file permissions

**Issue**: High failure rate
- Review error logs
- Check API rate limits
- Verify service availability
- Review retry configuration

### Debug Mode

Enable debug mode for detailed logging:
```json
{
  "settings": {
    "saveManualExecutions": true,
    "executionOrder": "v1"
  }
}
```

### Support

For issues:
1. Check n8n execution logs
2. Review backend API logs
3. Check service status
4. Consult error handling workflow logs
5. Contact admin if persistent

---

## Maintenance

### Regular Tasks

**Daily**:
- Review error handling workflow results
- Check success rates
- Monitor resource usage

**Weekly**:
- Review A/B test results
- Analyze performance trends
- Update email templates if needed

**Monthly**:
- Export workflow backups
- Review and optimize slow workflows
- Update documentation
- Analyze ROI metrics

### Updates

When updating workflows:
1. Export current version (backup)
2. Make changes in development environment
3. Test thoroughly
4. Update version number
5. Import to production
6. Monitor first few executions
7. Document changes

---

## Appendix

### Environment Variables

Required environment variables for workflows:

```bash
# n8n Configuration
N8N_URL=http://localhost:5678
N8N_API_KEY=your_api_key

# Backend API
API_BASE_URL=http://localhost:8000

# Email
ADMIN_EMAIL=admin@example.com

# External Services
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
LOOM_API_KEY=...
VERCEL_TOKEN=...
```

### Workflow IDs

Map of workflow names to IDs (update after import):

```
master-lead-processing: workflow-001
quick-demo-workflow: workflow-002
video-only-workflow: workflow-003
bulk-processing: workflow-004
error-handling: workflow-005
analytics-reporting: workflow-006
lead-nurturing: workflow-007
ab-testing: workflow-008
```

### API Endpoints

Key backend API endpoints used by workflows:

```
GET    /api/leads/{id}
PATCH  /api/leads/{id}
POST   /api/ml/analyze-website
POST   /api/ml/generate-improvement-plan
POST   /api/demo-sites/create
GET    /api/demo-sites/{id}/status
POST   /api/video/generate-script
POST   /api/video/generate-voiceover
POST   /api/video/record-screen
POST   /api/video/compose
POST   /api/video/upload-loom
POST   /api/outreach/send-email
POST   /api/workflows/log
POST   /api/ab-tests/track
```

### Changelog

**Version 1.0** (2025-01-15)
- Initial workflow implementation
- 8 production workflows
- Error handling system
- A/B testing framework
- Comprehensive documentation

---

**Last Updated**: 2025-01-15
**Version**: 1.0
**Maintainer**: Craigslist Lead Gen Team
