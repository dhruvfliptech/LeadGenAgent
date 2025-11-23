# Production Deployment Guide

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Database Migration](#database-migration)
4. [Security Configuration](#security-configuration)
5. [Deployment Procedures](#deployment-procedures)
6. [Monitoring Setup](#monitoring-setup)
7. [Rollback Procedures](#rollback-procedures)
8. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### Infrastructure Requirements
- [ ] PostgreSQL 14+ database server (with pgvector extension)
- [ ] Redis 6+ server for caching and background jobs
- [ ] Node.js 18+ for frontend build
- [ ] Python 3.11+ for backend
- [ ] Minimum 4GB RAM, 2 CPU cores
- [ ] 50GB+ disk space
- [ ] SSL/TLS certificates for HTTPS
- [ ] Domain name with DNS configured

### External Services
- [ ] OpenAI/Anthropic API key (for AI features)
- [ ] ElevenLabs API key (for voice synthesis - optional)
- [ ] AWS S3 bucket (for video hosting - optional)
- [ ] Email provider (SMTP, SendGrid, Mailgun, or Resend)
- [ ] 2Captcha API key (for email extraction - optional)
- [ ] LinkedIn API credentials (optional)
- [ ] Hunter.io API key (for email finder - optional)
- [ ] N8N instance (for workflow automation - optional)

### Code Preparation
- [ ] All tests passing (`pytest backend/tests/`)
- [ ] Frontend build succeeds (`npm run build`)
- [ ] No security vulnerabilities (`npm audit`, `safety check`)
- [ ] Database migrations reviewed and tested
- [ ] Environment variables documented
- [ ] Backup and rollback procedures tested

### Security Checklist
- [ ] Secrets rotated (SECRET_KEY, API keys)
- [ ] HTTPS enforced on all endpoints
- [ ] CORS configured with specific allowed origins
- [ ] Rate limiting enabled
- [ ] Database credentials secured
- [ ] File upload limits configured
- [ ] Input validation reviewed
- [ ] SQL injection prevention verified
- [ ] XSS protection enabled

---

## Environment Setup

### 1. Production Environment Variables

Copy the production template and fill in values:

```bash
cp .env.production.example .env.production
```

#### Critical Production Variables

```bash
# REQUIRED: Set environment to production
ENVIRONMENT=production
DEBUG=false

# REQUIRED: Generate secure secret key
# Run: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=<your-secure-secret-key>

# REQUIRED: Database configuration
DATABASE_URL=postgresql://user:password@host:5432/craigslist_leads
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# REQUIRED: Redis configuration
REDIS_URL=redis://user:password@host:6379
REDIS_DB=0

# REQUIRED: CORS - NO wildcards or localhost in production
ALLOWED_HOSTS=https://yourdomain.com,https://api.yourdomain.com

# REQUIRED: API rate limiting
RATE_LIMIT_PER_MINUTE=60
```

#### AI Services Configuration

```bash
# AI Provider (choose one or multiple)
AI_PROVIDER=openai  # openai, anthropic, openrouter

# OpenAI Configuration
OPENAI_API_KEY=sk-...

# Anthropic Configuration (Claude)
ANTHROPIC_API_KEY=sk-ant-...

# OpenRouter (unified API for multiple models)
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

#### Email Configuration

```bash
# Email Provider
EMAIL_PROVIDER=smtp  # smtp, sendgrid, mailgun, resend

# SMTP Configuration (Gmail, Outlook, etc.)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# Email Sender Details
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=Your Company
EMAIL_REPLY_TO=support@yourdomain.com
```

#### Optional Services

```bash
# Video Creation System (Phase 4)
ELEVENLABS_API_KEY=your_elevenlabs_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_S3_BUCKET=your-video-bucket
AWS_S3_REGION=us-east-1

# N8N Workflow Automation (Phase 6)
N8N_API_URL=https://your-n8n-instance.com/api/v1
N8N_API_KEY=your_n8n_api_key
N8N_WEBHOOK_SECRET=your_webhook_secret

# Email Finder Services
HUNTER_IO_API_KEY=your_hunter_key
ROCKETREACH_API_KEY=your_rocketreach_key

# LinkedIn Integration
LINKEDIN_API_KEY=your_piloterr_or_scraperapi_key
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret

# Vercel Deployment
VERCEL_API_TOKEN=your_vercel_token
VERCEL_TEAM_ID=your_team_id
```

### 2. Validate Configuration

Run the configuration validator:

```bash
python backend/scripts/validate_config.py --env production
```

This checks:
- All required variables are set
- No default/insecure values in production
- Service connectivity (database, Redis, external APIs)
- SSL/TLS configuration

---

## Database Migration

### 1. Backup Existing Database

**CRITICAL: Always backup before migrations**

```bash
# PostgreSQL backup
pg_dump -h localhost -U postgres -d craigslist_leads -F c -f backup_$(date +%Y%m%d_%H%M%S).dump

# Alternative: SQL format
pg_dump -h localhost -U postgres -d craigslist_leads > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Enable PostgreSQL Extensions

```bash
# Connect to database as superuser
psql -h localhost -U postgres -d craigslist_leads

# Enable pgvector extension (required for AI/ML features)
CREATE EXTENSION IF NOT EXISTS vector;

# Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';

# Exit
\q
```

### 3. Run Database Migrations

#### Using Alembic (Recommended)

```bash
cd backend

# Set production database URL
export DATABASE_URL="postgresql://user:password@host:5432/craigslist_leads"

# Check current migration version
alembic current

# Review pending migrations
alembic history

# Run all pending migrations
alembic upgrade head

# Verify migration success
alembic current
```

#### Manual SQL Execution (Alternative)

```bash
# Execute migrations in order
psql -h host -U user -d craigslist_leads -f backend/migrations/002_add_demo_sites.sql
psql -h host -U user -d craigslist_leads -f backend/migrations/005_webhook_tables.sql
```

### 4. Verify Database Schema

```bash
# Run verification script
python backend/scripts/verify_schema.py

# Check table counts
psql -h host -U user -d craigslist_leads -c "\dt"

# Verify critical tables exist
psql -h host -U user -d craigslist_leads -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
```

### 5. Initial Data Seeding (Optional)

```bash
# Seed reference data (locations, categories, templates)
python backend/scripts/seed_data.py --env production

# Create admin user
python backend/scripts/create_admin.py --email admin@yourdomain.com
```

---

## Security Configuration

### 1. Generate Secure Secrets

```bash
# SECRET_KEY (FastAPI JWT signing)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# N8N Webhook Secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Credential Encryption Key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. SSL/TLS Configuration

#### Option A: Nginx Reverse Proxy (Recommended)

```nginx
# /etc/nginx/sites-available/craigslist-leads

upstream backend {
    server 127.0.0.1:8000;
    keepalive 64;
}

upstream frontend {
    server 127.0.0.1:3000;
    keepalive 64;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # API Backend
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket Support
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files (if serving from backend)
    location /static/ {
        alias /var/www/craigslist-leads/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;
    limit_req zone=api_limit burst=10 nodelay;
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/craigslist-leads /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Option B: Let's Encrypt (Free SSL)

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (cron job)
sudo certbot renew --dry-run
```

### 3. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH
sudo ufw enable

# Deny direct access to backend/frontend ports
sudo ufw deny 8000/tcp
sudo ufw deny 3000/tcp
```

### 4. Rate Limiting

Configured in backend/app/core/rate_limiter.py:

```python
# Already configured in settings
RATE_LIMIT_PER_MINUTE=60
```

For additional protection, use Nginx rate limiting (shown above) or Cloudflare.

---

## Deployment Procedures

### Initial Deployment

#### 1. Backend Deployment

```bash
# Run deployment script
./scripts/deploy_backend.sh production

# This script will:
# - Pull latest code from Git
# - Install Python dependencies
# - Run database migrations
# - Restart backend service
# - Run health checks
```

#### 2. Frontend Deployment

```bash
# Run deployment script
./scripts/deploy_frontend.sh production

# This script will:
# - Pull latest code from Git
# - Install npm dependencies
# - Build production bundle
# - Deploy to static hosting or update proxy
# - Run health checks
```

#### 3. Background Services

```bash
# Start Celery workers (for background tasks)
./backend/start_celery_worker.sh

# Start Celery beat (for scheduled tasks)
./backend/start_celery_beat.sh

# Start Flower (Celery monitoring - optional)
./backend/start_flower.sh
```

### Zero-Downtime Deployment (Blue-Green)

#### Setup

1. **Prepare two environments:**
   - Blue: Currently active production
   - Green: New version to deploy

2. **Load balancer configuration:**
   - Nginx upstream with multiple servers
   - Health check endpoint: `/health`

#### Deployment Process

```bash
# 1. Deploy to Green environment
./scripts/deploy_backend.sh green
./scripts/deploy_frontend.sh green

# 2. Run health checks on Green
./scripts/health_check.sh green

# 3. If healthy, switch traffic to Green
./scripts/switch_traffic.sh green

# 4. Monitor Green for 5-10 minutes
./scripts/monitor.sh green

# 5. If stable, decommission Blue
# If issues, rollback to Blue
./scripts/rollback.sh blue
```

### Rolling Deployment

For gradual rollout:

```bash
# 1. Deploy to 10% of servers
./scripts/rolling_deploy.sh --percentage 10

# 2. Monitor metrics for 15 minutes
./scripts/monitor.sh --duration 900

# 3. If stable, deploy to 50%
./scripts/rolling_deploy.sh --percentage 50

# 4. Monitor again
./scripts/monitor.sh --duration 900

# 5. Deploy to remaining servers
./scripts/rolling_deploy.sh --percentage 100
```

---

## Monitoring Setup

### 1. Application Logging

#### Backend Logging Configuration

```python
# backend/app/core/config.py
LOG_LEVEL=INFO  # Use INFO in production (not DEBUG)
```

Logs written to:
- `logs/app.log` - Application logs
- `logs/error.log` - Error logs
- `logs/access.log` - Access logs

#### Log Rotation

```bash
# /etc/logrotate.d/craigslist-leads

/var/log/craigslist-leads/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    sharedscripts
    postrotate
        systemctl reload craigslist-backend
    endscript
}
```

### 2. Health Check Endpoints

#### Backend Health Check

```bash
# Basic health check
curl https://api.yourdomain.com/health

# Detailed system info
curl https://api.yourdomain.com/system/info
```

Expected response:

```json
{
  "status": "healthy",
  "timestamp": "2025-11-05T10:30:00Z",
  "version": "2.0.0",
  "services": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"}
  },
  "features": {
    "auto_responder": true,
    "rule_engine": true
  }
}
```

### 3. Monitoring Tools

#### Prometheus Metrics (Recommended)

Install Prometheus exporter:

```bash
pip install prometheus-fastapi-instrumentator
```

Configure in backend/app/main.py:

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

Metrics available at: `https://api.yourdomain.com/metrics`

#### Grafana Dashboards

1. Install Grafana
2. Add Prometheus data source
3. Import dashboard: https://grafana.com/grafana/dashboards/

Key metrics to monitor:
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Database connection pool usage
- Redis connection status
- Celery queue length
- Memory usage
- CPU usage

### 4. Alerting

#### Email Alerts

Configure in `.env.production`:

```bash
# Error notifications
ERROR_NOTIFICATION_EMAIL=ops@yourdomain.com
CRITICAL_ERROR_THRESHOLD=10  # Alert after 10 errors in 1 minute
```

#### Slack Alerts

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_ALERT_CHANNEL=#ops-alerts
```

#### PagerDuty Integration

```bash
PAGERDUTY_API_KEY=your_pagerduty_key
PAGERDUTY_SERVICE_ID=your_service_id
```

### 5. Database Monitoring

```bash
# PostgreSQL slow query log
ALTER SYSTEM SET log_min_duration_statement = 1000;  # Log queries > 1s
SELECT pg_reload_conf();

# Connection monitoring
SELECT count(*) FROM pg_stat_activity;

# Table size monitoring
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Rollback Procedures

### Automatic Rollback

The deployment scripts include automatic rollback on failure:

```bash
./scripts/deploy_backend.sh production

# If deployment fails, automatically rolls back to previous version
# Check logs: tail -f logs/deployment.log
```

### Manual Rollback

#### 1. Rollback Backend

```bash
# Rollback to previous version
./scripts/rollback.sh backend --version v1.9.0

# Or rollback to last known good version
./scripts/rollback.sh backend --last-good
```

#### 2. Rollback Database

```bash
# Rollback migrations
cd backend
alembic downgrade -1  # Rollback one migration
alembic downgrade <revision>  # Rollback to specific version

# Restore from backup (if needed)
pg_restore -h localhost -U postgres -d craigslist_leads backup_20251105.dump
```

#### 3. Rollback Frontend

```bash
# Rollback frontend to previous version
./scripts/rollback.sh frontend --version v1.9.0
```

### Emergency Rollback (Full System)

```bash
# Complete system rollback
./scripts/rollback.sh --all --emergency

# This will:
# 1. Stop all services
# 2. Restore database from last backup
# 3. Rollback backend to last stable version
# 4. Rollback frontend to last stable version
# 5. Restart all services
# 6. Run health checks
```

### Rollback Verification

```bash
# Verify rollback success
./scripts/health_check.sh production

# Check application version
curl https://api.yourdomain.com/ | jq '.version'

# Check database migration version
cd backend && alembic current
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failures

**Symptom:** `FATAL: too many connections`

**Solution:**

```bash
# Check current connections
psql -h host -U user -d craigslist_leads -c "SELECT count(*) FROM pg_stat_activity;"

# Reduce connection pool size in .env
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=5

# Restart backend
sudo systemctl restart craigslist-backend
```

#### 2. Redis Connection Issues

**Symptom:** `Error: Redis connection refused`

**Solution:**

```bash
# Check Redis status
redis-cli ping

# Verify Redis URL
echo $REDIS_URL

# Restart Redis
sudo systemctl restart redis

# Check Redis logs
sudo journalctl -u redis -n 100
```

#### 3. Migration Failures

**Symptom:** `alembic.util.exc.CommandError: Can't locate revision`

**Solution:**

```bash
# Check migration history
cd backend
alembic history

# Stamp database with current version (if migrations were applied manually)
alembic stamp head

# Force upgrade
alembic upgrade head --sql > migration.sql
psql -h host -U user -d craigslist_leads -f migration.sql
```

#### 4. High Memory Usage

**Symptom:** Server running out of memory

**Solution:**

```bash
# Check memory usage
free -h
htop

# Reduce worker processes
# In .env
CELERY_WORKER_CONCURRENCY=2  # Reduce from 4

# Restart workers
sudo systemctl restart craigslist-celery
```

#### 5. SSL Certificate Issues

**Symptom:** `SSL: CERTIFICATE_VERIFY_FAILED`

**Solution:**

```bash
# Renew Let's Encrypt certificate
sudo certbot renew --force-renewal

# Check certificate expiration
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates

# Reload Nginx
sudo systemctl reload nginx
```

#### 6. Frontend Build Failures

**Symptom:** `Error: JavaScript heap out of memory`

**Solution:**

```bash
# Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=4096"

# Rebuild
cd frontend
npm run build
```

#### 7. Background Jobs Not Running

**Symptom:** Celery tasks stuck in queue

**Solution:**

```bash
# Check Celery worker status
celery -A celery_app inspect active

# Restart workers
sudo systemctl restart craigslist-celery

# Check Flower dashboard
http://yourdomain.com:5555

# Purge stuck tasks (CAUTION)
celery -A celery_app purge
```

### Performance Issues

#### Slow Database Queries

```bash
# Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;

# Analyze slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

# Create indexes (if needed)
# Check backend/migrations/ for index creation scripts
```

#### High API Latency

```bash
# Check Nginx access logs
tail -f /var/log/nginx/access.log

# Check backend performance
curl -w "@curl-format.txt" -o /dev/null -s https://api.yourdomain.com/health

# Increase workers (if CPU available)
# In systemd service file: --workers 4
```

### Debugging Production Issues

```bash
# Enable debug logging temporarily (NOT recommended for extended periods)
# In .env.production
LOG_LEVEL=DEBUG

# Restart backend
sudo systemctl restart craigslist-backend

# Monitor logs in real-time
tail -f logs/app.log | grep ERROR

# Revert to INFO logging when done
LOG_LEVEL=INFO
sudo systemctl restart craigslist-backend
```

### Getting Help

1. **Check logs:** `tail -f logs/app.log`
2. **Run health check:** `./scripts/health_check.sh`
3. **Check service status:** `sudo systemctl status craigslist-backend`
4. **Review recent changes:** `git log --oneline -10`
5. **Contact support:** Support documentation or issue tracker

---

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily
- [ ] Check error logs for anomalies
- [ ] Monitor disk space usage
- [ ] Review performance metrics

#### Weekly
- [ ] Review and archive old logs
- [ ] Check database size and vacuum if needed
- [ ] Update dependency security patches
- [ ] Review backup integrity

#### Monthly
- [ ] Update dependencies (minor versions)
- [ ] Review and optimize database indexes
- [ ] Security audit
- [ ] Performance review and optimization

### Database Maintenance

```bash
# Vacuum database (reclaim space)
vacuumdb -h host -U user -d craigslist_leads --analyze --verbose

# Reindex database (improve query performance)
reindexdb -h host -U user -d craigslist_leads

# Analyze tables (update statistics)
psql -h host -U user -d craigslist_leads -c "ANALYZE;"
```

### Backup Procedures

```bash
# Automated daily backups (cron job)
0 2 * * * /usr/local/bin/backup_database.sh

# Backup script (backup_database.sh)
#!/bin/bash
BACKUP_DIR="/backups/craigslist-leads"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U postgres -d craigslist_leads -F c -f $BACKUP_DIR/backup_$DATE.dump

# Retain backups for 30 days
find $BACKUP_DIR -name "backup_*.dump" -mtime +30 -delete
```

---

## Security Hardening

### 1. Keep Dependencies Updated

```bash
# Backend
cd backend
pip list --outdated
pip install --upgrade <package>

# Frontend
cd frontend
npm audit
npm audit fix
npm update
```

### 2. Regular Security Scans

```bash
# Python security check
pip install safety
safety check

# Node.js security check
npm audit

# Penetration testing (use tools like OWASP ZAP)
```

### 3. Access Control

```bash
# Limit SSH access
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no

# Use SSH keys only
# Limit database access by IP
# PostgreSQL: pg_hba.conf
host    all    all    10.0.0.0/8    md5
```

---

## Performance Optimization

### Backend Optimization

```python
# Enable caching in .env
REDIS_CACHE_ENABLED=true
CACHE_TTL=3600

# Increase worker processes
# Systemd service: --workers 4

# Enable compression
# Already configured in main.py: GZipMiddleware
```

### Database Optimization

```sql
-- Add indexes for frequently queried fields
CREATE INDEX CONCURRENTLY idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX CONCURRENTLY idx_leads_status ON leads(status);
CREATE INDEX CONCURRENTLY idx_leads_source ON leads(source);

-- Partition large tables (if > 10M rows)
-- See PostgreSQL partitioning documentation
```

### Frontend Optimization

```bash
# Code splitting (already configured in Vite)
# Enable CDN for static assets
# Implement service workers for offline support
```

---

## Compliance and Auditing

### GDPR Compliance

- [ ] Data retention policies configured
- [ ] User data export functionality
- [ ] Right to deletion implemented
- [ ] Privacy policy updated
- [ ] Cookie consent implemented

### Audit Logging

```python
# Enable audit logging in .env
AUDIT_LOG_ENABLED=true
AUDIT_LOG_RETENTION_DAYS=90

# Logs all:
# - User authentication events
# - Data access/modifications
# - Administrative actions
```

### Data Retention

```bash
# Configure retention policies
LEAD_RETENTION_DAYS=365
LOG_RETENTION_DAYS=90
EXPORT_RETENTION_DAYS=30

# Automated cleanup (cron job)
0 3 * * * python backend/scripts/cleanup_old_data.py
```

---

## Disaster Recovery

### Backup Strategy

1. **Database:** Daily full backups, hourly incremental
2. **Files:** Daily backups to S3/cloud storage
3. **Code:** Git repository (multiple remotes)
4. **Configuration:** Encrypted backups of .env files

### Recovery Procedure

```bash
# 1. Restore database
pg_restore -h localhost -U postgres -d craigslist_leads backup_latest.dump

# 2. Restore files
aws s3 sync s3://backups/files /var/www/craigslist-leads/

# 3. Deploy code
git clone https://github.com/your-org/craigslist-leads.git
./scripts/deploy_backend.sh production
./scripts/deploy_frontend.sh production

# 4. Verify system
./scripts/health_check.sh production
```

### RTO/RPO Targets

- **RTO (Recovery Time Objective):** < 4 hours
- **RPO (Recovery Point Objective):** < 1 hour
- **Backup Frequency:** Every 1 hour
- **Backup Retention:** 30 days

---

## Additional Resources

- [Backend API Documentation](/backend/API_TECHNICAL_REFERENCE.md)
- [Database Schema](/backend/docs/database_schema.md)
- [Security Best Practices](/docs/security.md)
- [Performance Tuning](/docs/performance.md)
- [Monitoring Guide](/docs/monitoring.md)

---

**Last Updated:** 2025-11-05
**Version:** 1.0.0
**Maintained By:** DevOps Team
