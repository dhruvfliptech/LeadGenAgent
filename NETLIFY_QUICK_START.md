# CraigLeads Pro - Netlify Deployment Quick Start

Get CraigLeads Pro deployed to production in 30 minutes or less.

## TL;DR - Fastest Path to Production

```bash
# 1. Deploy backend to Railway (5 minutes)
#    → Visit railway.app, connect GitHub, add PostgreSQL + Redis

# 2. Deploy frontend to Netlify (5 minutes)
#    → Visit netlify.com, connect GitHub, set VITE_API_URL

# 3. Configure environment variables (10 minutes)
#    → Set API keys in Railway and Netlify dashboards

# 4. Test deployment (10 minutes)
#    → Visit your site, verify API connection, test features
```

---

## Step 1: Deploy Backend to Railway (Recommended)

### Why Railway?
- Easiest setup for Python/FastAPI
- Includes PostgreSQL and Redis out of the box
- Automatic HTTPS and deployment
- $5/month hobby plan

### Quick Deploy

1. **Sign up**: https://railway.app/ (use GitHub login)

2. **Create project**: Dashboard → New Project → Deploy from GitHub repo

3. **Select repository**: Choose your CraigLeads repo

4. **Add services**:
   ```
   - Add PostgreSQL: New → Database → PostgreSQL
   - Add Redis: New → Database → Redis
   - Railway auto-sets DATABASE_URL and REDIS_URL
   ```

5. **Configure backend service**:
   ```
   Root Directory: backend
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4
   ```

6. **Set environment variables**:
   ```
   Go to service → Variables → Add Variables

   Required:
   - SECRET_KEY: Run in terminal: openssl rand -hex 32
   - ENVIRONMENT: production
   - DEBUG: false
   - ALLOWED_HOSTS: ["https://your-app.netlify.app"]

   Optional (add as needed):
   - OPENAI_API_KEY: your-key
   - SMTP_USERNAME: your-email
   - SMTP_PASSWORD: your-password
   ```

7. **Deploy**:
   ```
   Railway auto-deploys on push to main
   Wait 2-3 minutes for first deploy
   Get URL: your-app.railway.app
   ```

8. **Verify deployment**:
   ```bash
   # Test health endpoint
   curl https://your-app.railway.app/api/v1/health
   # Should return: {"status":"healthy"}
   ```

9. **Run database migrations**:
   ```bash
   # In Railway dashboard → Service → Shell
   alembic upgrade head

   # Or install Railway CLI
   npm install -g @railway/cli
   railway login
   railway link
   railway run alembic upgrade head
   ```

10. **Enable Playwright (if using scrapers)**:
    ```bash
    # In Railway shell
    playwright install
    playwright install-deps
    ```

**Railway URL**: `https://your-app.railway.app`

---

## Step 2: Deploy Frontend to Netlify

### Why Netlify?
- Best static site hosting with global CDN
- Automatic SSL and deployments
- Free tier includes everything you need
- Deploy previews for PRs

### Quick Deploy

1. **Sign up**: https://app.netlify.com/signup (use GitHub login)

2. **Create site**: Add new site → Import an existing project → GitHub

3. **Configure build**:
   ```
   Base directory: frontend
   Build command: npm run build
   Publish directory: frontend/dist
   ```

4. **Add environment variables**:
   ```
   Site settings → Environment variables → Add a variable

   Required:
   - VITE_API_URL: https://your-app.railway.app
   - VITE_WS_URL: wss://your-app.railway.app

   Optional:
   - VITE_ENVIRONMENT: production
   - VITE_APP_NAME: CraigLeads Pro
   - VITE_ENABLE_LINKEDIN: true
   - VITE_ENABLE_GOOGLE_MAPS: true
   ```

5. **Deploy**:
   ```
   Click "Deploy site"
   Wait 2-3 minutes for build
   Get URL: random-name-123456.netlify.app
   ```

6. **Verify deployment**:
   ```
   Open your Netlify URL in browser
   Check browser console (F12) for errors
   Test API connection (check Network tab)
   ```

**Netlify URL**: `https://your-app.netlify.app`

---

## Step 3: Configure CORS and Connection

### Update Backend CORS

In Railway dashboard, update ALLOWED_HOSTS:

```
ALLOWED_HOSTS=["https://your-app.netlify.app", "https://*.netlify.app"]
```

This allows your frontend to make requests to the backend.

### Verify Connection

Open your Netlify site and check browser console:

```javascript
// Should see successful API requests
console.log(import.meta.env.VITE_API_URL)
// "https://your-app.railway.app"
```

### Test WebSocket

Check if real-time updates work:
1. Go to Scraper page
2. Start a scraping job
3. You should see real-time progress updates

---

## Step 4: Optional Enhancements

### Custom Domain

**Netlify**:
```
Site settings → Domain management → Add custom domain
Add DNS records at your registrar
SSL automatically provisioned
```

**Railway**:
```
Service → Settings → Networking → Custom Domain
Add CNAME record at your registrar
```

### Automatic Deployments

Both platforms auto-deploy on git push:

```bash
git add .
git commit -m "Update feature"
git push origin main
# Both Railway and Netlify will auto-deploy
```

### Environment Separation

Create separate environments:

```
Production:
- Branch: main
- Frontend: app.yourdomain.com
- Backend: api.yourdomain.com

Staging:
- Branch: development
- Frontend: staging.yourdomain.com
- Backend: staging-api.yourdomain.com
```

---

## Deployment Checklist

### Before Deployment
- [ ] Code pushed to GitHub
- [ ] Dependencies updated (package.json, requirements.txt)
- [ ] Environment variables documented
- [ ] Database models created
- [ ] API endpoints tested locally
- [ ] Frontend builds successfully

### Backend Deployment (Railway)
- [ ] Railway account created
- [ ] Project created from GitHub
- [ ] PostgreSQL added
- [ ] Redis added
- [ ] Environment variables set
- [ ] SECRET_KEY generated
- [ ] ALLOWED_HOSTS configured
- [ ] Service deployed successfully
- [ ] Health check returns 200
- [ ] Database migrations run

### Frontend Deployment (Netlify)
- [ ] Netlify account created
- [ ] Site created from GitHub
- [ ] Build settings configured
- [ ] VITE_API_URL set to Railway URL
- [ ] VITE_WS_URL set to Railway URL
- [ ] Site deployed successfully
- [ ] API connection working
- [ ] WebSocket connection working
- [ ] All routes accessible (no 404s)

### Post-Deployment
- [ ] Custom domain configured (optional)
- [ ] SSL certificates active
- [ ] CORS properly configured
- [ ] All features tested
- [ ] Error monitoring set up
- [ ] Team members invited
- [ ] Documentation updated
- [ ] Backups configured

---

## Common Issues & Quick Fixes

### "Network Error" in Frontend

**Problem**: Frontend can't connect to backend

**Fix**:
```bash
# Check VITE_API_URL in Netlify
# Must be: https://your-app.railway.app
# NOT: http:// (must use HTTPS)
# NOT: https://your-app.railway.app/api/v1 (axios adds this)

# Check ALLOWED_HOSTS in Railway
# Must include: https://your-app.netlify.app
```

### "CORS Error"

**Problem**: CORS policy blocking requests

**Fix**:
```bash
# In Railway environment variables
ALLOWED_HOSTS=["https://your-app.netlify.app", "https://*.netlify.app"]

# Redeploy backend after changing
```

### "Database Connection Error"

**Problem**: Backend can't connect to database

**Fix**:
```bash
# In Railway dashboard
# Check that PostgreSQL service is running
# Verify DATABASE_URL is set automatically
# Should be: postgresql://postgres:...@...railway.app:5432/railway
```

### "Build Failed" on Netlify

**Problem**: Build command fails

**Fix**:
```bash
# Check Node version in netlify.toml:
[build.environment]
  NODE_VERSION = "18"

# Or set in Netlify UI:
# Site settings → Environment variables
# NODE_VERSION = 18

# Clear cache and rebuild:
# Deploys → Trigger deploy → Clear cache and deploy site
```

### "WebSocket Connection Failed"

**Problem**: Real-time updates not working

**Fix**:
```bash
# Check VITE_WS_URL in Netlify
# Must be: wss://your-app.railway.app (wss not ws)

# Verify backend WebSocket endpoint exists
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  https://your-app.railway.app/ws
```

---

## One-Command Deployment (Alternative)

### Using Deployment Script

```bash
# Make script executable
chmod +x scripts/deploy-to-netlify.sh

# Deploy to draft (preview)
./scripts/deploy-to-netlify.sh

# Deploy to production
./scripts/deploy-to-netlify.sh --prod

# Skip checks and deploy
./scripts/deploy-to-netlify.sh --prod --auto-confirm
```

### Using Netlify CLI

```bash
# Install CLI
npm install -g netlify-cli

# Login
netlify login

# Link site (first time only)
cd frontend
netlify link

# Deploy to draft
netlify deploy

# Deploy to production
netlify deploy --prod
```

### Using Railway CLI

```bash
# Install CLI
npm install -g @railway/cli

# Login
railway login

# Link project (first time only)
railway link

# Deploy
railway up

# View logs
railway logs
```

---

## Cost Summary

### Free Tier (Testing)

```
Netlify: Free
- 100 GB bandwidth/month
- 300 build minutes/month
- Deploy previews included

Railway: $5/month Hobby
- 512 MB RAM
- 1 GB disk
- PostgreSQL + Redis included

Total: $5/month
```

### Production (Recommended)

```
Netlify: $19/month Pro (or stay on Free)
- 1 TB bandwidth/month
- 1000 build minutes/month
- Analytics included

Railway: $20/month Pro
- 8 GB RAM
- 100 GB disk
- Better performance

Total: $39/month (or $24 if Netlify Free is enough)
```

---

## Next Steps

1. **Monitor Performance**
   - Railway: Dashboard → Metrics
   - Netlify: Site overview → Analytics

2. **Set Up Alerts**
   - UptimeRobot for uptime monitoring
   - Sentry for error tracking

3. **Optimize**
   - Run Lighthouse audit
   - Optimize images
   - Enable caching

4. **Scale**
   - Add more Railway instances
   - Upgrade Netlify plan if needed
   - Add Redis for caching

---

## Getting Help

**Documentation**:
- Full guide: `NETLIFY_DEPLOYMENT_GUIDE.md`
- Backend setup: `backend/DEPLOYMENT_OPERATIONS_GUIDE.md`

**Support**:
- Railway: https://discord.gg/railway
- Netlify: https://answers.netlify.com/

**Project Issues**:
- Check Railway logs
- Check Netlify deploy logs
- Check browser console

---

## Summary

You should now have:

✅ Backend running on Railway with PostgreSQL + Redis
✅ Frontend deployed on Netlify with global CDN
✅ Automatic HTTPS on both
✅ Automatic deployments on git push
✅ Environment variables configured
✅ CORS properly set up

**Your URLs**:
- Frontend: `https://your-app.netlify.app`
- Backend: `https://your-app.railway.app`
- Health Check: `https://your-app.railway.app/api/v1/health`

**Time to Deploy**: ~30 minutes

Happy deploying! 🚀
