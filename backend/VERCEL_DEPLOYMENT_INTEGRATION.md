# Vercel Deployment Integration - Phase 3, Task 4

## Overview

Complete Vercel API integration for automatically deploying demo sites to Vercel from the Craigslist Lead Generation System. This integration allows you to deploy HTML, React, Next.js, Vue, and Svelte demo sites programmatically and track their deployment status, costs, and analytics.

## Architecture

### Components Created

1. **Database Models** (`app/models/demo_sites.py`)
   - `DemoSite`: Main model for tracking Vercel deployments
   - `DeploymentHistory`: Audit log for deployment events
   - `DeploymentStatus`: Enum for deployment states
   - `DeploymentFramework`: Enum for supported frameworks

2. **Vercel API Client** (`app/integrations/vercel_deployer.py`)
   - `VercelDeployer`: Main API client with authentication
   - `VercelRateLimiter`: Rate limiting (20 req/sec)
   - `DeploymentResult`: Structured deployment results
   - Full CRUD operations for projects and deployments

3. **API Endpoints** (`app/api/endpoints/demo_sites.py`)
   - `POST /api/v1/demo-sites/deploy`: Deploy a new demo site
   - `GET /api/v1/demo-sites/{id}`: Get deployment status
   - `GET /api/v1/demo-sites/lead/{lead_id}`: Get demos for a lead
   - `DELETE /api/v1/demo-sites/{id}`: Delete a deployment
   - `POST /api/v1/demo-sites/{id}/redeploy`: Redeploy (placeholder)
   - `GET /api/v1/demo-sites`: List all deployments with filters
   - `GET /api/v1/demo-sites/stats/overview`: Deployment analytics

4. **Database Migration** (`migrations/002_add_demo_sites.sql`)
   - SQL migration for creating tables and indexes
   - Automatic timestamp updates via trigger
   - Comprehensive indexing for performance

## Features

### Deployment Capabilities

- **Multi-Framework Support**: HTML, React, Next.js, Vue, Svelte
- **Automatic Project Creation**: Creates Vercel projects programmatically
- **Environment Variables**: Configure deployment environment
- **Custom Domains**: Optional custom domain support
- **SSL Certificates**: Automatic SSL via Vercel
- **CDN Distribution**: Global CDN through Vercel's edge network
- **Regional Deployment**: Deploy to multiple regions

### Tracking & Analytics

- **Build Metrics**: Build time, file count, total size
- **Performance Metrics**: Page views, unique visitors, bandwidth
- **Cost Tracking**: Estimated and actual deployment costs
- **Deployment History**: Complete audit trail
- **Status Monitoring**: Real-time deployment status

### Error Handling

- **Retry Logic**: Automatic retry with exponential backoff
- **Rate Limiting**: Respects Vercel's 20 req/sec limit
- **Timeout Handling**: Configurable timeouts
- **Error Logging**: Comprehensive error messages
- **Graceful Degradation**: Soft deletes and error states

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Vercel Deployment Settings
VERCEL_ENABLED=true
VERCEL_API_TOKEN=your_vercel_api_token_here
VERCEL_TEAM_ID=                              # Optional: for team accounts
VERCEL_MAX_RETRIES=3
VERCEL_TIMEOUT_SECONDS=60
VERCEL_RATE_LIMIT_PER_SECOND=20
VERCEL_MAX_DEPLOYMENT_WAIT_TIME=600          # 10 minutes
VERCEL_POLL_INTERVAL=5                       # Check status every 5s

# Vercel Cost Tracking
VERCEL_MONTHLY_BASE_COST=20.0                # Pro plan default
VERCEL_BANDWIDTH_INCLUDED_GB=100
VERCEL_BUILD_MINUTES_INCLUDED=6000
VERCEL_ADDITIONAL_BANDWIDTH_COST_PER_100GB=40.0
VERCEL_ADDITIONAL_BUILD_MINUTES_COST_PER_500MIN=8.0
```

### Getting a Vercel API Token

1. Go to https://vercel.com/account/tokens
2. Click "Create Token"
3. Name it (e.g., "CraigLeads Demo Deployer")
4. Set expiration (recommend: No Expiration for production)
5. Select scopes (needs: Read/Write deployments, projects)
6. Copy the token and add to `.env`

### Team Accounts (Optional)

If using a Vercel team account:

1. Get your Team ID from https://vercel.com/teams/your-team/settings
2. Add `VERCEL_TEAM_ID=team_xxxxx` to `.env`

## Database Setup

Run the migration to create the required tables:

```bash
# Using psql
psql -U postgres -d craigslist_leads -f backend/migrations/002_add_demo_sites.sql

# Or using your migration tool
python manage.py migrate
```

### Tables Created

**demo_sites**:
- Stores deployment information
- Tracks Vercel project/deployment IDs
- Contains URLs, status, build metrics
- Includes cost and analytics data

**deployment_history**:
- Audit log for all deployment events
- Tracks status changes
- Stores error details
- Enables deployment analytics

## API Usage

### 1. Deploy a Demo Site

```bash
POST /api/v1/demo-sites/deploy
Content-Type: application/json

{
  "lead_id": 123,
  "framework": "nextjs",
  "project_name": "demo-lead-123",
  "files": {
    "index.html": "<html>...</html>",
    "styles.css": "body { margin: 0; }",
    "package.json": "{...}",
    "pages/index.js": "export default function Home() { ... }"
  },
  "env_vars": {
    "NEXT_PUBLIC_API_URL": "https://api.example.com",
    "NODE_ENV": "production"
  },
  "custom_domain": "demo-lead-123.yourdomain.com"
}
```

**Response**:
```json
{
  "id": 1,
  "lead_id": 123,
  "vercel_project_id": "prj_abc123",
  "vercel_deployment_id": "dpl_xyz789",
  "project_name": "demo-lead-123",
  "framework": "nextjs",
  "url": "https://demo-lead-123.vercel.app",
  "preview_url": "https://demo-lead-123-git-main.vercel.app",
  "status": "ready",
  "build_time": 45.2,
  "created_at": "2025-11-04T18:00:00Z",
  "deployed_at": "2025-11-04T18:01:30Z",
  "error_message": null
}
```

### 2. Get Deployment Status

```bash
GET /api/v1/demo-sites/1
```

**Response**:
```json
{
  "id": 1,
  "lead_id": 123,
  "status": "ready",
  "url": "https://demo-lead-123.vercel.app",
  "build_time": 45.2,
  ...
}
```

### 3. List Deployments for a Lead

```bash
GET /api/v1/demo-sites/lead/123?page=1&page_size=20
```

**Response**:
```json
{
  "total": 5,
  "page": 1,
  "page_size": 20,
  "deployments": [
    {
      "id": 1,
      "status": "ready",
      "url": "https://demo-lead-123.vercel.app",
      ...
    }
  ]
}
```

### 4. Get Deployment Statistics

```bash
GET /api/v1/demo-sites/stats/overview?days=30
```

**Response**:
```json
{
  "total_deployments": 150,
  "active_deployments": 145,
  "failed_deployments": 5,
  "total_page_views": 12450,
  "total_bandwidth_gb": 15.8,
  "estimated_monthly_cost": 20.0,
  "deployments_by_status": {
    "ready": 145,
    "error": 5
  },
  "deployments_by_framework": {
    "nextjs": 80,
    "react": 45,
    "html": 25
  }
}
```

### 5. Delete a Deployment

```bash
# Soft delete (default)
DELETE /api/v1/demo-sites/1

# Permanent delete (also removes from Vercel)
DELETE /api/v1/demo-sites/1?permanent=true
```

**Response**:
```json
{
  "message": "Deployment deleted successfully",
  "id": 1,
  "permanent": true
}
```

### 6. List All Deployments with Filters

```bash
GET /api/v1/demo-sites?page=1&page_size=20&status=ready&framework=nextjs
```

## Integration with Demo Builder (Task 3)

Combine the demo builder from Task 3 with this deployment integration:

```python
from app.services.demo_builder import DemoBuilder
from app.integrations.vercel_deployer import VercelDeployer

# 1. Generate demo site files
builder = DemoBuilder()
demo_data = await builder.build_demo_site(
    lead=lead,
    template="professional",
    framework="nextjs"
)

# 2. Deploy to Vercel
deployer = VercelDeployer()
result = await deployer.deploy_demo_site(
    files=demo_data["files"],
    framework="nextjs",
    project_name=f"demo-lead-{lead.id}",
    lead_id=lead.id,
    env_vars={
        "NEXT_PUBLIC_LEAD_ID": str(lead.id),
        "NODE_ENV": "production"
    }
)

# 3. Save to database
demo_site = DemoSite(
    lead_id=lead.id,
    vercel_project_id=result.project_id,
    vercel_deployment_id=result.deployment_id,
    url=result.url,
    status=result.status,
    ...
)
db.add(demo_site)
await db.commit()
```

## Cost Estimation

The system tracks deployment costs based on Vercel's Pro plan pricing:

### Vercel Pro Plan ($20/month includes):
- 100GB bandwidth
- 6,000 build minutes
- Unlimited deployments
- Unlimited team members

### Additional Costs:
- Bandwidth: $40 per 100GB over included amount
- Build minutes: $8 per 500 minutes over included amount

### Cost Calculation Example:

```python
deployer = VercelDeployer()

# Estimate costs for a deployment
cost_estimate = deployer.estimate_cost(
    files_count=50,
    total_size_bytes=2_000_000,  # 2MB
    estimated_page_views=1000,   # per month
    estimated_build_minutes=1.0
)

print(cost_estimate)
# {
#   "bandwidth_gb": 2.0,
#   "bandwidth_cost": 0.0,     # Within included 100GB
#   "build_minutes": 1.0,
#   "build_cost": 0.0,         # Within included 6,000 min
#   "total_estimated_cost": 0.0,
#   "monthly_base_cost": 20.0
# }
```

## Rate Limiting

Vercel API limits: **20 requests/second**

The integration automatically handles rate limiting:

```python
class VercelRateLimiter:
    """Ensures we don't exceed 20 req/sec"""

    async def acquire(self):
        # Waits if necessary to stay within limits
        # Uses sliding window algorithm
        pass
```

## Error Handling

### Common Errors

1. **Authentication Error**: Invalid API token
   ```json
   {
     "error": "Invalid Vercel API token"
   }
   ```
   **Fix**: Check `VERCEL_API_TOKEN` in `.env`

2. **Rate Limit Exceeded**: Too many requests
   ```json
   {
     "error": "Rate limit exceeded after retries"
   }
   ```
   **Fix**: Automatic retry with backoff (max 3 retries)

3. **Deployment Timeout**: Build took too long
   ```json
   {
     "error": "Deployment timeout"
   }
   ```
   **Fix**: Increase `VERCEL_MAX_DEPLOYMENT_WAIT_TIME`

4. **Build Error**: Deployment failed
   ```json
   {
     "status": "error",
     "error_message": "Build failed: npm install error"
   }
   ```
   **Fix**: Check build logs in `build_output` field

### Retry Strategy

- **Server Errors (5xx)**: Automatic retry with exponential backoff
- **Rate Limiting (429)**: Wait for `Retry-After` header, then retry
- **Timeout**: Retry up to `max_retries` times
- **Client Errors (4xx)**: No retry (permanent failure)

## Monitoring & Analytics

### Deployment Metrics Tracked

1. **Build Metrics**:
   - Build time (seconds)
   - Files count
   - Total size (bytes)
   - Framework detected

2. **Performance Metrics**:
   - Lambda invocations
   - Bandwidth usage (bytes)
   - Page views
   - Unique visitors
   - Last accessed timestamp

3. **Cost Metrics**:
   - Estimated cost
   - Actual cost (from Vercel billing API)
   - Bandwidth overage
   - Build minutes overage

### Querying Analytics

```sql
-- Top 10 most viewed deployments
SELECT
    id,
    project_name,
    page_views,
    unique_visitors,
    url
FROM demo_sites
WHERE is_deleted = false
ORDER BY page_views DESC
LIMIT 10;

-- Total bandwidth usage this month
SELECT
    SUM(bandwidth_bytes) / (1024 * 1024 * 1024) as total_gb,
    COUNT(*) as deployment_count
FROM demo_sites
WHERE created_at >= DATE_TRUNC('month', NOW());

-- Failed deployments in last 7 days
SELECT
    id,
    project_name,
    error_message,
    created_at
FROM demo_sites
WHERE status = 'error'
  AND created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

## Security Considerations

1. **API Token Security**:
   - Store token in `.env` (never commit)
   - Use environment variables in production
   - Rotate tokens regularly
   - Limit token scopes to minimum required

2. **Soft Deletes**:
   - Default deletion is soft delete
   - Permanent deletion requires `permanent=true` flag
   - Prevents accidental data loss

3. **Authentication**:
   - All API endpoints should be protected
   - Add authentication middleware as needed
   - Consider rate limiting per user

4. **Input Validation**:
   - All inputs validated via Pydantic schemas
   - File content sanitized before deployment
   - Project names validated for Vercel compatibility

## Testing

### Unit Tests

```python
import pytest
from app.integrations.vercel_deployer import VercelDeployer

@pytest.mark.asyncio
async def test_deploy_demo_site():
    deployer = VercelDeployer()

    files = {
        "index.html": "<html><body>Test</body></html>"
    }

    result = await deployer.deploy_demo_site(
        files=files,
        framework="html",
        project_name="test-project",
        lead_id=1
    )

    assert result.success
    assert result.url is not None
    assert result.status == "ready"
```

### Integration Tests

```bash
# Test deployment endpoint
curl -X POST http://localhost:8000/api/v1/demo-sites/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": 1,
    "framework": "html",
    "files": {
      "index.html": "<html><body>Hello Vercel!</body></html>"
    }
  }'
```

## Troubleshooting

### Issue: Deployments stuck in "building" status

**Cause**: Vercel build timeout or status polling stopped

**Solution**:
1. Check Vercel dashboard for build logs
2. Increase `VERCEL_MAX_DEPLOYMENT_WAIT_TIME`
3. Check build output in database

### Issue: High cost estimates

**Cause**: Large files or high traffic

**Solution**:
1. Optimize file sizes (minify, compress)
2. Use CDN caching effectively
3. Monitor bandwidth usage
4. Consider upgrading Vercel plan

### Issue: Rate limit errors

**Cause**: Too many concurrent deployments

**Solution**:
1. Implement deployment queue
2. Reduce concurrent deployment workers
3. Increase `VERCEL_RATE_LIMIT_PER_SECOND` if using team plan

## Future Enhancements

1. **Deployment Queue**: Background job queue for large-scale deployments
2. **Analytics Dashboard**: Real-time deployment analytics UI
3. **Cost Alerts**: Email alerts when costs exceed threshold
4. **A/B Testing**: Deploy multiple versions for testing
5. **Rollback**: Automatic rollback on deployment failure
6. **Webhooks**: Vercel webhook integration for real-time updates
7. **Preview Environments**: Branch-based preview deployments
8. **Build Cache**: Optimize build times with caching

## File Locations

- **Models**: `/Users/greenmachine2.0/Craigslist/backend/app/models/demo_sites.py`
- **Integration**: `/Users/greenmachine2.0/Craigslist/backend/app/integrations/vercel_deployer.py`
- **Endpoints**: `/Users/greenmachine2.0/Craigslist/backend/app/api/endpoints/demo_sites.py`
- **Migration**: `/Users/greenmachine2.0/Craigslist/backend/migrations/002_add_demo_sites.sql`
- **Config**: `/Users/greenmachine2.0/Craigslist/backend/app/core/config.py` (lines 242-257)
- **Router**: `/Users/greenmachine2.0/Craigslist/backend/app/main.py` (lines 29, 388)

## Support

For issues or questions:
1. Check Vercel API documentation: https://vercel.com/docs/rest-api
2. Review deployment logs in database
3. Check application logs: `logs/app.log`
4. Review deployment history: `SELECT * FROM deployment_history`

## License

Part of the Craigslist Lead Generation System - Phase 3, Task 4
