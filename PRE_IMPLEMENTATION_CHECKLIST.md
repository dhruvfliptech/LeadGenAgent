# Pre-Implementation Checklist - FlipTech Pro

**Complete Audit Before Starting Backend Implementation**

---

## Executive Summary

This document consolidates our comprehensive audit findings to ensure we've identified EVERYTHING needed for a fully functional FlipTech Pro application before beginning Phase 1 implementation.

### What We Found
- **300+ API endpoints** identified across 47+ pages and 75+ components
- **6 WebSocket connections** needed for real-time features
- **15 major feature areas** requiring backend support
- **40+ disabled/incomplete features** with working frontend UI
- **Critical gaps**: Authentication, Revenue tracking, Real-time updates

---

## 1. WHAT'S CURRENTLY WORKING (Backend Exists)

### ✅ Functional Features

#### Lead Management (Partial)
- ✅ GET `/api/v1/leads` - List leads with basic filters
- ✅ PUT `/api/v1/leads/{id}` - Update lead
- ✅ POST `/api/v1/leads` - Create lead manually
- ⚠️ Missing: Advanced filtering, bulk operations, tags, notes, enrichment history

#### Craigslist Scraping (Core)
- ✅ POST `/api/v1/scraper/jobs` - Create scrape job
- ✅ GET `/api/v1/scraper/jobs` - List jobs
- ✅ GET `/api/v1/scraper/jobs/{id}` - Job details
- ✅ GET `/api/v1/scraper/categories` - Get categories
- ✅ GET `/api/v1/scraper/queue/status` - Queue status

#### AI Features (Basic)
- ✅ POST `/api/v1/ai-mvp/analyze-website` - Website analysis
- ✅ POST `/api/v1/ai-mvp/generate-email` - Generate email
- ✅ POST `/api/v1/ai-mvp/send-email` - Send email
- ✅ GET `/api/v1/ai-mvp/performance` - Model performance

#### Workflows (n8n Integration)
- ✅ GET `/api/v1/n8n-webhooks/workflows` - List workflows
- ✅ POST `/api/v1/n8n-webhooks/workflows/{id}/activate` - Activate workflow
- ✅ GET `/api/v1/n8n-webhooks/executions` - Execution history

#### Approvals
- ✅ GET `/api/v1/workflow-approvals/pending` - Pending approvals
- ✅ POST `/api/v1/workflow-approvals/{id}/decide` - Approve/reject
- ✅ GET `/api/v1/workflow-approvals/auto-approval/rules` - Get rules

---

## 2. WHAT'S MISSING OR BROKEN

### 🚨 Critical Missing Features

#### 2.1 Authentication & Authorization (P0)
**Status**: ❌ COMPLETELY MISSING

No authentication system exists. The entire application is wide open.

**Required Endpoints**:
```http
POST   /api/v1/auth/login            # User login
POST   /api/v1/auth/register         # User registration
POST   /api/v1/auth/logout           # User logout
POST   /api/v1/auth/refresh          # Refresh token
POST   /api/v1/auth/forgot-password  # Password reset
POST   /api/v1/auth/reset-password   # Reset with token
GET    /api/v1/auth/me               # Get current user
PUT    /api/v1/auth/me               # Update profile
```

**Required Features**:
- JWT token generation and validation
- Password hashing with bcrypt
- Token refresh mechanism
- Role-based access control (admin, user, viewer)
- API key authentication for integrations
- Session management

**Database Tables Needed**:
- `users` - User accounts
- `sessions` - Active sessions
- `api_keys` - API keys for integrations
- `roles` and `permissions` - RBAC tables

---

#### 2.2 Revenue & ROI Tracking (P0)
**Status**: ❌ HARDCODED MOCK DATA

Dashboard shows revenue metrics but ALL data is fake.

**Required Endpoints**:
```http
POST   /api/v1/leads/{id}/mark-converted    # Mark as won
POST   /api/v1/leads/{id}/mark-lost         # Mark as lost
GET    /api/v1/revenue/dashboard            # Revenue overview
GET    /api/v1/revenue/by-source            # Revenue by source
GET    /api/v1/revenue/trends               # Revenue over time
GET    /api/v1/revenue/forecast             # Revenue forecast
GET    /api/v1/costs/breakdown              # Cost breakdown
GET    /api/v1/roi/calculate                # ROI calculation
```

**Database Schema Needed**:
```sql
-- Add to leads table
ALTER TABLE leads ADD COLUMN revenue_amount DECIMAL(10,2);
ALTER TABLE leads ADD COLUMN conversion_date TIMESTAMP;
ALTER TABLE leads ADD COLUMN deal_stage VARCHAR(50);
ALTER TABLE leads ADD COLUMN deal_value DECIMAL(10,2);
ALTER TABLE leads ADD COLUMN expected_close_date DATE;

-- New costs table
CREATE TABLE costs (
  id SERIAL PRIMARY KEY,
  cost_type VARCHAR(50),  -- ai_processing, scraping, email_sending, operating
  amount DECIMAL(10,2),
  currency VARCHAR(3),
  related_entity_type VARCHAR(50),  -- lead, campaign, scrape_job
  related_entity_id INTEGER,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- New conversions table
CREATE TABLE conversions (
  id SERIAL PRIMARY KEY,
  lead_id INTEGER REFERENCES leads(id),
  revenue_amount DECIMAL(10,2),
  conversion_date TIMESTAMP,
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

#### 2.3 Real-Time Updates (P0)
**Status**: ⚠️ PARTIAL - Polling only, no WebSocket

All real-time features use polling (scraper progress, workflow updates, etc.). This is inefficient and doesn't scale.

**Required WebSocket Endpoints**:
```websocket
WS /ws/scraper           # Scrape job progress
WS /ws/workflows         # Workflow execution updates
WS /ws/notifications     # Real-time notifications
WS /ws/conversations     # New conversation replies
WS /ws/campaigns         # Campaign stats updates
WS /ws/demo-sites        # Demo site generation
```

**WebSocket Message Types**:
```typescript
// Scraper updates
{
  type: 'scrape_progress',
  job_id: string,
  status: string,
  progress: number,
  leads_found: number
}

// Workflow updates
{
  type: 'execution_update',
  execution_id: string,
  status: string,
  current_node: string,
  progress: number
}

// Notification
{
  type: 'notification',
  notification_id: string,
  title: string,
  message: string,
  severity: 'info' | 'success' | 'warning' | 'error'
}
```

**Implementation Requirements**:
- FastAPI WebSocket support (already available)
- Redis Pub/Sub for message broadcasting
- Connection management and reconnection logic
- Message queuing for offline clients
- Authentication for WebSocket connections

---

#### 2.4 Phase 3 Features (P1)
**Status**: 🔴 DISABLED - Routers commented out in backend

From `phase3Api.ts`:
```typescript
// These endpoints are DISABLED due to backend router being commented out:
// - Templates: /api/v1/templates/*
// - Rules: /api/v1/rules/*
// - Notifications: /api/v1/notifications/*
// - Schedules: /api/v1/schedules/*
```

**Frontend UI Exists** - Backend Missing:
- ✅ Templates page - Full CRUD UI, bulk actions, preview
- ✅ Rules builder - Visual rule builder, conditions, actions
- ✅ Notifications page - Notification list, preferences
- ✅ Schedule page - Cron builder, execution logs

**Action Required**: Uncomment and implement these routers.

---

#### 2.5 Multi-Source Scraping (P1)
**Status**: ⚠️ UI EXISTS - No Backend

Pages exist for:
- `/scraper/google-maps` - Google Maps scraping
- `/scraper/linkedin` - LinkedIn scraping
- `/scraper/social-media` - Social media scraping
- `/scraper/custom-url` - Custom URL scraping
- `/scraper/audience-builder` - Advanced targeting

**Required Endpoints**:
```http
# Google Maps
POST   /api/v1/google-maps/scrape
GET    /api/v1/google-maps/sources
GET    /api/v1/google-maps/jobs
GET    /api/v1/google-maps/jobs/{id}

# LinkedIn
POST   /api/v1/linkedin/scrape
GET    /api/v1/linkedin/sources
POST   /api/v1/linkedin/auth
GET    /api/v1/linkedin/jobs

# Job Boards
POST   /api/v1/job-boards/scrape
GET    /api/v1/job-boards/sources
GET    /api/v1/job-boards/jobs

# Social Media
POST   /api/v1/social-media/scrape
GET    /api/v1/social-media/platforms

# Custom URL
POST   /api/v1/custom-url/scrape
POST   /api/v1/custom-url/analyze

# Audience Builder
POST   /api/v1/audience-builder/build
GET    /api/v1/audience-builder/audiences
```

---

#### 2.6 Campaign Management (P1)
**Status**: ⚠️ PARTIAL - Basic structure only

**What's Missing**:
- Campaign creation flow
- Recipient selection
- Email sending infrastructure
- Tracking (opens, clicks, replies)
- Campaign analytics
- Test email sending
- Campaign scheduling

**Required Endpoints**:
```http
POST   /api/v1/campaigns              # Create campaign
PUT    /api/v1/campaigns/{id}         # Update campaign
POST   /api/v1/campaigns/{id}/launch  # Launch campaign
POST   /api/v1/campaigns/{id}/pause   # Pause campaign
POST   /api/v1/campaigns/{id}/test    # Send test
GET    /api/v1/campaigns/{id}/stats   # Get statistics
GET    /api/v1/campaigns/{id}/opens   # Open tracking
GET    /api/v1/campaigns/{id}/clicks  # Click tracking
GET    /api/v1/campaigns/{id}/replies # Reply tracking
```

**Email Infrastructure Needed**:
- SMTP configuration and sending
- Email tracking (open/click pixels)
- Bounce handling
- Unsubscribe handling
- SPF/DKIM/DMARC setup
- Email throttling/rate limiting
- Delivery queue with retry logic

---

#### 2.7 Conversation Management (P1)
**Status**: ⚠️ UI EXISTS - Limited Backend

**What Works**:
- Basic conversation list
- Message display

**What's Missing**:
- AI-generated reply suggestions
- Approve/reject suggestions
- Sentiment analysis
- Conversation context
- Mark as read/unread
- Archive conversations
- Reply to conversations

**Required Endpoints**:
```http
GET    /api/v1/conversations
GET    /api/v1/conversations/{id}
GET    /api/v1/conversations/{id}/messages
POST   /api/v1/conversations/{id}/reply
POST   /api/v1/conversations/{id}/generate-response
POST   /api/v1/conversations/suggestions/{id}/approve
POST   /api/v1/conversations/suggestions/{id}/reject
POST   /api/v1/conversations/suggestions/regenerate
PATCH  /api/v1/conversations/{id}/read
PATCH  /api/v1/conversations/{id}/archive
```

---

#### 2.8 Demo Sites & Videos (P2)
**Status**: ⚠️ UI EXISTS - No Backend

Complete UI exists for:
- Demo site generation
- Video creation
- Analytics tracking
- Deployment to Vercel

**Required Endpoints**:
```http
POST   /api/v1/demo-sites              # Generate demo site
GET    /api/v1/demo-sites/{id}         # Get demo site
GET    /api/v1/demo-sites/{id}/status  # Generation status
POST   /api/v1/demo-sites/{id}/deploy  # Deploy to Vercel
GET    /api/v1/demo-sites/{id}/download # Download ZIP

POST   /api/v1/videos/generate          # Generate video
GET    /api/v1/hosted-videos            # List videos
GET    /api/v1/hosted-videos/{id}       # Get video
GET    /api/v1/hosted-videos/{id}/analytics # Video analytics
POST   /api/v1/hosted-videos/{id}/track-view # Track view
```

**External Services Needed**:
- Vercel API integration
- FFmpeg for video processing
- ElevenLabs for voiceover
- CDN for video hosting

---

#### 2.9 AI Gym & A/B Testing (P2)
**Status**: ⚠️ UI EXISTS - No Backend

Complete pages for:
- AI model management
- A/B test creation
- Performance comparison
- Cost tracking

**Required Endpoints**:
```http
GET    /api/v1/ai-gym/models
GET    /api/v1/ai-gym/models/{id}/performance
POST   /api/v1/ai-gym/models/{id}/benchmark

GET    /api/v1/ai-gym/ab-tests
POST   /api/v1/ai-gym/ab-tests
GET    /api/v1/ai-gym/ab-tests/{id}/results
POST   /api/v1/ai-gym/ab-tests/{id}/select-winner
```

---

#### 2.10 Analytics & Reporting (P1)
**Status**: ⚠️ PARTIAL - Mock data

Analytics page exists but shows hardcoded data.

**Required Endpoints**:
```http
GET    /api/v1/analytics/dashboard
GET    /api/v1/analytics/lead-funnel
GET    /api/v1/analytics/trends
GET    /api/v1/analytics/sources
GET    /api/v1/analytics/templates/performance
GET    /api/v1/analytics/locations/performance
POST   /api/v1/exports/analytics
```

---

### 🔧 Supporting Features Missing

#### Tags System (P1)
**Status**: ⚠️ PARTIAL - UI exists, limited backend

```http
GET    /api/v1/tags                    # List all tags
POST   /api/v1/tags                    # Create tag
PUT    /api/v1/tags/{id}               # Update tag
DELETE /api/v1/tags/{id}               # Delete tag
POST   /api/v1/leads/{id}/tags         # Add tag to lead
DELETE /api/v1/leads/{id}/tags/{tag_id} # Remove tag
```

#### Notes & Comments (P1)
**Status**: ❌ MISSING

```http
POST   /api/v1/leads/{id}/notes        # Add note
GET    /api/v1/leads/{id}/notes        # Get notes
PUT    /api/v1/notes/{id}              # Update note
DELETE /api/v1/notes/{id}              # Delete note
```

#### Activity Feed (P1)
**Status**: ❌ PLACEHOLDER ONLY

```http
GET    /api/v1/activity/recent         # Recent activity
GET    /api/v1/activity/by-user        # User activity
GET    /api/v1/activity/by-lead/{id}   # Lead activity
```

#### File Uploads (P1)
**Status**: ⚠️ LIMITED

```http
POST   /api/v1/uploads/csv             # Upload leads CSV
POST   /api/v1/uploads/image           # Upload image
POST   /api/v1/uploads/avatar          # Upload avatar
GET    /api/v1/files/{id}/download     # Download file
```

#### Location Groups (P2)
**Status**: ❌ MISSING (UI disabled)

```http
GET    /api/v1/locations/groups
POST   /api/v1/locations/groups
PUT    /api/v1/locations/groups/{id}
DELETE /api/v1/locations/groups/{id}
```

#### Global Search (P2)
**Status**: ❌ MISSING

```http
GET    /api/v1/search?q=query&type=leads|campaigns|conversations
```

#### Usage Tracking (P3)
**Status**: ❌ MISSING

```http
GET    /api/v1/usage/current           # Current usage
GET    /api/v1/usage/limits            # Account limits
GET    /api/v1/usage/history           # Usage history
```

---

## 3. DATABASE SCHEMA REQUIREMENTS

### 3.1 Existing Tables (Need Expansion)

#### `leads` Table - Add Columns
```sql
ALTER TABLE leads ADD COLUMN IF NOT EXISTS tags VARCHAR(255)[];
ALTER TABLE leads ADD COLUMN IF NOT EXISTS deal_value DECIMAL(10,2);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS deal_stage VARCHAR(50);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS revenue_amount DECIMAL(10,2);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS conversion_date TIMESTAMP;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS expected_close_date DATE;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_contacted_at TIMESTAMP;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS contacted_count INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS qualification_score INTEGER;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_source_metadata JSONB;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS enrichment_status VARCHAR(50);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS enriched_at TIMESTAMP;
```

### 3.2 New Tables Required

#### Authentication & Users
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(255),
  role VARCHAR(50) DEFAULT 'user',
  timezone VARCHAR(100) DEFAULT 'UTC',
  avatar_url TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  email_verified BOOLEAN DEFAULT FALSE,
  last_login_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE sessions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  token VARCHAR(500) UNIQUE NOT NULL,
  refresh_token VARCHAR(500) UNIQUE,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE api_keys (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  key_name VARCHAR(255),
  key_hash VARCHAR(255) UNIQUE NOT NULL,
  key_prefix VARCHAR(20),
  permissions JSONB,
  last_used_at TIMESTAMP,
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### Revenue & Costs
```sql
CREATE TABLE conversions (
  id SERIAL PRIMARY KEY,
  lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
  revenue_amount DECIMAL(10,2) NOT NULL,
  conversion_date TIMESTAMP NOT NULL,
  deal_stage VARCHAR(50),
  notes TEXT,
  created_by INTEGER REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE costs (
  id SERIAL PRIMARY KEY,
  cost_type VARCHAR(50) NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'USD',
  related_entity_type VARCHAR(50),
  related_entity_id INTEGER,
  description TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### Tags & Notes
```sql
CREATE TABLE tags (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL,
  color VARCHAR(20),
  category VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE lead_tags (
  lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
  tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (lead_id, tag_id)
);

CREATE TABLE notes (
  id SERIAL PRIMARY KEY,
  lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  author_id INTEGER REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Campaigns
```sql
CREATE TABLE campaigns (
  id SERIAL PRIMARY KEY,
  campaign_id VARCHAR(100) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  template_id INTEGER REFERENCES templates(id),
  status VARCHAR(50) DEFAULT 'draft',
  scheduled_at TIMESTAMP,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  total_recipients INTEGER DEFAULT 0,
  emails_sent INTEGER DEFAULT 0,
  emails_opened INTEGER DEFAULT 0,
  emails_clicked INTEGER DEFAULT 0,
  emails_replied INTEGER DEFAULT 0,
  emails_bounced INTEGER DEFAULT 0,
  created_by INTEGER REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE campaign_recipients (
  id SERIAL PRIMARY KEY,
  campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
  lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
  status VARCHAR(50) DEFAULT 'pending',
  sent_at TIMESTAMP,
  opened_at TIMESTAMP,
  clicked_at TIMESTAMP,
  replied_at TIMESTAMP,
  bounced_at TIMESTAMP,
  error_message TEXT,
  UNIQUE(campaign_id, lead_id)
);
```

#### Templates
```sql
CREATE TABLE templates (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  subject VARCHAR(500),
  body_html TEXT,
  body_text TEXT,
  category VARCHAR(100),
  tags VARCHAR(100)[],
  variables VARCHAR(100)[],
  is_active BOOLEAN DEFAULT TRUE,
  created_by INTEGER REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE template_performance (
  id SERIAL PRIMARY KEY,
  template_id INTEGER REFERENCES templates(id) ON DELETE CASCADE,
  total_sent INTEGER DEFAULT 0,
  total_opened INTEGER DEFAULT 0,
  total_clicked INTEGER DEFAULT 0,
  total_replied INTEGER DEFAULT 0,
  avg_open_time_minutes INTEGER,
  last_used_at TIMESTAMP,
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Conversations
```sql
CREATE TABLE conversations (
  id SERIAL PRIMARY KEY,
  conversation_id VARCHAR(100) UNIQUE NOT NULL,
  lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
  subject VARCHAR(500),
  status VARCHAR(50) DEFAULT 'active',
  sentiment VARCHAR(50),
  last_message_at TIMESTAMP,
  needs_reply BOOLEAN DEFAULT FALSE,
  assigned_to INTEGER REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE messages (
  id SERIAL PRIMARY KEY,
  conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
  direction VARCHAR(20) NOT NULL,
  from_email VARCHAR(255),
  to_email VARCHAR(255),
  subject VARCHAR(500),
  body_html TEXT,
  body_text TEXT,
  sentiment VARCHAR(50),
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ai_suggestions (
  id SERIAL PRIMARY KEY,
  conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
  message_id INTEGER REFERENCES messages(id),
  suggested_response TEXT NOT NULL,
  sentiment VARCHAR(50),
  confidence_score DECIMAL(3,2),
  status VARCHAR(50) DEFAULT 'pending',
  approved_by INTEGER REFERENCES users(id),
  approved_at TIMESTAMP,
  edited_response TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### Rules & Automation
```sql
CREATE TABLE rules (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  conditions JSONB NOT NULL,
  actions JSONB NOT NULL,
  logic_operator VARCHAR(10) DEFAULT 'AND',
  priority INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_by INTEGER REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE rule_executions (
  id SERIAL PRIMARY KEY,
  rule_id INTEGER REFERENCES rules(id) ON DELETE CASCADE,
  entity_type VARCHAR(50),
  entity_id INTEGER,
  matched BOOLEAN,
  actions_taken JSONB,
  error_message TEXT,
  executed_at TIMESTAMP DEFAULT NOW()
);
```

#### Schedules
```sql
CREATE TABLE schedules (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  cron_expression VARCHAR(100) NOT NULL,
  task_type VARCHAR(50) NOT NULL,
  task_config JSONB,
  is_active BOOLEAN DEFAULT TRUE,
  last_run_at TIMESTAMP,
  next_run_at TIMESTAMP,
  created_by INTEGER REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE schedule_logs (
  id SERIAL PRIMARY KEY,
  schedule_id INTEGER REFERENCES schedules(id) ON DELETE CASCADE,
  status VARCHAR(50) NOT NULL,
  started_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP,
  error_message TEXT,
  results JSONB
);
```

#### Notifications
```sql
CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  type VARCHAR(50) NOT NULL,
  title VARCHAR(255) NOT NULL,
  message TEXT,
  severity VARCHAR(20) DEFAULT 'info',
  is_read BOOLEAN DEFAULT FALSE,
  action_url TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE notification_preferences (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
  email_enabled BOOLEAN DEFAULT TRUE,
  sms_enabled BOOLEAN DEFAULT FALSE,
  in_app_enabled BOOLEAN DEFAULT TRUE,
  notification_types JSONB,
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Activity Log
```sql
CREATE TABLE activity_log (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  action VARCHAR(100) NOT NULL,
  entity_type VARCHAR(50),
  entity_id INTEGER,
  details JSONB,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### Files & Uploads
```sql
CREATE TABLE files (
  id SERIAL PRIMARY KEY,
  filename VARCHAR(255) NOT NULL,
  original_filename VARCHAR(255),
  file_type VARCHAR(100),
  file_size BIGINT,
  storage_path TEXT NOT NULL,
  uploaded_by INTEGER REFERENCES users(id),
  entity_type VARCHAR(50),
  entity_id INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### Demo Sites
```sql
CREATE TABLE demo_sites (
  id SERIAL PRIMARY KEY,
  build_id VARCHAR(100) UNIQUE NOT NULL,
  lead_id INTEGER REFERENCES leads(id),
  target_url TEXT NOT NULL,
  framework VARCHAR(50),
  status VARCHAR(50) DEFAULT 'pending',
  progress_percentage INTEGER DEFAULT 0,
  current_step VARCHAR(255),
  deployment_url TEXT,
  files_generated JSONB,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP
);
```

#### Videos
```sql
CREATE TABLE videos (
  id SERIAL PRIMARY KEY,
  video_id VARCHAR(100) UNIQUE NOT NULL,
  lead_id INTEGER REFERENCES leads(id),
  demo_site_id INTEGER REFERENCES demo_sites(id),
  title VARCHAR(255),
  description TEXT,
  status VARCHAR(50) DEFAULT 'pending',
  storage_url TEXT,
  thumbnail_url TEXT,
  duration_seconds INTEGER,
  file_size BIGINT,
  view_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE video_analytics (
  id SERIAL PRIMARY KEY,
  video_id INTEGER REFERENCES videos(id) ON DELETE CASCADE,
  viewer_ip INET,
  viewer_location VARCHAR(255),
  device_type VARCHAR(50),
  watch_duration_seconds INTEGER,
  watched_at TIMESTAMP DEFAULT NOW()
);
```

#### Webhooks
```sql
CREATE TABLE webhooks (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  url TEXT NOT NULL,
  events VARCHAR(50)[],
  secret VARCHAR(255),
  is_active BOOLEAN DEFAULT TRUE,
  created_by INTEGER REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE webhook_logs (
  id SERIAL PRIMARY KEY,
  webhook_id INTEGER REFERENCES webhooks(id) ON DELETE CASCADE,
  event_type VARCHAR(50) NOT NULL,
  payload JSONB,
  response_status INTEGER,
  response_body TEXT,
  error_message TEXT,
  delivered_at TIMESTAMP DEFAULT NOW()
);
```

---

## 4. INFRASTRUCTURE REQUIREMENTS

### 4.1 Required Services

#### Database
- ✅ PostgreSQL 15+ (already running)
- ✅ Alembic migrations (already configured)
- ⚠️ Need: Connection pooling configuration
- ⚠️ Need: Read replicas for analytics queries

#### Cache & Queue
- ✅ Redis (already running)
- ⚠️ Need: Redis Pub/Sub for WebSocket
- ⚠️ Need: Celery for async tasks
- ⚠️ Need: Celery Beat for scheduled tasks

#### Background Workers
- ❌ Celery workers (not set up)
- ❌ Celery Beat scheduler (not set up)
- ❌ Task queues: high, normal, low priority

#### Email Service
- ❌ SMTP configuration
- ❌ Email provider (SendGrid, Mailgun, or AWS SES)
- ❌ Email tracking service
- ❌ Bounce/complaint handling

#### File Storage
- ❌ S3 or similar for file uploads
- ❌ CDN for serving files
- ❌ Image optimization service

#### Real-time
- ⚠️ WebSocket server (FastAPI supports, needs configuration)
- ❌ Redis Pub/Sub for broadcasting
- ❌ Connection manager

#### External APIs
- ✅ OpenRouter (configured)
- ⚠️ Hunter.io (API key in settings, not implemented)
- ⚠️ Apollo.io (API key in settings, not implemented)
- ⚠️ Clearbit (not implemented)
- ❌ Vercel API (for demo site deployment)
- ❌ ElevenLabs (for video voiceover)

#### Monitoring & Logging
- ❌ Error tracking (Sentry)
- ❌ Logging service (LogDNA, DataDog)
- ❌ Metrics (Prometheus)
- ❌ APM (Application Performance Monitoring)

### 4.2 Configuration Files Needed

#### `.env` Template
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/fliptechpro
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379
REDIS_CHANNEL_PREFIX=fliptechpro

# Authentication
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Email
EMAIL_PROVIDER=sendgrid  # sendgrid, mailgun, smtp, ses
SENDGRID_API_KEY=your-key
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email
SMTP_PASSWORD=your-password
FROM_EMAIL=noreply@fliptechpro.com
FROM_NAME=FlipTech Pro

# AI Services
OPENROUTER_API_KEY=your-key
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key

# Enrichment Services
HUNTER_IO_API_KEY=your-key
APOLLO_IO_API_KEY=your-key
CLEARBIT_API_KEY=your-key

# External Services
VERCEL_API_TOKEN=your-token
ELEVENLABS_API_KEY=your-key
CAPTCHA_API_KEY=your-key

# File Storage
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_S3_BUCKET=fliptechpro-files
AWS_REGION=us-east-1

# n8n
N8N_WEBHOOK_BASE_URL=http://localhost:5678

# Monitoring
SENTRY_DSN=your-dsn
LOG_LEVEL=INFO

# Application
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173,http://localhost:5176
RATE_LIMIT_PER_MINUTE=60
```

#### `celery_config.py`
```python
from celery import Celery
from celery.schedules import crontab

app = Celery(
    'fliptechpro',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

app.conf.task_routes = {
    'tasks.scraper.*': {'queue': 'scraper'},
    'tasks.email.*': {'queue': 'email'},
    'tasks.ai.*': {'queue': 'ai'},
    'tasks.analytics.*': {'queue': 'analytics'}
}

app.conf.beat_schedule = {
    'daily-lead-scoring': {
        'task': 'tasks.ml.score_all_leads',
        'schedule': crontab(hour=9, minute=0)
    },
    'cleanup-old-executions': {
        'task': 'tasks.cleanup.remove_old_executions',
        'schedule': crontab(hour=2, minute=0)
    }
}
```

---

## 5. IMPLEMENTATION PRIORITY MATRIX

### Phase 0: Foundation (Week 1)
**Goal**: Get core infrastructure ready

- [ ] Set up Celery workers and queues
- [ ] Configure Redis Pub/Sub
- [ ] Set up WebSocket infrastructure
- [ ] Database schema migrations (all new tables)
- [ ] `.env` configuration template
- [ ] Docker Compose for local development

### Phase 1: Core Features (Weeks 2-4)
**Goal**: MVP functionality

#### Week 2: Authentication & Users
- [ ] User authentication (login/register/logout)
- [ ] JWT token management
- [ ] Password reset flow
- [ ] User profile management
- [ ] API key management
- [ ] Role-based access control

#### Week 3: Lead Management Complete
- [ ] Advanced lead filtering
- [ ] Tags system
- [ ] Notes/comments
- [ ] Activity timeline
- [ ] Bulk operations
- [ ] Lead enrichment (Hunter.io, Apollo.io)

#### Week 4: Revenue & Analytics
- [ ] Revenue tracking
- [ ] Cost tracking
- [ ] ROI calculations
- [ ] Analytics dashboard
- [ ] Conversion funnel
- [ ] Export functionality

### Phase 2: Communication (Weeks 5-7)
**Goal**: Email and conversation features

#### Week 5: Templates & Campaigns
- [ ] Template CRUD operations
- [ ] Template performance tracking
- [ ] Campaign creation
- [ ] Recipient management
- [ ] Email sending infrastructure

#### Week 6: Campaign Execution
- [ ] Campaign launch/pause/resume
- [ ] Email tracking (opens, clicks)
- [ ] Bounce handling
- [ ] Campaign analytics
- [ ] Test email sending

#### Week 7: Conversations
- [ ] Conversation management
- [ ] AI reply suggestions
- [ ] Approve/reject suggestions
- [ ] Sentiment analysis
- [ ] Real-time updates

### Phase 3: Automation (Weeks 8-10)
**Goal**: Rules, schedules, workflows

#### Week 8: Rules & Auto-Response
- [ ] Rule engine
- [ ] Auto-response system
- [ ] Rule testing
- [ ] Exclude lists

#### Week 9: Schedules
- [ ] Schedule management
- [ ] Cron execution
- [ ] Schedule logs
- [ ] Task types

#### Week 10: Workflows Complete
- [ ] Complete n8n integration
- [ ] Workflow monitoring
- [ ] Error handling
- [ ] Performance optimization

### Phase 4: Multi-Source Scraping (Weeks 11-13)
**Goal**: Additional data sources

- [ ] Google Maps scraper
- [ ] LinkedIn scraper
- [ ] Job boards scraper
- [ ] Social media scraper
- [ ] Custom URL scraper
- [ ] Audience builder

### Phase 5: Content Generation (Weeks 14-15)
**Goal**: Demo sites and videos

- [ ] Demo site generation
- [ ] Vercel deployment
- [ ] Video generation
- [ ] Video analytics
- [ ] Content tracking

### Phase 6: Advanced Features (Weeks 16-17)
**Goal**: AI Gym, approvals, webhooks

- [ ] AI Gym implementation
- [ ] A/B testing framework
- [ ] Approval workflows
- [ ] Webhook management
- [ ] Integration templates

### Phase 7: Polish (Week 18)
**Goal**: Production readiness

- [ ] Real-time notifications
- [ ] Global search
- [ ] Usage tracking
- [ ] Error monitoring
- [ ] Performance optimization
- [ ] API documentation
- [ ] Testing & QA

---

## 6. TESTING REQUIREMENTS

### 6.1 Unit Tests Needed
```python
# Example structure
tests/
├── test_auth/
│   ├── test_login.py
│   ├── test_register.py
│   └── test_token_refresh.py
├── test_leads/
│   ├── test_crud.py
│   ├── test_filtering.py
│   └── test_enrichment.py
├── test_campaigns/
├── test_workflows/
└── test_analytics/
```

### 6.2 Integration Tests
- API endpoint tests
- Database transaction tests
- External API integration tests
- Email sending tests
- WebSocket tests

### 6.3 E2E Tests
- User journey tests
- Critical path tests
- UI integration tests

---

## 7. DOCUMENTATION REQUIREMENTS

### 7.1 API Documentation
- [ ] OpenAPI/Swagger spec
- [ ] Endpoint descriptions
- [ ] Request/response examples
- [ ] Authentication guide
- [ ] Error code reference

### 7.2 Developer Documentation
- [ ] Setup guide
- [ ] Architecture overview
- [ ] Database schema docs
- [ ] Deployment guide
- [ ] Contributing guide

### 7.3 User Documentation
- [ ] User guide
- [ ] Feature tutorials
- [ ] Video walkthroughs
- [ ] FAQ
- [ ] Troubleshooting

---

## 8. DEPLOYMENT CHECKLIST

### 8.1 Production Environment
- [ ] Production database (RDS, Supabase, etc.)
- [ ] Redis cluster
- [ ] Celery workers (multiple instances)
- [ ] Load balancer
- [ ] CDN setup
- [ ] SSL certificates
- [ ] Domain configuration

### 8.2 CI/CD Pipeline
- [ ] GitHub Actions workflow
- [ ] Automated testing
- [ ] Database migrations on deploy
- [ ] Blue-green deployment
- [ ] Rollback procedure

### 8.3 Monitoring Setup
- [ ] Error tracking (Sentry)
- [ ] Logging (DataDog, LogDNA)
- [ ] Uptime monitoring
- [ ] Performance monitoring
- [ ] Alert configuration

### 8.4 Security
- [ ] HTTPS only
- [ ] CORS configuration
- [ ] Rate limiting
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] API key rotation policy
- [ ] Security headers

---

## 9. FINAL CHECKLIST BEFORE STARTING

### Database
- [ ] All schema migrations ready
- [ ] Indexes planned for performance
- [ ] Foreign key constraints defined
- [ ] Default values set correctly

### Backend Structure
- [ ] FastAPI routers organized
- [ ] Pydantic models defined
- [ ] SQLAlchemy models updated
- [ ] Service layer architecture
- [ ] Error handling strategy

### Infrastructure
- [ ] Celery configured
- [ ] Redis Pub/Sub configured
- [ ] WebSocket manager ready
- [ ] Email service configured
- [ ] File storage configured

### External Services
- [ ] All API keys obtained
- [ ] Rate limits understood
- [ ] Quotas checked
- [ ] Test accounts created

### Development Environment
- [ ] Docker Compose updated
- [ ] `.env.example` created
- [ ] Setup script ready
- [ ] README updated

---

## 10. RISK ASSESSMENT

### High Risk Items
1. **Email deliverability** - Complex SPF/DKIM setup
2. **WebSocket scaling** - Connection management at scale
3. **AI cost management** - Potential runaway costs
4. **Data privacy** - GDPR compliance
5. **Rate limiting** - External API limits

### Mitigation Strategies
1. Use established email service (SendGrid/Mailgun)
2. Implement connection pooling and Redis Pub/Sub
3. Set budget alerts and request limits
4. Implement data retention policies
5. Implement exponential backoff and queuing

---

## SUMMARY

### Total Implementation Effort
- **Estimated Time**: 18 weeks (4.5 months)
- **Estimated Endpoints**: 300+
- **Database Tables**: 30+ new tables
- **Major Features**: 15+
- **External Integrations**: 10+

### Critical Path
1. Authentication & Authorization (cannot proceed without this)
2. Revenue tracking (business critical)
3. Real-time updates (user experience critical)
4. Email infrastructure (core functionality)
5. Multi-source scraping (competitive advantage)

### Current Status
- ✅ **25%** of backend implemented (Craigslist scraping, basic leads, workflows)
- ⚠️ **40%** has frontend UI but no backend
- ❌ **35%** completely missing (auth, revenue, real-time)

### Recommendation
**START WITH PHASE 0 & 1**: Foundation and core features. Without authentication and revenue tracking, the application cannot move to production. Everything else can be added incrementally.

---

**Document Version**: 2.0
**Last Updated**: 2025-01-05
**Status**: Ready for Implementation Review
