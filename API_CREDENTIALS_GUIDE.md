# API Credentials Guide

**Last Updated**: November 4, 2025

This document lists all API credentials needed for the Craigslist Lead Generation System to function fully.

---

## Quick Setup Checklist

- [ ] OpenRouter (AI models) - **REQUIRED**
- [ ] ElevenLabs (voiceovers) - Required for Phase 4
- [ ] Vercel (demo hosting) - Required for Phase 3
- [ ] Loom (video hosting) - Optional for Phase 4
- [ ] AWS S3 (storage/video backup) - Optional for Phase 4
- [ ] PostgreSQL database - **REQUIRED**
- [ ] Redis cache - **REQUIRED**
- [ ] Hunter.io (email finder) - Optional for Phase 2
- [ ] Piloterr (LinkedIn scraper) - Optional for Phase 2
- [ ] ScraperAPI (anti-bot) - Optional for Phase 2
- [ ] 2Captcha (CAPTCHA solving) - Optional for Phase 2

---

## 1. Core Services (REQUIRED)

### PostgreSQL Database
**Purpose**: Primary data storage
**Cost**: Free (self-hosted) or $7-20/month (hosted)
**Required For**: All phases

**Setup**:
```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb craigslist_leads
```

**Environment Variables**:
```bash
DATABASE_URL="postgresql://postgres@localhost:5432/craigslist_leads"
```

**Verification**:
```bash
psql -d craigslist_leads -c "SELECT version();"
```

---

### Redis Cache
**Purpose**: Session storage, caching, rate limiting
**Cost**: Free (self-hosted) or $5-15/month (hosted)
**Required For**: All phases

**Setup**:
```bash
# macOS
brew install redis
brew services start redis
```

**Environment Variables**:
```bash
REDIS_URL="redis://localhost:6379"
```

**Verification**:
```bash
redis-cli ping
# Should return: PONG
```

---

### OpenRouter (AI Models)
**Purpose**: AI-powered features (analysis, scripts, improvements)
**Cost**: Pay-per-use, ~$10-50/month depending on volume
**Required For**: Phase 3 (Demo Sites), Phase 4 (Video Scripts)

**Get API Key**:
1. Sign up at https://openrouter.ai/
2. Add credits ($5 minimum)
3. Create API key at https://openrouter.ai/keys

**Environment Variables**:
```bash
OPENROUTER_API_KEY="sk-or-v1-YOUR_KEY_HERE"
OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
```

**Models Used**:
- **Claude Sonnet 4** (high-value leads): $3/million tokens
- **GPT-4 Turbo** (medium-value): $10/million tokens
- **Claude Haiku** (low-value): $0.25/million tokens

**Monthly Cost Estimate**:
- 100 demo sites: ~$20
- 100 video scripts: ~$5
- Total: ~$25/month

**Verification**:
```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer sk-or-v1-YOUR_KEY"
```

---

## 2. Phase 3: Demo Site Builder

### Vercel (Demo Site Deployment)
**Purpose**: Deploy and host demo sites
**Cost**: Free tier (100 deployments/day) or $20/month (Pro)
**Required For**: Phase 3

**Get API Key**:
1. Sign up at https://vercel.com/
2. Go to Settings → Tokens
3. Create new token with full access

**Environment Variables**:
```bash
VERCEL_ENABLED=true
VERCEL_API_TOKEN="your_vercel_token_here"
VERCEL_TEAM_ID=""  # Optional, for team accounts
```

**Free Tier Limits**:
- 100 deployments/day
- 100 GB bandwidth/month
- Automatic HTTPS
- Custom domains (with Pro)

**Monthly Cost**:
- Free: 0-50 demos/day
- Pro ($20/mo): Unlimited demos

**Verification**:
```bash
curl https://api.vercel.com/v2/user \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 3. Phase 4: Video Automation

### ElevenLabs (Text-to-Speech)
**Purpose**: Generate professional voiceovers
**Cost**: $5-99/month depending on usage
**Required For**: Phase 4 (Voice Synthesis)

**Get API Key**:
1. Sign up at https://elevenlabs.io/
2. Go to Profile → API Keys
3. Copy your API key

**Environment Variables**:
```bash
ELEVENLABS_ENABLED=true
ELEVENLABS_API_KEY="your_elevenlabs_api_key"
ELEVENLABS_MODEL_ID="eleven_multilingual_v2"
ELEVENLABS_TIMEOUT_SECONDS=60
ELEVENLABS_MAX_RETRIES=3
ELEVENLABS_CONCURRENT_LIMIT=3
```

**Pricing Tiers**:
- **Free**: 10k chars/month (~7 videos)
- **Starter** ($5/mo): 30k chars/month (~20 videos) = $0.25/video
- **Creator** ($22/mo): 100k chars/month (~70 videos) = $0.31/video
- **Pro** ($99/mo): 500k chars/month (~350 videos) = $0.28/video

**Voice Presets Available**:
- professional_male
- professional_female
- casual_male
- casual_female
- energetic_male
- calm_female

**Monthly Cost Estimate** (100 videos):
- Starter: $5/month (need to upgrade)
- Creator: $22/month (sufficient)
- Pro: $99/month (for high volume)

**Verification**:
```bash
curl https://api.elevenlabs.io/v1/user \
  -H "xi-api-key: YOUR_API_KEY"
```

---

### Loom (Video Hosting - Primary)
**Purpose**: Host and share demo videos with built-in analytics
**Cost**: Free (25 videos/user) or $12/month (unlimited)
**Required For**: Phase 4 (Video Hosting)

**Get API Key**:
1. Sign up at https://loom.com/
2. Go to Settings → Developer
3. Create API key

**Environment Variables**:
```bash
LOOM_ENABLED=true
LOOM_API_KEY="your_loom_api_key"
LOOM_DEFAULT_PRIVACY="unlisted"
LOOM_FOLDER_ID=""  # Optional
```

**Pricing**:
- **Starter** ($8/user/mo): 25 videos per user
- **Business** ($12/user/mo): Unlimited videos
- **Enterprise**: Custom pricing

**Features**:
- Built-in video player
- Viewer analytics
- Engagement metrics
- Shareable links
- Embed codes
- No bandwidth costs

**Monthly Cost** (100 videos):
- Business: $12/month (flat fee)

**Verification**:
```bash
curl https://api.loom.com/v1/videos \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

### AWS S3 (Video Storage - Backup)
**Purpose**: Alternative video hosting and file storage
**Cost**: Pay-per-use, ~$5-20/month
**Required For**: Phase 4 (Video Hosting backup)

**Get Credentials**:
1. Sign up at https://aws.amazon.com/
2. Go to IAM → Users → Create User
3. Attach policy: `AmazonS3FullAccess`
4. Create access key

**Environment Variables**:
```bash
AWS_ENABLED=true
AWS_ACCESS_KEY_ID="your_aws_access_key"
AWS_SECRET_ACCESS_KEY="your_aws_secret"
S3_BUCKET_NAME="craigslist-leads-videos"
S3_REGION="us-east-1"
CLOUDFRONT_DOMAIN=""  # Optional CDN
```

**Pricing**:
- **Storage**: $0.023/GB/month
- **Transfer**: $0.09/GB (first 10 TB)
- **Requests**: $0.0004 per 1,000 PUT

**Cost Example** (100 videos, 1.8 GB total):
- Storage: $0.04/month
- Transfer (500 views): $0.81/month
- Total: ~$0.85/month

**Setup S3 Bucket**:
```bash
aws s3 mb s3://craigslist-leads-videos --region us-east-1
aws s3api put-bucket-cors --bucket craigslist-leads-videos --cors-configuration file://cors.json
```

**Verification**:
```bash
aws s3 ls s3://craigslist-leads-videos
```

---

### FFmpeg (Video Processing)
**Purpose**: Compose and encode videos
**Cost**: Free (open source)
**Required For**: Phase 4 (Video Composer)

**Setup**:
```bash
# macOS
brew install ffmpeg

# Verify
ffmpeg -version
```

**No API key needed** - runs locally

---

### Playwright (Screen Recording)
**Purpose**: Record demo site interactions
**Cost**: Free (open source)
**Required For**: Phase 4 (Screen Recording)

**Setup**:
```bash
pip install playwright
playwright install chromium
```

**No API key needed** - runs locally

---

## 4. Phase 2: Multi-Source Leads (OPTIONAL)

### Hunter.io (Email Finder)
**Purpose**: Find email addresses for leads
**Cost**: Free (100 searches/month) or $49/month (1,000 searches)
**Required For**: Phase 2 (Email Finder)

**Get API Key**:
1. Sign up at https://hunter.io/
2. Go to API → Your API Keys
3. Copy API key

**Environment Variables**:
```bash
HUNTER_IO_ENABLED=true
HUNTER_IO_API_KEY="your_hunter_io_api_key"
```

**Pricing**:
- **Free**: 25 searches/month
- **Starter** ($49/mo): 1,000 searches = $0.049/email
- **Growth** ($99/mo): 5,000 searches = $0.020/email

**Monthly Cost** (500 emails):
- Free: Not sufficient
- Starter: $49/month

**Verification**:
```bash
curl "https://api.hunter.io/v2/account?api_key=YOUR_KEY"
```

---

### Piloterr (LinkedIn Scraper)
**Purpose**: Scrape LinkedIn job postings
**Cost**: $49/month (18k jobs/month)
**Required For**: Phase 2 (LinkedIn)

**Get API Key**:
1. Sign up at https://piloterr.com/
2. Purchase LinkedIn Job Scraper plan
3. Get API credentials from dashboard

**Environment Variables**:
```bash
PILOTERR_ENABLED=true
PILOTERR_API_KEY="your_piloterr_api_key"
PILOTERR_PROJECT_ID="your_project_id"
```

**Pricing**:
- **Basic** ($49/mo): 18k jobs/month (600/day)
- **Pro** ($99/mo): 45k jobs/month (1,500/day)

**Monthly Cost**:
- Basic: $49/month for 600 jobs/day

**Verification**:
Check dashboard at https://piloterr.com/dashboard

---

### ScraperAPI (Anti-Bot Protection)
**Purpose**: Bypass anti-bot detection for web scraping
**Cost**: Free (1,000 requests/month) or $49+/month
**Required For**: Phase 2 (Google Maps scraper)

**Get API Key**:
1. Sign up at https://scraperapi.com/
2. Copy API key from dashboard

**Environment Variables**:
```bash
SCRAPERAPI_ENABLED=false  # Optional
SCRAPERAPI_KEY="your_scraperapi_key"
```

**Pricing**:
- **Free**: 1,000 requests/month
- **Hobby** ($49/mo): 100k requests/month
- **Startup** ($149/mo): 500k requests/month

**Monthly Cost** (optional):
- Free tier sufficient for testing
- $49/month for production

**Verification**:
```bash
curl "http://api.scraperapi.com?api_key=YOUR_KEY&url=https://httpbin.org/ip"
```

---

### 2Captcha (CAPTCHA Solving)
**Purpose**: Solve CAPTCHAs during scraping
**Cost**: Pay-per-use, ~$3-10/month
**Required For**: Phase 2 (Job boards with heavy bot protection)

**Get API Key**:
1. Sign up at https://2captcha.com/
2. Add funds ($3 minimum)
3. Copy API key from dashboard

**Environment Variables**:
```bash
TWOCAPTCHA_ENABLED=false  # Optional
TWOCAPTCHA_API_KEY="your_2captcha_api_key"
```

**Pricing**:
- **reCAPTCHA v2**: $2.99 per 1,000 solves
- **reCAPTCHA v3**: $2.99 per 1,000 solves
- **hCaptcha**: $2.99 per 1,000 solves

**Monthly Cost** (100 CAPTCHAs):
- ~$0.30/month (very low cost)

**Verification**:
```bash
curl "http://2captcha.com/res.php?key=YOUR_KEY&action=getbalance"
```

---

## 5. Environment Variables Summary

### Complete .env File Template

```bash
# =====================================================
# CORE SERVICES (REQUIRED)
# =====================================================

# Database
DATABASE_URL="postgresql://postgres@localhost:5432/craigslist_leads"

# Redis
REDIS_URL="redis://localhost:6379"

# OpenRouter (AI Models)
OPENROUTER_API_KEY="sk-or-v1-YOUR_KEY_HERE"
OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"

# =====================================================
# PHASE 3: DEMO SITE BUILDER
# =====================================================

# Vercel (Demo Hosting)
VERCEL_ENABLED=true
VERCEL_API_TOKEN="your_vercel_token_here"
VERCEL_TEAM_ID=""

# =====================================================
# PHASE 4: VIDEO AUTOMATION
# =====================================================

# ElevenLabs (Voiceover)
ELEVENLABS_ENABLED=true
ELEVENLABS_API_KEY="your_elevenlabs_api_key"
ELEVENLABS_MODEL_ID="eleven_multilingual_v2"
ELEVENLABS_TIMEOUT_SECONDS=60
ELEVENLABS_MAX_RETRIES=3
ELEVENLABS_CONCURRENT_LIMIT=3

# Loom (Video Hosting - Primary)
LOOM_ENABLED=true
LOOM_API_KEY="your_loom_api_key"
LOOM_DEFAULT_PRIVACY="unlisted"
LOOM_FOLDER_ID=""

# AWS S3 (Video Storage - Backup)
AWS_ENABLED=true
AWS_ACCESS_KEY_ID="your_aws_access_key"
AWS_SECRET_ACCESS_KEY="your_aws_secret"
S3_BUCKET_NAME="craigslist-leads-videos"
S3_REGION="us-east-1"
CLOUDFRONT_DOMAIN=""

# Storage Paths
VOICEOVER_STORAGE_PATH="./storage/voiceovers"
RECORDING_STORAGE_PATH="./storage/recordings"
VIDEO_STORAGE_PATH="./storage/composed_videos"

# =====================================================
# PHASE 2: MULTI-SOURCE LEADS (OPTIONAL)
# =====================================================

# Hunter.io (Email Finder)
HUNTER_IO_ENABLED=false
HUNTER_IO_API_KEY=""

# Piloterr (LinkedIn)
PILOTERR_ENABLED=false
PILOTERR_API_KEY=""
PILOTERR_PROJECT_ID=""

# ScraperAPI (Anti-Bot)
SCRAPERAPI_ENABLED=false
SCRAPERAPI_KEY=""

# 2Captcha (CAPTCHA Solving)
TWOCAPTCHA_ENABLED=false
TWOCAPTCHA_API_KEY=""

# =====================================================
# APPLICATION SETTINGS
# =====================================================

# Environment
ENVIRONMENT="development"
DEBUG=true
LOG_LEVEL="INFO"
SECRET_KEY="your-secret-key-here-change-in-production"

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

---

## 6. Cost Summary

### Minimum Viable Setup (MVP)
**Monthly Total: ~$0** (free tiers only)

| Service | Cost | Notes |
|---------|------|-------|
| PostgreSQL | $0 | Self-hosted |
| Redis | $0 | Self-hosted |
| OpenRouter | ~$25 | Pay-per-use |
| **Total** | **~$25/month** | Basic functionality |

---

### Phase 3 Production Setup
**Monthly Total: ~$45/month**

| Service | Cost | Notes |
|---------|------|-------|
| PostgreSQL | $0 | Self-hosted |
| Redis | $0 | Self-hosted |
| OpenRouter | ~$25 | AI features |
| Vercel | $20 | Pro plan (unlimited demos) |
| **Total** | **~$45/month** | Demo sites enabled |

---

### Phase 4 Full Production Setup
**Monthly Total: ~$158/month** (100 videos/month)

| Service | Cost | Notes |
|---------|------|-------|
| PostgreSQL | $0 | Self-hosted |
| Redis | $0 | Self-hosted |
| OpenRouter | ~$30 | AI + video scripts |
| Vercel | $20 | Demo hosting |
| ElevenLabs | $22 | Creator plan (70 videos) |
| Loom | $12 | Business plan |
| AWS S3 | ~$5 | Storage backup |
| **Total** | **~$89/month** | Full video automation |

---

### Enterprise Setup with All Features
**Monthly Total: ~$268/month** (high volume)

| Service | Cost | Notes |
|---------|------|-------|
| PostgreSQL | $20 | Hosted (DigitalOcean) |
| Redis | $15 | Hosted (Redis Cloud) |
| OpenRouter | ~$50 | High volume |
| Vercel | $20 | Pro plan |
| ElevenLabs | $99 | Pro plan (350 videos) |
| Loom | $12 | Business plan |
| AWS S3 | ~$10 | Storage + CDN |
| Hunter.io | $49 | Email finder |
| Piloterr | $49 | LinkedIn scraper |
| ScraperAPI | $0 | Free tier |
| 2Captcha | $3 | CAPTCHA solving |
| **Total** | **~$327/month** | All features enabled |

---

## 7. Setup Priority

### Phase 1: Get Started (Day 1)
1. ✅ PostgreSQL (free, local)
2. ✅ Redis (free, local)
3. ✅ OpenRouter ($5 credit to start)

**Cost**: $5 one-time
**Result**: Core system functional

---

### Phase 2: Enable Demo Sites (Week 1)
4. ✅ Vercel (free tier, upgrade to Pro later)

**Cost**: $0 (free tier) or $20/month (Pro)
**Result**: Can create and deploy demo sites

---

### Phase 3: Enable Video Automation (Week 2)
5. ✅ ElevenLabs ($5-22/month)
6. ✅ Loom ($12/month) OR AWS S3 ($5/month)
7. ✅ FFmpeg (free, install locally)
8. ✅ Playwright (free, install locally)

**Cost**: $17-34/month
**Result**: Full video generation pipeline

---

### Phase 4: Optimize Lead Generation (Month 2)
9. ⚪ Hunter.io ($49/month) - for email finding
10. ⚪ Piloterr ($49/month) - for LinkedIn scraping
11. ⚪ ScraperAPI (free tier) - for anti-bot
12. ⚪ 2Captcha (~$3/month) - for CAPTCHAs

**Cost**: $0-101/month (all optional)
**Result**: Maximum lead volume

---

## 8. Quick Verification Script

Save as `verify_credentials.sh`:

```bash
#!/bin/bash

echo "🔍 Verifying API Credentials..."
echo ""

# PostgreSQL
echo "📊 PostgreSQL:"
psql -d craigslist_leads -c "SELECT 'Connected ✅'" 2>/dev/null || echo "❌ Not connected"
echo ""

# Redis
echo "💾 Redis:"
redis-cli ping 2>/dev/null || echo "❌ Not running"
echo ""

# OpenRouter
echo "🤖 OpenRouter:"
if [ -n "$OPENROUTER_API_KEY" ]; then
    curl -s https://openrouter.ai/api/v1/models \
      -H "Authorization: Bearer $OPENROUTER_API_KEY" | grep -q "models" && echo "✅ Valid" || echo "❌ Invalid"
else
    echo "❌ Not configured"
fi
echo ""

# Vercel
echo "🚀 Vercel:"
if [ -n "$VERCEL_API_TOKEN" ]; then
    curl -s https://api.vercel.com/v2/user \
      -H "Authorization: Bearer $VERCEL_API_TOKEN" | grep -q "id" && echo "✅ Valid" || echo "❌ Invalid"
else
    echo "⚪ Not configured (optional)"
fi
echo ""

# ElevenLabs
echo "🎙️ ElevenLabs:"
if [ -n "$ELEVENLABS_API_KEY" ]; then
    curl -s https://api.elevenlabs.io/v1/user \
      -H "xi-api-key: $ELEVENLABS_API_KEY" | grep -q "subscription" && echo "✅ Valid" || echo "❌ Invalid"
else
    echo "⚪ Not configured (optional)"
fi
echo ""

# FFmpeg
echo "🎬 FFmpeg:"
ffmpeg -version >/dev/null 2>&1 && echo "✅ Installed" || echo "❌ Not installed"
echo ""

echo "✅ Verification complete!"
```

Run with:
```bash
chmod +x verify_credentials.sh
source .env && ./verify_credentials.sh
```

---

## 9. Getting Started Checklist

### Immediate Setup (Required)
- [ ] Install PostgreSQL and create database
- [ ] Install Redis and start service
- [ ] Sign up for OpenRouter and add $5 credit
- [ ] Copy API key to `.env` file
- [ ] Run database migrations: `alembic upgrade head`
- [ ] Start backend: `./start_backend.sh`
- [ ] Start frontend: `./start_frontend.sh`
- [ ] Test at http://localhost:5173

### Phase 3 Setup (Demo Sites)
- [ ] Sign up for Vercel account
- [ ] Create API token
- [ ] Add to `.env` file
- [ ] Test demo site deployment

### Phase 4 Setup (Videos)
- [ ] Sign up for ElevenLabs (choose plan)
- [ ] Sign up for Loom OR configure AWS S3
- [ ] Install FFmpeg: `brew install ffmpeg`
- [ ] Install Playwright: `playwright install chromium`
- [ ] Create storage directories
- [ ] Test video generation

---

## 10. Troubleshooting

### "Connection refused" errors
- ✅ Check PostgreSQL is running: `brew services list`
- ✅ Check Redis is running: `redis-cli ping`

### "Invalid API key" errors
- ✅ Verify key in `.env` file (no quotes, no spaces)
- ✅ Check key hasn't expired
- ✅ Verify account has credits/active subscription

### "Quota exceeded" errors
- ✅ Check usage in provider dashboard
- ✅ Upgrade plan or add credits
- ✅ Enable fallback providers (S3 instead of Loom)

### "FFmpeg not found" errors
- ✅ Install: `brew install ffmpeg`
- ✅ Verify: `ffmpeg -version`
- ✅ Restart backend after installing

---

## 11. Support Resources

### OpenRouter
- Dashboard: https://openrouter.ai/
- Docs: https://openrouter.ai/docs
- Discord: https://discord.gg/openrouter

### Vercel
- Dashboard: https://vercel.com/dashboard
- Docs: https://vercel.com/docs
- Support: https://vercel.com/support

### ElevenLabs
- Dashboard: https://elevenlabs.io/
- Docs: https://elevenlabs.io/docs
- Discord: https://discord.gg/elevenlabs

### Loom
- Dashboard: https://loom.com/
- Docs: https://dev.loom.com/
- Support: support@loom.com

### AWS S3
- Console: https://console.aws.amazon.com/s3/
- Docs: https://docs.aws.amazon.com/s3/
- Support: https://aws.amazon.com/support/

---

**Last Updated**: November 4, 2025
**Maintained By**: Development Team
**Next Review**: When adding new integrations
