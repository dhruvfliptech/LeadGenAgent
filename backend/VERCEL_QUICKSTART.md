# Vercel Deployment - Quick Start Guide

Get your demo site deployment up and running in 5 minutes.

## Step 1: Get Vercel API Token (2 minutes)

1. Go to https://vercel.com/account/tokens
2. Click **"Create Token"**
3. Name: `CraigLeads Deployer`
4. Expiration: `No Expiration`
5. Scope: `Full Access` (or at minimum: Read/Write for deployments and projects)
6. Click **"Create"**
7. **Copy the token** (you won't see it again!)

## Step 2: Configure Environment (1 minute)

Add to `/Users/greenmachine2.0/Craigslist/backend/.env`:

```bash
# Minimum required
VERCEL_ENABLED=true
VERCEL_API_TOKEN=vercel_token_you_just_copied

# Optional (use defaults if not set)
VERCEL_TEAM_ID=                              # Only if using team account
VERCEL_MAX_RETRIES=3
VERCEL_TIMEOUT_SECONDS=60
```

## Step 3: Run Database Migration (1 minute)

```bash
cd /Users/greenmachine2.0/Craigslist/backend

# Run migration
psql -U postgres -d craigslist_leads -f migrations/002_add_demo_sites.sql

# Verify tables created
psql -U postgres -d craigslist_leads -c "\dt demo_*"
```

Expected output:
```
              List of relations
 Schema |        Name         | Type  |  Owner
--------+---------------------+-------+----------
 public | demo_sites          | table | postgres
 public | deployment_history  | table | postgres
```

## Step 4: Deploy Your First Site (1 minute)

### Option A: Via API

```bash
curl -X POST http://localhost:8000/api/v1/demo-sites/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": 1,
    "framework": "html",
    "files": {
      "index.html": "<!DOCTYPE html><html><head><title>My Demo</title></head><body><h1>Hello Vercel!</h1><p>This site was deployed automatically!</p></body></html>"
    }
  }'
```

### Option B: Via Python

```python
import asyncio
from app.integrations.vercel_deployer import VercelDeployer

async def deploy():
    deployer = VercelDeployer()

    files = {
        "index.html": """
<!DOCTYPE html>
<html>
<head>
    <title>My First Demo</title>
    <style>
        body {
            font-family: Arial;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: #f0f0f0;
        }
        .card {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>🚀 Demo Site Deployed!</h1>
        <p>This site was automatically deployed to Vercel.</p>
    </div>
</body>
</html>
"""
    }

    result = await deployer.deploy_demo_site(
        files=files,
        framework="html",
        project_name="my-first-demo",
        lead_id=1
    )

    if result.success:
        print(f"✅ Success! Your site is live at:")
        print(f"   {result.url}")
    else:
        print(f"❌ Failed: {result.error_message}")

asyncio.run(deploy())
```

Save as `test_deploy.py` and run:
```bash
python test_deploy.py
```

## Step 5: Check Your Deployment

Visit the URL from the response (e.g., `https://my-first-demo-xxx.vercel.app`)

You should see your demo site live!

---

## What You Get

- ✅ Live site on Vercel's CDN (global distribution)
- ✅ Automatic SSL certificate (HTTPS)
- ✅ Custom domain support (optional)
- ✅ Deployment tracking in database
- ✅ Cost estimation
- ✅ Analytics ready

---

## Next Steps

### View All Deployments
```bash
curl http://localhost:8000/api/v1/demo-sites
```

### Get Deployment Stats
```bash
curl http://localhost:8000/api/v1/demo-sites/stats/overview?days=30
```

### Deploy a Next.js Site
```bash
# See examples/vercel_deployment_example.py
# Example 2: Next.js deployment
```

### Add Custom Domain
```python
deployer = VercelDeployer()
success, error = await deployer.add_domain(
    project_id="prj_xxx",
    domain="demo.yourdomain.com"
)
```

---

## Common Use Cases

### 1. Deploy Demo for New Lead
```python
# When lead is created, automatically deploy demo
async def on_lead_created(lead):
    files = generate_demo_files(lead)  # Your demo builder
    deployer = VercelDeployer()
    result = await deployer.deploy_demo_site(
        files=files,
        framework="html",
        project_name=f"demo-lead-{lead.id}",
        lead_id=lead.id
    )
    return result.url
```

### 2. Batch Deploy for Multiple Leads
```python
lead_ids = [1, 2, 3, 4, 5]

for lead_id in lead_ids:
    # Deploy site
    # Wait 1 second between deployments (rate limiting)
    await asyncio.sleep(1)
```

### 3. Track Costs
```python
deployer = VercelDeployer()
cost = deployer.estimate_cost(
    files_count=20,
    total_size_bytes=1_000_000,
    estimated_page_views=5_000,
    estimated_build_minutes=2
)
print(f"Estimated monthly cost: ${cost['total_estimated_cost']:.2f}")
```

---

## Troubleshooting

### "Authentication failed"
- Check `VERCEL_API_TOKEN` in `.env`
- Get new token from https://vercel.com/account/tokens

### "Deployment timeout"
- Normal for large sites (can take up to 10 minutes)
- Check Vercel dashboard for build progress

### "Rate limit exceeded"
- Wait 1 minute and try again
- Reduce concurrent deployments

---

## Documentation

- **Full Guide**: `VERCEL_DEPLOYMENT_INTEGRATION.md`
- **Examples**: `examples/vercel_deployment_example.py`
- **Summary**: `VERCEL_DEPLOYMENT_SUMMARY.md`
- **API Reference**: OpenAPI docs at `http://localhost:8000/docs`

---

## Support

For issues:
1. Check logs: `tail -f logs/app.log`
2. Query database: `SELECT * FROM demo_sites ORDER BY created_at DESC LIMIT 10`
3. Check Vercel dashboard: https://vercel.com/dashboard
4. Review examples: `examples/vercel_deployment_example.py`

---

**That's it! You're ready to deploy demo sites to Vercel automatically!** 🚀
