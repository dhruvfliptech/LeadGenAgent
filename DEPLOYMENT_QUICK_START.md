# Deployment Quick Start Guide

Quick reference for deploying the Craigslist Lead Generation System to production.

## Pre-Deployment Checklist

- [ ] PostgreSQL 14+ with pgvector extension
- [ ] Redis 6+ server
- [ ] SSL certificates configured
- [ ] Environment variables configured (see `.env.production.example`)
- [ ] All tests passing
- [ ] Database backup created

## Initial Production Deployment

### 1. Configure Environment

```bash
# Copy production environment template
cp .env.production.example .env.production

# Edit with your production values
nano .env.production

# CRITICAL: Set these variables:
# - SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
# - DATABASE_URL
# - REDIS_URL
# - ALLOWED_HOSTS (NO wildcards!)
# - DEBUG=false
# - ENVIRONMENT=production
```

### 2. Setup Database

```bash
# Enable pgvector extension
psql -U postgres -d craigslist_leads -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run migrations
cd backend
export DATABASE_URL="postgresql://user:password@host:5432/craigslist_leads"
alembic upgrade head
```

### 3. Deploy Backend

```bash
# Run deployment script
./scripts/deploy_backend.sh production

# Verify deployment
curl https://api.yourdomain.com/health
```

### 4. Deploy Frontend

```bash
# Run deployment script
./scripts/deploy_frontend.sh production

# Verify deployment
curl https://yourdomain.com
```

### 5. Start Background Services

```bash
# Start Celery worker
cd backend
./start_celery_worker.sh

# Start Celery beat (scheduler)
./start_celery_beat.sh

# Optional: Start Flower (monitoring)
./start_flower.sh
```

### 6. Verify Deployment

```bash
# Run comprehensive health check
./scripts/health_check.sh production
```

## Updating Existing Deployment

### Standard Update (Zero-Downtime)

```bash
# 1. Pull latest code
git pull origin main

# 2. Deploy backend
./scripts/deploy_backend.sh production

# 3. Deploy frontend
./scripts/deploy_frontend.sh production

# 4. Run health checks
./scripts/health_check.sh production
```

### Emergency Rollback

```bash
# Rollback everything
./scripts/rollback.sh --all --emergency

# Or rollback specific component
./scripts/rollback.sh backend --last-good
./scripts/rollback.sh frontend --last-good
```

## Common Commands

### Check Service Status

```bash
# Backend API
sudo systemctl status craigslist-backend

# Celery worker
sudo systemctl status craigslist-celery

# Celery beat
sudo systemctl status craigslist-celery-beat
```

### View Logs

```bash
# Backend logs
tail -f logs/app.log

# Deployment logs
tail -f logs/deployment_production_*.log

# Health check reports
tail -f logs/health_check_production_*.txt
```

### Database Operations

```bash
# Create backup
pg_dump -U postgres -d craigslist_leads -F c -f backup_$(date +%Y%m%d).dump

# Check migration status
cd backend && alembic current

# Rollback one migration
cd backend && alembic downgrade -1
```

### Redis Operations

```bash
# Check Redis connection
redis-cli ping

# Check memory usage
redis-cli info memory

# Check number of keys
redis-cli dbsize
```

## Monitoring URLs

- **API Health:** `https://api.yourdomain.com/health`
- **API Docs:** `https://api.yourdomain.com/docs`
- **System Info:** `https://api.yourdomain.com/system/info`
- **Flower (Celery):** `http://yourdomain.com:5555` (if enabled)

## Environment Variables Quick Reference

### Critical Production Settings

```bash
# MUST be set correctly
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<secure-random-value>

# NO wildcards or localhost
ALLOWED_HOSTS=https://yourdomain.com,https://api.yourdomain.com

# Secure database and Redis
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379
```

### Service Dependencies

```bash
# AI Services (at least one required)
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...

# Email (required for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=app-password
```

### Optional Services

```bash
# ElevenLabs (voice synthesis)
ELEVENLABS_API_KEY=

# AWS S3 (video hosting)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# N8N (workflow automation)
N8N_API_URL=
N8N_API_KEY=
```

## Troubleshooting

### Database Connection Failed

```bash
# Check database is running
pg_isready -h host -p 5432

# Verify connection string
echo $DATABASE_URL

# Check connection pool
# Reduce pool size in .env if needed:
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=5
```

### Redis Connection Failed

```bash
# Check Redis is running
redis-cli ping

# Verify Redis URL
echo $REDIS_URL

# Restart Redis
sudo systemctl restart redis
```

### API Not Responding

```bash
# Check service status
sudo systemctl status craigslist-backend

# View recent logs
journalctl -u craigslist-backend -n 100

# Restart service
sudo systemctl restart craigslist-backend
```

### High Memory Usage

```bash
# Check memory usage
free -h

# Reduce Celery workers
# In .env:
CELERY_WORKER_CONCURRENCY=2

# Restart Celery
sudo systemctl restart craigslist-celery
```

### Frontend Not Loading

```bash
# Check Nginx status
sudo systemctl status nginx

# Test Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Check frontend files exist
ls -la /var/www/craigslist-leads/
```

## Security Checklist

- [ ] HTTPS enabled with valid SSL certificate
- [ ] SECRET_KEY is unique and secure
- [ ] Database credentials are strong
- [ ] CORS configured (no wildcards)
- [ ] DEBUG=false in production
- [ ] Rate limiting enabled
- [ ] Firewall configured
- [ ] Logs reviewed for security issues

## Performance Optimization

### Backend

```bash
# Increase workers (if CPU available)
# In systemd service file:
ExecStart=/path/to/venv/bin/uvicorn app.main:app --workers 4

# Enable Redis caching
REDIS_CACHE_ENABLED=true
```

### Database

```sql
-- Add indexes for frequently queried fields
CREATE INDEX CONCURRENTLY idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX CONCURRENTLY idx_leads_status ON leads(status);

-- Vacuum database
VACUUM ANALYZE;
```

### Frontend

```bash
# Enable CDN (Cloudflare, CloudFront)
# Configure in Nginx or DNS

# Enable gzip compression (already in Nginx config)
# Enable browser caching (already configured)
```

## Backup Strategy

### Automated Daily Backups

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /usr/local/bin/backup_database.sh
```

### Backup Script

```bash
#!/bin/bash
BACKUP_DIR="/backups/craigslist-leads"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
pg_dump -U postgres -d craigslist_leads -F c -f $BACKUP_DIR/db_$DATE.dump

# Files backup
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /var/www/craigslist-leads/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.dump" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

## Scaling Considerations

### Horizontal Scaling

- Load balance across multiple backend instances
- Use separate database read replicas
- Deploy Redis in cluster mode
- Use CDN for static assets

### Vertical Scaling

- Increase server resources (CPU, RAM)
- Optimize database queries
- Implement caching strategies
- Use connection pooling

## Support

For detailed documentation, see:
- [Full Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Backend API Reference](backend/API_TECHNICAL_REFERENCE.md)
- [Operations Guide](backend/DEPLOYMENT_OPERATIONS_GUIDE.md)

---

**Quick Help:** If deployment fails, check logs at `logs/deployment_production_*.log` and run `./scripts/health_check.sh production` for diagnostics.
