# CraigLeads Pro - Production Deployment Guide

This guide will help you deploy the CraigLeads Pro application to production using Render (backend) and Netlify (frontend).

## Prerequisites

- GitHub account with this repository
- Render account (https://render.com)
- Netlify account (https://netlify.com)
- PostgreSQL database (can be created on Render)
- Redis instance (can be created on Render)

## Critical Fixes Applied

Before deployment, the following production-blocking issues have been fixed:

1. **CSP Configuration**: Updated to allow Google Fonts and external API calls
2. **Duplicate Security Headers**: Removed conflicting headers
3. **CORS Configuration**: Replaced wildcards with explicit allow lists
4. **Environment Configuration**: Created proper `.env` files for all environments

---

## Part 1: Local Testing (REQUIRED FIRST)

### Backend Setup

1. **Install PostgreSQL** (if not already installed):
   ```bash
   # macOS
   brew install postgresql@15
   brew services start postgresql@15

   # Ubuntu/Debian
   sudo apt install postgresql postgresql-contrib
   sudo systemctl start postgresql
   ```

2. **Install Redis** (if not already installed):
   ```bash
   # macOS
   brew install redis
   brew services start redis

   # Ubuntu/Debian
   sudo apt install redis-server
   sudo systemctl start redis
   ```

3. **Create Database**:
   ```bash
   # Connect to PostgreSQL
   psql postgres

   # Create database
   CREATE DATABASE craigleads;

   # Create user (if needed)
   CREATE USER postgres WITH PASSWORD 'postgres';

   # Grant privileges
   GRANT ALL PRIVILEGES ON DATABASE craigleads TO postgres;

   # Exit
   \q
   ```

4. **Setup Backend**:
   ```bash
   cd backend

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Install Playwright browsers
   playwright install chromium

   # The .env file is already created with local settings
   # Review and update if needed:
   # - DATABASE_URL (if your postgres credentials are different)
   # - REDIS_URL (if redis is on a different port)
   # - Add API keys for AI features (optional)

   # Create database tables
   cd ..
   python create_tables.py
   ```

5. **Start Backend**:
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

   # Test it's working:
   # Open http://localhost:8000/docs in your browser
   # You should see the Swagger API documentation
   ```

### Frontend Setup

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Review Environment Configuration**:
   The `.env.development` file is already configured to connect to `http://localhost:8000`.
   No changes needed for local development.

3. **Start Frontend**:
   ```bash
   npm run dev

   # The frontend will start on http://localhost:5176
   ```

4. **Test Locally**:
   - Open http://localhost:5176 in your browser
   - Verify the UI loads without errors
   - Check browser console for any errors
   - Test basic navigation
   - Verify API calls are working (check Network tab)

---

## Part 2: Backend Deployment to Render

### Step 1: Prepare for Deployment

1. **Generate Secret Key**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Save this output - you'll need it for Render environment variables.

2. **Commit all changes to Git**:
   ```bash
   git add .
   git commit -m "fix: production configuration and deployment setup"
   git push origin main
   ```

### Step 2: Create PostgreSQL Database on Render

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `craigleads-db`
   - **Database**: `craigleads`
   - **User**: `craigleads_user`
   - **Region**: Choose closest to you
   - **Plan**: Select based on your needs (Free tier available)
4. Click **"Create Database"**
5. **Save the connection details** (you'll see them in the database dashboard):
   - Internal Database URL (for connecting from Render services)
   - External Database URL (for connecting from your local machine)

### Step 3: Create Redis Instance on Render

1. Click **"New +"** → **"Redis"**
2. Configure:
   - **Name**: `craigleads-redis`
   - **Region**: Same as your database
   - **Plan**: Select based on your needs (Free tier available)
3. Click **"Create Redis"**
4. **Save the Redis URL** from the dashboard

### Step 4: Create Web Service for Backend

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `craigleads-backend`
   - **Region**: Same as your database
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && playwright install chromium
     ```
   - **Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: Select based on your needs

4. **Add Environment Variables** (click "Advanced" → "Add Environment Variable"):

   ```bash
   # Core Settings
   ENVIRONMENT=production
   DEBUG=false
   SECRET_KEY=<paste-your-generated-secret-key>

   # Database - Use Internal Database URL from Step 2
   DATABASE_URL=${{craigleads-db.DATABASE_URL}}

   # Redis - Use Internal Redis URL from Step 3
   REDIS_URL=${{craigleads-redis.REDIS_URL}}

   # CORS - We'll update this after deploying frontend
   ALLOWED_HOSTS=https://craigleads-backend.onrender.com

   # API Configuration
   API_V1_STR=/api/v1
   PROJECT_NAME=CraigLeads Pro
   VERSION=2.0.0

   # Feature Flags
   ENABLE_REAL_TIME_NOTIFICATIONS=true
   ENABLE_AUTOMATED_RESPONSES=false
   ENABLE_ADVANCED_FILTERING=true
   AUTO_RESPONDER_ENABLED=false
   RULE_ENGINE_ENABLED=true
   ENABLE_ADVANCED_ANALYTICS=true
   ENABLE_AB_TESTING=true
   GMAIL_ENABLED=false
   ENABLE_EMAIL_EXTRACTION=false

   # Database Settings
   DATABASE_POOL_SIZE=10
   DATABASE_MAX_OVERFLOW=10

   # Logging
   LOG_LEVEL=INFO

   # Scraping Configuration
   SCRAPER_DELAY_MIN=2.0
   SCRAPER_DELAY_MAX=5.0
   SCRAPER_CONCURRENT_LIMIT=3

   # Rate Limiting
   RATE_LIMIT_PER_MINUTE=60

   # AI Provider (if using AI features)
   AI_PROVIDER=openai
   DEFAULT_AI_MODEL=gpt-3.5-turbo
   # OPENAI_API_KEY=<your-key>  # Add if using AI features
   # ANTHROPIC_API_KEY=<your-key>  # Add if using AI features
   # OPENROUTER_API_KEY=<your-key>  # Add if using AI features

   # User Information
   USER_NAME=Your Name
   USER_EMAIL=your.email@example.com
   USER_PHONE=+1234567890
   USER_COMPANY=Your Company

   # Email Tracking
   TRACKING_DOMAIN=https://craigleads-backend.onrender.com
   TRACKING_PIXEL_ENABLED=true
   LINK_TRACKING_ENABLED=true
   ```

5. Click **"Create Web Service"**

6. **Wait for deployment** (first deploy takes 5-10 minutes)

7. **Run database migrations** after deployment:
   - Go to your backend service dashboard
   - Click **"Shell"** in the left sidebar
   - Run:
     ```bash
     python /opt/render/project/src/../create_tables.py
     ```

8. **Note your backend URL**:
   - Something like: `https://craigleads-backend.onrender.com`
   - **Save this URL** - you'll need it for frontend configuration

9. **Test your backend**:
   - Visit: `https://craigleads-backend.onrender.com/docs`
   - You should see the Swagger API documentation
   - Test the `/health` endpoint

---

## Part 3: Frontend Deployment to Netlify

### Step 1: Update Frontend Environment Variables

1. Edit `frontend/.env.production`:
   ```bash
   # Replace with your actual Render backend URL
   VITE_API_URL=https://craigleads-backend.onrender.com
   VITE_WS_URL=wss://craigleads-backend.onrender.com

   # Turn off mock data for production
   VITE_USE_MOCK_DATA=false

   # Feature Flags
   VITE_ENABLE_WORKFLOWS=true
   VITE_ENABLE_TEMPLATES=true
   VITE_ENABLE_EMAIL_TRACKING=true
   VITE_ENABLE_APPROVALS=true
   VITE_ENABLE_DEMO_SITES=true
   ```

2. **Commit and push**:
   ```bash
   git add frontend/.env.production
   git commit -m "feat: configure frontend for production backend"
   git push origin main
   ```

### Step 2: Deploy to Netlify

1. Go to https://app.netlify.com
2. Click **"Add new site"** → **"Import an existing project"**
3. Connect your GitHub repository
4. Configure build settings:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`
   - **Node version**: `18`

5. **Add Environment Variables** (Site settings → Environment variables):
   ```bash
   VITE_API_URL=https://craigleads-backend.onrender.com
   VITE_WS_URL=wss://craigleads-backend.onrender.com
   VITE_USE_MOCK_DATA=false
   VITE_ENABLE_WORKFLOWS=true
   VITE_ENABLE_TEMPLATES=true
   VITE_ENABLE_EMAIL_TRACKING=true
   VITE_ENABLE_APPROVALS=true
   VITE_ENABLE_DEMO_SITES=true
   ```

6. Click **"Deploy site"**

7. **Note your frontend URL**:
   - Something like: `https://your-site-name.netlify.app`
   - You can customize this in Site settings → Domain management

### Step 3: Update Backend CORS Settings

1. Go back to Render dashboard
2. Open your backend service
3. Go to **"Environment"**
4. Update `ALLOWED_HOSTS` to include your Netlify URL:
   ```bash
   ALLOWED_HOSTS=https://your-site-name.netlify.app,https://craigleads-backend.onrender.com
   ```
5. Click **"Save Changes"**
6. Backend will automatically redeploy

### Step 4: Test Production Deployment

1. Visit your Netlify URL: `https://your-site-name.netlify.app`
2. Open browser DevTools (F12) → Console tab
3. Verify:
   - ✅ No CSP errors
   - ✅ No CORS errors
   - ✅ API calls are successful (check Network tab)
   - ✅ WebSocket connection established
   - ✅ UI renders correctly
   - ✅ Navigation works
   - ✅ Data loads from backend

---

## Part 4: Post-Deployment Configuration

### Configure Custom Domain (Optional)

#### Backend (Render):
1. Go to your backend service on Render
2. Click **"Settings"** → **"Custom Domain"**
3. Add your domain (e.g., `api.yourdomain.com`)
4. Follow DNS configuration instructions
5. Update frontend environment variables with new domain

#### Frontend (Netlify):
1. Go to Site settings → Domain management
2. Add custom domain
3. Follow DNS configuration instructions
4. SSL will be automatically configured

### Enable Monitoring

#### Render:
- Built-in monitoring available in dashboard
- Set up email/Slack alerts for service health

#### Netlify:
- Enable Netlify Analytics (paid feature)
- Set up build notifications

### Backup Strategy

1. **Database Backups**:
   - Render automatically backs up PostgreSQL databases
   - Manual backups: Use Render dashboard or `pg_dump`

2. **Code Backups**:
   - Your code is on GitHub (already backed up)
   - Tag releases: `git tag v1.0.0 && git push --tags`

---

## Troubleshooting

### Backend Issues

**Problem**: Service fails to start
- Check logs in Render dashboard
- Verify all environment variables are set
- Ensure database migrations ran successfully

**Problem**: Database connection errors
- Verify DATABASE_URL is correct
- Check database is running and accessible
- Review firewall/security group settings

**Problem**: Out of memory errors
- Upgrade to a larger Render plan
- Optimize queries and reduce memory usage

### Frontend Issues

**Problem**: API calls fail with CORS errors
- Verify backend ALLOWED_HOSTS includes frontend URL
- Check frontend VITE_API_URL is correct
- Ensure both URLs use HTTPS

**Problem**: Build fails on Netlify
- Check build logs in Netlify dashboard
- Verify all dependencies are in package.json
- Ensure Node version is 18+

**Problem**: Environment variables not working
- Verify variables are prefixed with `VITE_`
- Re-deploy after changing environment variables
- Check variables are set in Netlify dashboard

### Performance Issues

**Problem**: Slow API responses
- Enable Redis caching
- Optimize database queries
- Consider CDN for static assets

**Problem**: Cold starts on Render (Free tier)
- Upgrade to paid plan for always-on service
- Or implement keep-alive pings

---

## Maintenance

### Regular Updates

1. **Update Dependencies**:
   ```bash
   # Backend
   cd backend
   pip list --outdated
   pip install --upgrade <package>

   # Frontend
   cd frontend
   npm outdated
   npm update
   ```

2. **Security Updates**:
   - Monitor GitHub security alerts
   - Apply patches promptly
   - Test in staging before production

### Monitoring Checklist

- [ ] Check service health daily
- [ ] Review error logs weekly
- [ ] Monitor database size
- [ ] Check Redis memory usage
- [ ] Review API response times
- [ ] Verify backup success

---

## Cost Estimates

### Render (Backend + Database + Redis)

**Free Tier**:
- Web Service: $0 (750 hours/month, sleeps after 15min inactivity)
- PostgreSQL: $0 (Limited storage)
- Redis: $0 (Limited memory)

**Paid Options**:
- Starter Plan: $7/month (Web Service always on)
- Standard PostgreSQL: $7/month (1GB storage)
- Standard Redis: $10/month (25MB memory)

**Recommended for Production**: ~$25-50/month

### Netlify (Frontend)

**Free Tier**:
- 100GB bandwidth/month
- 300 build minutes/month
- Automatic HTTPS
- Global CDN

**Paid Options**:
- Pro Plan: $19/month (more bandwidth, builds, features)

**Recommended**: Free tier is usually sufficient

---

## Security Best Practices

1. **Never commit sensitive data**:
   - Use environment variables for all secrets
   - Add `.env` to `.gitignore` (already done)

2. **Rotate secrets regularly**:
   - Change SECRET_KEY every 90 days
   - Rotate API keys as needed

3. **Monitor for suspicious activity**:
   - Review access logs
   - Set up rate limiting
   - Monitor failed login attempts

4. **Keep software updated**:
   - Apply security patches promptly
   - Update dependencies regularly

5. **Use HTTPS everywhere**:
   - Both Render and Netlify provide free SSL
   - Never use HTTP in production

---

## Support

For issues:
1. Check logs (Render dashboard or Netlify deploy log)
2. Review this guide
3. Check documentation in `/docs`
4. Review code comments
5. Contact your development team

---

## Next Steps

After successful deployment:

1. ✅ Test all features thoroughly
2. ✅ Set up monitoring and alerts
3. ✅ Configure backups
4. ✅ Add custom domain (optional)
5. ✅ Enable AI features (add API keys)
6. ✅ Set up analytics
7. ✅ Create user documentation

Congratulations! Your CraigLeads Pro application is now live! 🎉
