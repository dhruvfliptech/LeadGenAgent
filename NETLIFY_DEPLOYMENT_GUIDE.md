# CraigLeads Pro - Complete Netlify Deployment Guide

Complete guide for deploying CraigLeads Pro to production using Netlify (frontend) and Railway/Render (backend).

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Backend Deployment Options](#backend-deployment-options)
4. [Frontend Deployment (Netlify)](#frontend-deployment-netlify)
5. [Environment Configuration](#environment-configuration)
6. [Custom Domain Setup](#custom-domain-setup)
7. [Team Collaboration](#team-collaboration)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     PRODUCTION ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Frontend (Netlify)          Backend (Railway/Render)       │
│  ┌──────────────────┐       ┌────────────────────────┐     │
│  │   React + Vite   │◄─────►│   FastAPI + Uvicorn    │     │
│  │   Static Files   │ HTTPS │   REST API + WebSocket │     │
│  │   CDN Cached     │       │   Background Workers    │     │
│  └──────────────────┘       └────────────────────────┘     │
│                                      │                       │
│                                      ▼                       │
│                             ┌─────────────────┐             │
│                             │  PostgreSQL DB  │             │
│                             │  Redis Cache    │             │
│                             └─────────────────┘             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Why This Stack?**
- **Netlify**: Best-in-class static hosting, automatic SSL, global CDN, CI/CD
- **Railway/Render**: Managed Python hosting with PostgreSQL, Redis, automatic scaling
- **Separation**: Frontend and backend can scale independently
- **Cost**: Free tiers available for testing, affordable production pricing

---

## Prerequisites

### Required Accounts

1. **GitHub Account** (for code hosting and CI/CD)
   - Sign up: https://github.com/signup

2. **Netlify Account** (for frontend hosting)
   - Sign up: https://app.netlify.com/signup
   - Recommendation: Sign up with GitHub for easier integration

3. **Backend Platform** (choose one):
   - **Railway** (Recommended): https://railway.app/
     - $5/month hobby plan
     - Includes PostgreSQL, Redis
     - Easiest setup
   - **Render**: https://render.com/
     - Free tier available
     - Good for testing
   - **Heroku**: https://heroku.com/
     - Traditional option
     - More expensive

### Required Tools

```bash
# Node.js 18+ (for frontend builds)
node --version  # Should be 18.x or higher

# npm (comes with Node.js)
npm --version   # Should be 9.x or higher

# Git (for version control)
git --version

# Netlify CLI (optional but recommended)
npm install -g netlify-cli
```

### Project Checklist

- [ ] Code pushed to GitHub repository
- [ ] All dependencies listed in package.json and requirements.txt
- [ ] Environment variables documented
- [ ] Database migrations ready
- [ ] API endpoints tested locally
- [ ] Frontend build succeeds locally

---

## Backend Deployment Options

### Option 1: Railway (Recommended)

**Pros:** Easiest setup, includes PostgreSQL + Redis, great DX, automatic HTTPS
**Pricing:** $5/month hobby plan, $20/month pro plan

#### Step-by-Step Railway Deployment

1. **Create Railway Account**
   ```
   Go to: https://railway.app/
   Sign up with GitHub
   ```

2. **Create New Project**
   ```
   Dashboard > New Project > Deploy from GitHub repo
   Select your repository
   Select "backend" as root directory
   ```

3. **Add PostgreSQL Database**
   ```
   Project Dashboard > Add Service > Database > PostgreSQL
   Railway automatically sets DATABASE_URL environment variable
   ```

4. **Add Redis**
   ```
   Project Dashboard > Add Service > Database > Redis
   Railway automatically sets REDIS_URL environment variable
   ```

5. **Configure Environment Variables**
   ```
   Go to your service > Variables tab
   Add all variables from backend/.env.example
   Critical variables:
   - SECRET_KEY (generate with: openssl rand -hex 32)
   - ALLOWED_HOSTS (add your Netlify domain)
   - OPENAI_API_KEY
   - SMTP credentials
   ```

6. **Configure Build Settings**
   ```
   Settings > Build
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4
   ```

7. **Enable Health Checks**
   ```
   Settings > Health Check
   Path: /api/v1/health
   Timeout: 100 seconds
   ```

8. **Deploy**
   ```
   Railway auto-deploys on push to main branch
   Get your URL: something.railway.app
   Test: https://your-app.railway.app/api/v1/health
   ```

9. **Run Database Migrations**
   ```bash
   # In Railway dashboard, open service shell or use CLI
   railway run alembic upgrade head

   # Or connect locally
   railway link
   railway run python create_tables_simple.py
   ```

10. **Enable Playwright (if using scrapers)**
    ```bash
    # In Railway shell
    playwright install
    playwright install-deps
    ```

#### Railway Configuration Files

Railway automatically detects Python projects. The `railway.json` file provides additional configuration:

```json
{
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4",
    "healthcheckPath": "/api/v1/health"
  }
}
```

**Railway CLI Commands**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# Check status
railway status

# View logs
railway logs

# Run migrations
railway run alembic upgrade head

# Open shell
railway shell
```

---

### Option 2: Render

**Pros:** Free tier, good documentation, includes PostgreSQL
**Cons:** Free tier sleeps after inactivity, slower cold starts

#### Step-by-Step Render Deployment

1. **Create Render Account**
   ```
   Go to: https://render.com/
   Sign up with GitHub
   ```

2. **Create New Web Service**
   ```
   Dashboard > New + > Web Service
   Connect your GitHub repository
   Name: craigleads-backend
   Region: Oregon (or closest to you)
   Branch: main
   Root Directory: backend
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4
   ```

3. **Choose Plan**
   ```
   Free tier: Good for testing (sleeps after 15 min inactivity)
   Starter ($7/month): Production-ready, no sleep
   ```

4. **Add PostgreSQL Database**
   ```
   Dashboard > New + > PostgreSQL
   Name: craigleads-db
   Plan: Free or Starter
   Region: Same as web service

   After creation, connect to web service:
   Web Service > Environment > Add from Database
   Select craigleads-db
   ```

5. **Add Redis**
   ```
   Dashboard > New + > Redis
   Name: craigleads-redis
   Plan: Free or Starter

   Connect to web service:
   Copy Redis connection string
   Add to web service environment as REDIS_URL
   ```

6. **Configure Environment Variables**
   ```
   Web Service > Environment
   Add all variables from backend/.env.example
   Use "Add from Database" for DATABASE_URL
   ```

7. **Enable Auto-Deploy**
   ```
   Web Service > Settings
   Auto-Deploy: Yes
   Branch: main
   ```

8. **Run Database Migrations**
   ```bash
   # Use Render Shell
   Dashboard > Web Service > Shell
   alembic upgrade head

   # Or use Render Blueprint (render.yaml)
   ```

9. **Add Health Check**
   ```
   Web Service > Settings > Health Check Path
   Path: /api/v1/health
   ```

#### Render Blueprint Deployment

Alternative: Use `render.yaml` for infrastructure-as-code:

```bash
# In your repo root, commit render.yaml
git add backend/render.yaml
git commit -m "Add Render blueprint"
git push

# In Render dashboard
Dashboard > New + > Blueprint
Connect repository
Select render.yaml
Review and create services
```

**Render CLI Commands**

```bash
# Install Render CLI
brew install render  # macOS
# or download from https://render.com/docs/cli

# Login
render login

# Deploy
render deploy

# View logs
render logs

# Open shell
render shell
```

---

### Option 3: Heroku

**Pros:** Mature platform, extensive documentation
**Cons:** More expensive, no free tier since 2022

#### Quick Heroku Deployment

```bash
# Install Heroku CLI
brew tap heroku/brew && brew install heroku  # macOS
# or download from https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Create app
cd backend
heroku create craigleads-backend

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis
heroku addons:create heroku-redis:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY=$(openssl rand -hex 32)
heroku config:set ENVIRONMENT=production
heroku config:set DEBUG=false
# ... add all other variables

# Deploy
git push heroku main

# Run migrations
heroku run alembic upgrade head

# View logs
heroku logs --tail

# Open app
heroku open
```

---

## Frontend Deployment (Netlify)

### Step-by-Step Netlify Deployment

#### Method 1: Connect GitHub Repository (Recommended)

1. **Push Code to GitHub**
   ```bash
   # If not already done
   cd /Users/greenmachine2.0/Craigslist
   git add .
   git commit -m "Prepare for Netlify deployment"
   git push origin main
   ```

2. **Create Netlify Site**
   ```
   Go to: https://app.netlify.com/
   Click: "Add new site" > "Import an existing project"
   Choose: GitHub
   Authorize Netlify to access your repository
   Select: Your CraigLeads repository
   ```

3. **Configure Build Settings**
   ```
   Base directory: frontend
   Build command: npm run build
   Publish directory: frontend/dist
   ```

4. **Add Environment Variables**
   ```
   Site settings > Environment variables > Add a variable

   Required:
   VITE_API_URL=https://your-backend.railway.app
   VITE_WS_URL=wss://your-backend.railway.app

   Optional (see .env.netlify.example):
   VITE_ENVIRONMENT=production
   VITE_APP_NAME=CraigLeads Pro
   VITE_ENABLE_LINKEDIN=true
   VITE_ENABLE_GOOGLE_MAPS=true
   ```

5. **Deploy**
   ```
   Click: "Deploy site"
   Netlify will:
   - Clone your repository
   - Install dependencies (npm install)
   - Run build (npm run build)
   - Deploy to CDN
   - Provide a URL: random-name-123456.netlify.app
   ```

6. **Verify Deployment**
   ```
   Open the provided URL
   Check browser console for errors
   Test API connectivity
   Verify WebSocket connection
   ```

#### Method 2: Netlify CLI (Alternative)

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Navigate to frontend
cd /Users/greenmachine2.0/Craigslist/frontend

# Initialize Netlify (creates .netlify folder)
netlify init

# Follow prompts:
# - Create & configure a new site
# - Choose team
# - Site name: craigleads-pro
# - Build command: npm run build
# - Publish directory: dist

# Deploy to production
netlify deploy --prod

# Or use the deploy script
cd ..
./scripts/deploy-to-netlify.sh
```

#### Method 3: Manual Deploy (Drag & Drop)

```bash
# Build locally
cd /Users/greenmachine2.0/Craigslist/frontend
npm install
npm run build

# Drag and drop the 'dist' folder to Netlify dashboard
# Go to: https://app.netlify.com/drop
# Drag frontend/dist folder
```

### Netlify Configuration Files

The following files control Netlify behavior:

1. **netlify.toml** (in `/frontend/`)
   - Build settings
   - Redirects for SPA routing
   - Security headers
   - Environment-specific configs

2. **public/_redirects**
   - SPA fallback rules
   - API proxy configuration
   - Custom redirects

3. **public/_headers**
   - Security headers (CSP, HSTS, etc.)
   - Cache control
   - CORS headers

---

## Environment Configuration

### Backend Environment Variables

**Critical Variables (Must Set)**

```bash
# Security
SECRET_KEY=<generate with: openssl rand -hex 32>
ENVIRONMENT=production
DEBUG=false

# Database (auto-set by Railway/Render)
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379

# CORS - Allow your Netlify domain
ALLOWED_HOSTS=["https://your-app.netlify.app"]

# AI Services
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...

# Email (choose one)
# Postmark
POSTMARK_SERVER_TOKEN=...

# Or SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

**Optional Variables**

```bash
# LinkedIn Scraping
LINKEDIN_ENABLED=true
LINKEDIN_SERVICE=piloterr
LINKEDIN_API_KEY=...

# Email Extraction
ENABLE_EMAIL_EXTRACTION=true
TWOCAPTCHA_API_KEY=...

# User Profile
USER_NAME=Your Name
USER_EMAIL=your-email@example.com
USER_PHONE=+1-555-0123

# Performance
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
SCRAPER_CONCURRENT_LIMIT=5
RATE_LIMIT_PER_MINUTE=100
```

### Frontend Environment Variables

Set in Netlify Dashboard: Site settings > Environment variables

```bash
# Required
VITE_API_URL=https://your-backend.railway.app
VITE_WS_URL=wss://your-backend.railway.app

# Optional
VITE_ENVIRONMENT=production
VITE_APP_NAME=CraigLeads Pro
VITE_APP_VERSION=1.0.0

# Feature Flags
VITE_ENABLE_LINKEDIN=true
VITE_ENABLE_GOOGLE_MAPS=true
VITE_ENABLE_JOB_BOARDS=true
VITE_ENABLE_AI_FEATURES=true
```

### Variable Scopes in Netlify

Netlify supports different scopes for environment variables:

- **All**: Used in all contexts (production, previews, branches)
- **Production**: Only production builds
- **Deploy previews**: Only PR preview builds
- **Branch deploys**: Specific branches

**Example Setup:**

```
Production:
  VITE_API_URL=https://api.craigleads.com

Deploy Previews:
  VITE_API_URL=https://staging-api.craigleads.com

Branch: development
  VITE_API_URL=https://dev-api.craigleads.com
```

---

## Custom Domain Setup

### Configure Custom Domain on Netlify

1. **Add Domain**
   ```
   Site settings > Domain management > Add custom domain
   Enter: app.yourdomain.com (or yourdomain.com)
   ```

2. **Verify Ownership**
   ```
   Netlify will provide DNS records
   Add to your domain registrar:
   - A record: 75.2.60.5
   - AAAA record: 2600:... (IPv6)
   Or:
   - CNAME: your-site.netlify.app
   ```

3. **Enable HTTPS**
   ```
   Netlify automatically provisions SSL certificate
   Via Let's Encrypt (free)
   Auto-renewal enabled
   HTTPS enforced by default
   ```

4. **Configure Domain Settings**
   ```
   Primary domain: app.yourdomain.com
   Redirects: www.yourdomain.com → yourdomain.com
   HTTPS: Enabled
   Force HTTPS: Yes
   ```

### Configure Custom Domain on Railway

1. **Add Domain**
   ```
   Service > Settings > Networking > Custom Domain
   Enter: api.yourdomain.com
   ```

2. **Add DNS Record**
   ```
   In your domain registrar, add CNAME:
   api.yourdomain.com → your-app.railway.app
   ```

3. **SSL Certificate**
   ```
   Railway automatically provisions SSL
   Usually takes 5-10 minutes
   ```

### Update CORS Settings

After setting custom domains, update backend CORS:

```python
# In Railway/Render environment variables
ALLOWED_HOSTS=["https://app.yourdomain.com", "https://yourdomain.com"]
```

And frontend API URL:

```bash
# In Netlify environment variables
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com
```

---

## Team Collaboration

### Invite Team Members to Netlify

1. **Team Settings**
   ```
   Team overview > Members > Invite members
   Enter email addresses
   Choose role: Owner, Collaborator, Controller, Viewer
   ```

2. **Roles Explained**
   - **Owner**: Full access, billing
   - **Collaborator**: Deploy, change settings, no billing
   - **Controller**: Deploy only
   - **Viewer**: Read-only access

3. **Site-Level Access**
   ```
   You can also invite members to specific sites
   Site settings > Team and guests > Add members
   ```

### Invite Team Members to Railway

1. **Project Settings**
   ```
   Project > Settings > Members > Invite member
   Enter email
   Choose role: Admin or Member
   ```

2. **Roles**
   - **Admin**: Full project access
   - **Member**: Can view, deploy, no project deletion

### Deploy Preview for PRs

**Netlify automatically creates deploy previews for pull requests:**

1. **Enable Deploy Previews**
   ```
   Site settings > Build & deploy > Deploy contexts
   Deploy previews: Any pull request against main branch
   Branch deploys: All branches
   ```

2. **Review Process**
   ```
   Developer creates PR
   Netlify builds and deploys preview
   Preview URL added as comment in PR
   Team reviews changes on preview URL
   Merge PR → Auto-deploy to production
   ```

3. **Preview URL Format**
   ```
   https://deploy-preview-{PR-NUMBER}--{SITE-NAME}.netlify.app
   ```

### Collaboration Best Practices

1. **Branching Strategy**
   ```
   main → production (auto-deploy)
   development → staging (auto-deploy to separate site)
   feature/* → deploy previews
   ```

2. **Environment Separation**
   ```
   Production: app.yourdomain.com
   Staging: staging.yourdomain.com
   Development: dev.yourdomain.com
   ```

3. **Access Control**
   ```
   Use Netlify Identity or JWT for authenticated routes
   Implement API key authentication for backend
   Use environment-specific API keys
   ```

---

## Monitoring & Maintenance

### Netlify Monitoring

1. **Analytics Dashboard**
   ```
   Site overview > Analytics
   - Bandwidth usage
   - Page views
   - Unique visitors
   - Popular pages
   - Deploy frequency
   ```

2. **Deploy Logs**
   ```
   Deploys tab > Select deploy > Deploy log
   - Build output
   - Error messages
   - Deploy duration
   ```

3. **Function Logs** (if using Netlify Functions)
   ```
   Functions tab > Select function > Logs
   Real-time function invocation logs
   ```

4. **Forms Monitoring** (if using Netlify Forms)
   ```
   Forms tab
   Spam filtering included
   Email notifications on submission
   ```

### Backend Monitoring

**Railway Monitoring**

```
Project Dashboard > Metrics
- CPU usage
- Memory usage
- Network I/O
- Request count
- Response time
```

**Render Monitoring**

```
Dashboard > Service > Metrics
- CPU & Memory
- Bandwidth
- Response time
- Error rate
```

**Custom Monitoring Setup**

1. **Health Check Endpoint**
   ```python
   # Already included in app/main.py
   @app.get("/api/v1/health")
   async def health_check():
       return {"status": "healthy"}
   ```

2. **Logging**
   ```python
   # Use structlog (already configured)
   import structlog
   logger = structlog.get_logger()

   logger.info("scrape_started", location="San Francisco")
   logger.error("scrape_failed", error=str(e))
   ```

3. **Error Tracking** (Optional)
   ```bash
   # Add Sentry for error tracking
   pip install sentry-sdk

   # In app/main.py
   import sentry_sdk
   sentry_sdk.init(dsn="your-sentry-dsn")
   ```

### Performance Optimization

**Frontend (Netlify)**

1. **Lighthouse Scores**
   ```
   Run in Chrome DevTools
   Target: 90+ for all metrics
   ```

2. **Bundle Size**
   ```bash
   npm run build
   # Check dist/ folder size
   # Should be < 2MB total
   ```

3. **CDN Caching**
   ```
   Already configured in netlify.toml
   Static assets cached for 1 year
   HTML not cached (always fresh)
   ```

**Backend (Railway/Render)**

1. **Database Indexing**
   ```sql
   -- Add indexes for frequently queried fields
   CREATE INDEX idx_leads_created_at ON leads(created_at);
   CREATE INDEX idx_leads_location ON leads(location_id);
   ```

2. **Connection Pooling**
   ```python
   # Already configured in app/core/config.py
   DATABASE_POOL_SIZE=20
   DATABASE_MAX_OVERFLOW=30
   ```

3. **Caching with Redis**
   ```python
   # Implement Redis caching for expensive queries
   from app.core.cache import cache

   @cache(ttl=3600)  # 1 hour
   async def get_leads_stats():
       # Expensive query
       pass
   ```

### Backup Strategy

**Database Backups**

**Railway:**
```
PostgreSQL add-on includes automated daily backups
Retention: 7 days on hobby plan, 30 days on pro
Manual backup: Railway dashboard > Database > Backups
```

**Render:**
```
Free tier: No automated backups
Paid plans: Daily automated backups
Manual: pg_dump via shell
```

**Manual Backup Script:**

```bash
#!/bin/bash
# backup-database.sh

# Get connection string from environment
DB_URL=$DATABASE_URL

# Create backup
pg_dump $DB_URL > backup-$(date +%Y%m%d-%H%M%S).sql

# Upload to S3 (optional)
# aws s3 cp backup-*.sql s3://your-bucket/backups/
```

---

## Troubleshooting

### Common Issues & Solutions

#### 1. Build Failures on Netlify

**Issue:** "Command failed with exit code 1"

**Solutions:**
```bash
# Check Node version
# In netlify.toml:
[build.environment]
  NODE_VERSION = "18"

# Clear cache and rebuild
# Netlify dashboard > Deploys > Trigger deploy > Clear cache and deploy site

# Check for missing dependencies
# Ensure all dependencies in package.json

# Verify build locally
cd frontend
npm install
npm run build
```

#### 2. API Connection Errors

**Issue:** "Network Error" or "CORS Error" in browser console

**Solutions:**

1. **Check VITE_API_URL**
   ```bash
   # In Netlify environment variables
   VITE_API_URL=https://your-backend.railway.app
   # NOT http:// (must be https)
   # NOT ending with /api/v1 (added by axios)
   ```

2. **Check Backend CORS**
   ```python
   # In backend environment variables
   ALLOWED_HOSTS=["https://your-app.netlify.app", "https://*.netlify.app"]
   ```

3. **Verify Backend is Running**
   ```bash
   curl https://your-backend.railway.app/api/v1/health
   # Should return: {"status": "healthy"}
   ```

4. **Check Browser Console**
   ```javascript
   // Should show:
   console.log(import.meta.env.VITE_API_URL)
   // "https://your-backend.railway.app"
   ```

#### 3. WebSocket Connection Failures

**Issue:** WebSocket connection refused or immediate disconnect

**Solutions:**

1. **Check WS URL**
   ```bash
   # Must be wss:// not ws://
   VITE_WS_URL=wss://your-backend.railway.app
   ```

2. **Verify Backend WebSocket Support**
   ```python
   # In app/main.py, ensure WebSocket route exists
   @app.websocket("/ws")
   async def websocket_endpoint(websocket: WebSocket):
       # ...
   ```

3. **Check Railway/Render WebSocket Support**
   ```
   Railway: WebSockets fully supported
   Render: Ensure on paid plan (free tier has limitations)
   ```

#### 4. Environment Variables Not Working

**Issue:** Variables undefined in application

**Solutions:**

1. **Check Variable Names**
   ```bash
   # Frontend variables MUST start with VITE_
   VITE_API_URL=...  # ✓ Correct
   API_URL=...       # ✗ Wrong (won't be exposed)
   ```

2. **Rebuild After Adding Variables**
   ```
   Environment variables are injected at BUILD TIME
   Must trigger new deploy after adding/changing variables
   Netlify: Deploys > Trigger deploy
   ```

3. **Check Variable Scope**
   ```
   Ensure variable is set for correct context:
   - Production for prod builds
   - All for all contexts
   ```

4. **Verify in Build Log**
   ```
   Netlify build log shows environment variables
   (values hidden, but names visible)
   ```

#### 5. 404 Errors on Frontend Routes

**Issue:** Direct navigation to routes like /leads, /scraper returns 404

**Solutions:**

1. **Check SPA Redirect**
   ```toml
   # In netlify.toml:
   [[redirects]]
     from = "/*"
     to = "/index.html"
     status = 200
   ```

2. **Check _redirects File**
   ```
   # In frontend/public/_redirects:
   /*    /index.html   200
   ```

3. **Verify React Router**
   ```jsx
   // Ensure using BrowserRouter not HashRouter
   import { BrowserRouter } from 'react-router-dom'
   ```

#### 6. Database Connection Errors

**Issue:** "Connection refused" or "too many connections"

**Solutions:**

1. **Check DATABASE_URL**
   ```bash
   # Should be auto-set by Railway/Render
   # Format: postgresql://user:pass@host:port/dbname
   # Verify in environment variables
   ```

2. **Connection Pool Settings**
   ```python
   # Adjust based on your plan limits
   DATABASE_POOL_SIZE=10  # Lower for free tier
   DATABASE_MAX_OVERFLOW=5
   ```

3. **Check Service Status**
   ```bash
   # Railway: Dashboard > Database > Metrics
   # Render: Dashboard > Database > Metrics
   # Look for connection count
   ```

#### 7. Slow Build Times

**Issue:** Netlify builds taking > 5 minutes

**Solutions:**

1. **Enable Dependency Caching**
   ```toml
   # In netlify.toml:
   [build]
     publish = "dist"
   # Netlify automatically caches node_modules
   ```

2. **Optimize Dependencies**
   ```bash
   # Remove unused dependencies
   npm uninstall <unused-package>

   # Use production install
   npm ci --production
   ```

3. **Reduce Bundle Size**
   ```javascript
   // Use dynamic imports
   const Component = lazy(() => import('./Component'))
   ```

#### 8. SSL/HTTPS Issues

**Issue:** "Your connection is not private" or mixed content warnings

**Solutions:**

1. **Wait for SSL Provisioning**
   ```
   Netlify: Usually < 1 minute
   Railway: Usually < 5 minutes
   Render: Usually < 10 minutes
   ```

2. **Check DNS Propagation**
   ```bash
   # Check if DNS is propagated
   dig your-domain.com
   nslookup your-domain.com
   ```

3. **Force HTTPS**
   ```toml
   # In netlify.toml:
   [[redirects]]
     from = "http://yourdomain.com/*"
     to = "https://yourdomain.com/:splat"
     status = 301
     force = true
   ```

#### 9. Scraper/Playwright Errors

**Issue:** "Playwright not found" or browser crashes

**Solutions:**

1. **Install Playwright on Railway**
   ```bash
   # In Railway shell or deployment script
   playwright install
   playwright install-deps
   ```

2. **Use Headless Mode**
   ```python
   # In scraper config
   browser = await playwright.chromium.launch(
       headless=True,
       args=['--no-sandbox', '--disable-setuid-sandbox']
   )
   ```

3. **Increase Memory Limit**
   ```
   Railway: Upgrade to hobby+ or pro plan
   Render: Use at least starter plan
   ```

### Getting Help

1. **Netlify Support**
   ```
   Community forum: https://answers.netlify.com/
   Docs: https://docs.netlify.com/
   Twitter: @Netlify
   ```

2. **Railway Support**
   ```
   Discord: https://discord.gg/railway
   Docs: https://docs.railway.app/
   Twitter: @Railway
   ```

3. **Render Support**
   ```
   Community: https://community.render.com/
   Docs: https://render.com/docs/
   Email: support@render.com
   ```

4. **Project-Specific Issues**
   ```
   Check backend logs: Railway/Render dashboard
   Check frontend logs: Netlify deploy log
   Check browser console: DevTools (F12)
   Check network tab: Look for failed requests
   ```

---

## Quick Reference

### Essential Commands

```bash
# Frontend (Netlify)
netlify login
netlify init
netlify deploy --prod
netlify open
netlify logs

# Backend (Railway)
railway login
railway link
railway up
railway logs
railway shell

# Backend (Render CLI)
render login
render deploy
render logs
render shell

# Local Development
# Frontend
cd frontend && npm run dev

# Backend
cd backend && uvicorn app.main:app --reload

# Database migrations
cd backend && alembic upgrade head
```

### Important URLs

```
Frontend (Netlify):
https://app.netlify.com/

Backend Options:
https://railway.app/
https://render.com/
https://heroku.com/

Domain Registrars:
https://www.namecheap.com/
https://www.cloudflare.com/
https://domains.google/
```

### Cost Estimates

**Monthly Costs:**

```
Netlify (Frontend):
- Free: 100GB bandwidth, 300 build minutes
- Pro ($19/month): 1TB bandwidth, 1000 build minutes

Railway (Backend):
- Hobby ($5/month): 512MB RAM, 1GB disk, includes DB
- Pro ($20/month): 8GB RAM, 100GB disk

Render (Backend):
- Free: 512MB RAM, 0.1 CPU (spins down)
- Starter ($7/month): 512MB RAM, always on
- Standard ($25/month): 2GB RAM, better performance

Domain:
- $10-15/year

Total Minimum:
- Free tier: $0 (with limitations)
- Production: $24-44/month (Netlify Free + Railway Hobby/Render Starter)
```

---

## Next Steps After Deployment

1. **Set Up Monitoring**
   - Configure uptime monitoring (UptimeRobot, StatusCake)
   - Set up error tracking (Sentry)
   - Enable analytics (Google Analytics, PostHog)

2. **Performance Optimization**
   - Run Lighthouse audits
   - Optimize images and assets
   - Enable caching strategies

3. **Security Hardening**
   - Enable 2FA on all accounts
   - Rotate API keys regularly
   - Set up security headers
   - Configure CSP properly

4. **Backup & Disaster Recovery**
   - Set up automated database backups
   - Document recovery procedures
   - Test restore process

5. **CI/CD Enhancements**
   - Add automated tests to deployment pipeline
   - Set up staging environment
   - Configure deploy notifications

6. **Documentation**
   - Document custom domain setup
   - Create runbooks for common tasks
   - Update team onboarding docs

---

## Conclusion

You now have a complete production deployment of CraigLeads Pro:

- **Frontend**: Hosted on Netlify with global CDN, automatic SSL, and CI/CD
- **Backend**: Deployed on Railway/Render with PostgreSQL, Redis, and scalable infrastructure
- **Monitoring**: Dashboard access to metrics, logs, and performance
- **Team Collaboration**: Shared access, deploy previews, and branch deploys

**Deployment Checklist:**

- [ ] Backend deployed to Railway/Render
- [ ] Database migrations run successfully
- [ ] Environment variables configured
- [ ] Health check endpoint responding
- [ ] Frontend deployed to Netlify
- [ ] API connection working
- [ ] WebSocket connection working
- [ ] Custom domain configured (optional)
- [ ] SSL certificates active
- [ ] Team members invited
- [ ] Monitoring enabled
- [ ] Backup strategy in place

**Support:**

For issues specific to CraigLeads Pro, check:
- Backend logs in Railway/Render dashboard
- Frontend deploy logs in Netlify
- Browser console for frontend errors
- API health endpoint: `/api/v1/health`

Happy deploying!
