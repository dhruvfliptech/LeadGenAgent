# CraigLeads Pro - Netlify Deployment Package

Complete production deployment configuration for CraigLeads Pro using Netlify (frontend) and Railway/Render (backend).

## What's Included

This deployment package provides everything you need to deploy CraigLeads Pro to production in under 30 minutes.

### Configuration Files

```
Frontend (Netlify):
├── frontend/netlify.toml                 - Main Netlify configuration
├── frontend/.env.netlify.example         - Environment variables template
├── frontend/public/_redirects            - SPA routing configuration
└── frontend/public/_headers              - Security and cache headers

Backend (Railway/Render/Heroku):
├── backend/Procfile                      - Process configuration
├── backend/railway.json                  - Railway-specific config
├── backend/render.yaml                   - Render Blueprint
└── backend/.env.production.example       - Production environment template

Deployment Scripts:
├── scripts/deploy-to-netlify.sh          - Automated deployment script
└── NETLIFY_DEPLOYMENT_GUIDE.md           - Comprehensive guide
```

### Documentation

1. **NETLIFY_DEPLOYMENT_GUIDE.md** (30,000+ words)
   - Complete step-by-step deployment instructions
   - Backend deployment options (Railway, Render, Heroku)
   - Environment configuration guide
   - Custom domain setup
   - Team collaboration setup
   - Monitoring and maintenance
   - Extensive troubleshooting section

2. **NETLIFY_QUICK_START.md**
   - Fast 30-minute deployment path
   - Essential steps only
   - Common issues and quick fixes
   - Cost breakdown

3. **Backend Environment Documentation**
   - Complete environment variable reference
   - Security configuration checklist
   - Production optimization settings

## Quick Start

### 1. Deploy Backend (5 minutes)

**Railway (Recommended)**:
```bash
1. Visit https://railway.app/
2. Connect your GitHub repository
3. Add PostgreSQL and Redis
4. Set environment variables
5. Deploy automatically
```

### 2. Deploy Frontend (5 minutes)

**Netlify**:
```bash
1. Visit https://app.netlify.com/
2. Connect your GitHub repository
3. Configure: Base=frontend, Build=npm run build, Publish=frontend/dist
4. Set VITE_API_URL and VITE_WS_URL
5. Deploy automatically
```

### 3. Test Deployment (5 minutes)

```bash
# Backend health check
curl https://your-app.railway.app/api/v1/health

# Frontend - open in browser
https://your-app.netlify.app

# Check browser console for API connection
```

## File Guide

### Frontend Configuration

#### netlify.toml
```toml
# Main configuration file - controls build, redirects, headers
Location: frontend/netlify.toml

Key Features:
- Build command and publish directory
- SPA routing redirects
- Security headers (CSP, HSTS, etc.)
- Cache configuration
- Environment-specific settings
```

#### .env.netlify.example
```bash
# Environment variables template
Location: frontend/.env.netlify.example

Required Variables:
- VITE_API_URL: Your backend URL
- VITE_WS_URL: WebSocket URL

Optional:
- Feature flags
- Service configuration
- UI settings
```

#### _redirects
```
# SPA routing and proxy configuration
Location: frontend/public/_redirects

Features:
- Client-side routing support
- API proxy rules (optional)
- Custom redirects
```

#### _headers
```
# Security and performance headers
Location: frontend/public/_headers

Features:
- Security headers (CSP, HSTS, X-Frame-Options)
- Cache control for static assets
- CORS headers
```

### Backend Configuration

#### Procfile
```bash
# Process definition for Railway/Heroku
Location: backend/Procfile

Processes:
- web: Main FastAPI application
- worker: Celery background tasks (optional)
- beat: Celery scheduler (optional)
```

#### railway.json
```json
# Railway-specific configuration
Location: backend/railway.json

Features:
- Build and deploy commands
- Health check configuration
- Service dependencies
- Environment settings
```

#### render.yaml
```yaml
# Render Blueprint - Infrastructure as Code
Location: backend/render.yaml

Defines:
- Web service (FastAPI)
- Worker service (Celery)
- Database (PostgreSQL)
- Redis cache
- Environment variables
- Auto-deploy settings
```

#### .env.production.example
```bash
# Complete production environment template
Location: backend/.env.production.example

Sections:
- Application settings
- Security configuration
- Database and Redis
- AI services (OpenAI, Anthropic)
- Email configuration
- Scraping settings
- Feature flags
- Monitoring
```

### Deployment Scripts

#### deploy-to-netlify.sh
```bash
# Automated deployment with checks
Location: scripts/deploy-to-netlify.sh

Features:
- Pre-deployment validation
- Build testing
- Environment verification
- One-command deployment
- Post-deployment checklist

Usage:
./scripts/deploy-to-netlify.sh --prod
```

## Deployment Options Comparison

### Frontend: Netlify

**Why Netlify?**
- Best-in-class static site hosting
- Global CDN (200+ edge locations)
- Automatic SSL/TLS certificates
- Deploy previews for PRs
- Generous free tier
- Atomic deployments (instant rollback)

**Pricing**:
- Free: 100GB bandwidth, 300 build minutes
- Pro ($19/mo): 1TB bandwidth, team features

### Backend: Railway (Recommended)

**Why Railway?**
- Easiest Python/FastAPI deployment
- Includes PostgreSQL + Redis
- Automatic HTTPS
- Great developer experience
- Simple pricing

**Pricing**:
- Hobby ($5/mo): 512MB RAM, includes DB
- Pro ($20/mo): 8GB RAM, better performance

### Backend: Render (Alternative)

**Why Render?**
- Free tier available
- Good for testing
- Infrastructure as code (render.yaml)
- Automatic SSL

**Pricing**:
- Free: Sleeps after inactivity
- Starter ($7/mo): Always on
- Standard ($25/mo): 2GB RAM

### Backend: Heroku (Traditional)

**Why Heroku?**
- Mature platform
- Extensive documentation
- Large ecosystem

**Pricing**:
- No free tier (as of 2022)
- Starting at $7/mo per dyno

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PRODUCTION STACK                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Frontend                           Backend                  │
│  ┌──────────────────┐              ┌─────────────────────┐  │
│  │   Netlify CDN    │              │  Railway/Render     │  │
│  │   React + Vite   │◄────HTTPS───►│  FastAPI + Uvicorn │  │
│  │   Static Files   │              │  REST API          │  │
│  │   Global Edge    │              │  WebSockets        │  │
│  └──────────────────┘              └─────────────────────┘  │
│                                              │               │
│                                              ▼               │
│                                     ┌─────────────────┐     │
│                                     │  PostgreSQL     │     │
│                                     │  Redis          │     │
│                                     │  (Managed)      │     │
│                                     └─────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Benefits**:
- Frontend and backend scale independently
- Frontend served from edge locations (fast globally)
- Backend in single region (simpler, cost-effective)
- Managed databases (automatic backups, scaling)
- Automatic SSL everywhere
- Zero-downtime deployments

## Environment Variables Reference

### Frontend (Netlify)

**Required**:
```bash
VITE_API_URL=https://your-backend.railway.app
VITE_WS_URL=wss://your-backend.railway.app
```

**Optional**:
```bash
VITE_ENVIRONMENT=production
VITE_APP_NAME=CraigLeads Pro
VITE_ENABLE_LINKEDIN=true
VITE_ENABLE_GOOGLE_MAPS=true
```

### Backend (Railway/Render)

**Required**:
```bash
SECRET_KEY=<generate with: openssl rand -hex 32>
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS=["https://your-app.netlify.app"]
DATABASE_URL=<auto-set by Railway/Render>
REDIS_URL=<auto-set by Railway/Render>
```

**AI Services** (choose one):
```bash
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...
```

**Email** (choose one):
```bash
POSTMARK_SERVER_TOKEN=...
# OR
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=...
SMTP_PASSWORD=...
```

**Optional**:
```bash
LINKEDIN_API_KEY=...
TWOCAPTCHA_API_KEY=...
GOOGLE_MAPS_API_KEY=...
```

## Security Checklist

- [ ] `DEBUG=false` in production
- [ ] Unique `SECRET_KEY` generated (min 32 chars)
- [ ] `ALLOWED_HOSTS` contains only actual domains (no wildcards)
- [ ] All API keys are production keys (not test keys)
- [ ] Database uses SSL connection
- [ ] Redis password protected
- [ ] HTTPS enforced on both frontend and backend
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] Environment variables not committed to git
- [ ] 2FA enabled on all accounts (Netlify, Railway, GitHub)

## Deployment Workflow

### Initial Deployment

1. **Prepare Code**
   ```bash
   git add .
   git commit -m "Prepare for production"
   git push origin main
   ```

2. **Deploy Backend**
   - Connect Railway/Render to GitHub
   - Add databases (PostgreSQL, Redis)
   - Set environment variables
   - Deploy automatically

3. **Deploy Frontend**
   - Connect Netlify to GitHub
   - Configure build settings
   - Set environment variables
   - Deploy automatically

4. **Verify**
   - Test health endpoint
   - Check frontend loads
   - Verify API connectivity
   - Test WebSocket connection

### Continuous Deployment

After initial setup, deployments are automatic:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Both Railway and Netlify will:
# 1. Detect push to main branch
# 2. Build your application
# 3. Run tests (if configured)
# 4. Deploy to production
# 5. Update within 2-3 minutes
```

### Deploy Previews (PR Workflow)

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and push
git add .
git commit -m "Add new feature"
git push origin feature/new-feature

# Create PR on GitHub
# Netlify automatically creates deploy preview
# Team reviews changes on preview URL
# Merge PR → automatic production deployment
```

## Team Sharing

### Invite Team Members

**Netlify**:
```
1. Go to team settings
2. Click "Add team member"
3. Enter email address
4. Choose role: Owner, Collaborator, Controller, Viewer
5. Team member receives invitation
```

**Railway**:
```
1. Go to project settings
2. Click "Add member"
3. Enter email address
4. Choose role: Admin or Member
5. Team member receives invitation
```

### Access Levels

**Netlify Roles**:
- **Owner**: Full access, billing
- **Collaborator**: Deploy, settings (no billing)
- **Controller**: Deploy only
- **Viewer**: Read-only

**Railway Roles**:
- **Admin**: Full project access
- **Member**: View and deploy

## Monitoring

### Built-in Monitoring

**Netlify**:
- Deploy history and logs
- Bandwidth usage
- Build minutes used
- Form submissions (if enabled)
- Analytics (Pro plan)

**Railway**:
- CPU and memory usage
- Network I/O
- Request count
- Response time
- Logs (real-time)

**Render**:
- CPU and memory metrics
- Response time
- Error rate
- Logs (real-time)

### Recommended External Monitoring

1. **Uptime Monitoring**
   - UptimeRobot (free tier: 50 monitors)
   - Pingdom
   - StatusCake

2. **Error Tracking**
   - Sentry (recommended)
   - Rollbar
   - Bugsnag

3. **Analytics**
   - Google Analytics
   - PostHog (open source)
   - Plausible (privacy-friendly)

## Costs

### Minimal Production Setup

```
Netlify Free:        $0/mo
Railway Hobby:       $5/mo
Domain Name:         $10-15/year
------------------------
Total:               ~$5-6/mo
```

### Recommended Production Setup

```
Netlify Free:        $0/mo
Railway Pro:         $20/mo
Domain Name:         $10-15/year
------------------------
Total:               ~$21-22/mo
```

### Full Production Setup

```
Netlify Pro:         $19/mo
Railway Pro:         $20/mo
Domain Name:         $10-15/year
Monitoring:          $0-29/mo (Sentry, etc.)
------------------------
Total:               ~$39-68/mo
```

## Troubleshooting

### Common Issues

1. **"Network Error" in frontend**
   - Check `VITE_API_URL` in Netlify (must be HTTPS)
   - Check `ALLOWED_HOSTS` in backend
   - Verify backend is running

2. **"CORS Error"**
   - Update `ALLOWED_HOSTS` to include Netlify URL
   - Redeploy backend after changing CORS

3. **"Build Failed" on Netlify**
   - Check Node version (set to 18 in netlify.toml)
   - Clear cache and rebuild
   - Check build log for errors

4. **"Database Connection Error"**
   - Verify `DATABASE_URL` is set correctly
   - Check PostgreSQL service is running
   - Reduce connection pool size if needed

5. **"WebSocket Connection Failed"**
   - Check `VITE_WS_URL` uses `wss://` not `ws://`
   - Verify backend WebSocket endpoint exists
   - Check Railway/Render WebSocket support

### Getting Help

**Documentation**:
- Read full guide: `NETLIFY_DEPLOYMENT_GUIDE.md`
- Check quick start: `NETLIFY_QUICK_START.md`
- Review backend guide: `backend/DEPLOYMENT_OPERATIONS_GUIDE.md`

**Platform Support**:
- Netlify: https://answers.netlify.com/
- Railway: https://discord.gg/railway
- Render: https://community.render.com/

**Project Support**:
- Check backend logs in Railway/Render dashboard
- Check frontend logs in Netlify deploy log
- Check browser console (F12) for errors
- Review Network tab for failed API calls

## Success Criteria

Your deployment is successful when:

- [ ] Backend health check returns 200: `/api/v1/health`
- [ ] Frontend loads without errors
- [ ] Browser console shows no errors
- [ ] API requests succeed (check Network tab)
- [ ] WebSocket connection established
- [ ] All routes accessible (no 404s)
- [ ] Real-time updates work (WebSocket)
- [ ] Custom domain configured (optional)
- [ ] SSL certificates active (HTTPS)
- [ ] Team members can access dashboards
- [ ] Monitoring configured
- [ ] Backup strategy in place

## Next Steps After Deployment

1. **Configure Custom Domain** (optional)
   - Add domain in Netlify and Railway
   - Update DNS records
   - Wait for SSL provisioning

2. **Set Up Monitoring**
   - Configure uptime monitoring
   - Set up error tracking (Sentry)
   - Enable analytics

3. **Optimize Performance**
   - Run Lighthouse audit
   - Optimize images
   - Review database indexes

4. **Team Onboarding**
   - Invite team members
   - Share access credentials
   - Document deployment process

5. **Plan for Scale**
   - Monitor usage and metrics
   - Plan for database scaling
   - Consider CDN optimization

## Additional Resources

### Official Documentation

- **Netlify**: https://docs.netlify.com/
- **Railway**: https://docs.railway.app/
- **Render**: https://render.com/docs/
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Vite**: https://vitejs.dev/

### Helpful Tools

- **Netlify CLI**: `npm install -g netlify-cli`
- **Railway CLI**: `npm install -g @railway/cli`
- **Render CLI**: https://render.com/docs/cli
- **PostgreSQL Client**: `psql` or pgAdmin
- **Redis Client**: `redis-cli` or RedisInsight

### Community

- **Netlify Community**: https://answers.netlify.com/
- **Railway Discord**: https://discord.gg/railway
- **Render Community**: https://community.render.com/
- **FastAPI Discord**: https://discord.gg/VQjSZaeJmf

## Summary

This deployment package provides:

✅ Complete Netlify configuration for frontend
✅ Multiple backend deployment options (Railway, Render, Heroku)
✅ Production-ready environment templates
✅ Security-hardened configurations
✅ Automated deployment scripts
✅ Comprehensive documentation
✅ Troubleshooting guides
✅ Team collaboration setup
✅ Monitoring recommendations
✅ Cost optimization tips

**Deployment Time**: 30 minutes for basic setup

**Result**: Production-ready application with:
- Global CDN distribution
- Automatic HTTPS
- Managed databases
- Automatic deployments
- Deploy previews
- Team collaboration
- Professional infrastructure

Ready to deploy? Start with `NETLIFY_QUICK_START.md` for the fastest path to production!

---

**Created**: November 2024
**Version**: 1.0.0
**Maintained by**: CraigLeads Pro Team
