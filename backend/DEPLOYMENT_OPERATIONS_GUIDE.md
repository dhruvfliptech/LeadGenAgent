# Craigslist Lead Generation System v2.0
## Deployment & Operations Guide

---

> Note: Docker and Kubernetes deployment paths in this document are deprecated for this repository. Prefer native installs or your hosting platform's buildpack. See the README and `start_local.sh` for local development.

## Quick Start

### Local Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8001

# Frontend
cd frontend
npm install
npm run dev
```

### Production Deployment
```bash
# Using Docker Compose
docker-compose up -d

# Using Kubernetes
kubectl apply -f k8s/
```

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Production Deployment](#production-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Database Management](#database-management)
6. [Monitoring & Logging](#monitoring--logging)
7. [Backup & Recovery](#backup--recovery)
8. [Performance Tuning](#performance-tuning)
9. [Security Hardening](#security-hardening)
10. [Troubleshooting](#troubleshooting)
11. [Maintenance Procedures](#maintenance-procedures)
12. [Scaling Guidelines](#scaling-guidelines)

---

## Prerequisites

### System Requirements

#### Minimum (Development)
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 20 GB SSD
- **OS**: Ubuntu 20.04+ / macOS 12+ / Windows 10+
- **Python**: 3.11+
- **Node.js**: 18+
- **PostgreSQL**: 15+

#### Recommended (Production)
- **CPU**: 4+ cores
- **RAM**: 16 GB
- **Storage**: 100 GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Python**: 3.11+
- **Node.js**: 18 LTS
- **PostgreSQL**: 15+
- **Redis**: 7+
- **Nginx**: 1.24+

### Software Dependencies
```bash
# System packages
sudo apt-get update
sudo apt-get install -y \
  python3.11 \
  python3.11-venv \
  python3-pip \
  postgresql-15 \
  redis-server \
  nginx \
  supervisor \
  git \
  curl \
  build-essential

# Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Playwright dependencies
npx playwright install-deps
```

---

## Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/yourorg/craigleads.git
cd craigleads
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install Playwright browsers
playwright install chromium

# Create .env file
cp .env.example .env
# Edit .env with your configuration
```

### 3. Database Setup
```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE craigslist_leads;
CREATE USER craigleads WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE craigslist_leads TO craigleads;
\q

# Run migrations
alembic upgrade head

# Seed initial data
python scripts/seed_locations.py
```

### 4. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env
# Edit .env with your configuration

# Start development server
npm run dev
```

### 5. Start Services
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8001

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Redis (optional)
redis-server

# Terminal 4: Background workers (optional)
cd backend
source venv/bin/activate
python -m app.workers.scraper_worker
```

---

## Production Deployment

### Option 1: Docker Deployment

#### Docker Compose Configuration
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    image: craigleads-backend:latest
    container_name: craigleads-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    image: craigleads-frontend:latest
    container_name: craigleads-frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://backend:8000
    depends_on:
      - backend
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    container_name: craigleads-db
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=craigslist_leads
      - POSTGRES_USER=craigleads
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: craigleads-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

  nginx:
    image: nginx:alpine
    container_name: craigleads-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/sites:/etc/nginx/sites-enabled
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

#### Backend Dockerfile
```dockerfile
# backend/Dockerfile.prod
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright
RUN pip install playwright
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### Frontend Dockerfile
```dockerfile
# frontend/Dockerfile.prod
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install serve
RUN npm install -g serve

# Copy built application
COPY --from=builder /app/dist ./dist

# Run application
CMD ["serve", "-s", "dist", "-l", "3000"]
```

#### Deploy with Docker Compose
```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Option 2: Kubernetes Deployment

#### Kubernetes Manifests
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: craigleads

---
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: craigleads
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: craigleads-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: craigleads-secrets
              key: database-url
        - name: REDIS_URL
          value: redis://redis-service:6379
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# k8s/backend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: craigleads
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: craigleads-ingress
  namespace: craigleads
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.craigleads.com
    - app.craigleads.com
    secretName: craigleads-tls
  rules:
  - host: api.craigleads.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
  - host: app.craigleads.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 3000
```

#### Deploy to Kubernetes
```bash
# Create namespace
kubectl create namespace craigleads

# Create secrets
kubectl create secret generic craigleads-secrets \
  --from-literal=database-url='postgresql://...' \
  --from-literal=secret-key='...' \
  -n craigleads

# Apply manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n craigleads
kubectl get services -n craigleads
kubectl get ingress -n craigleads
```

### Option 3: Traditional Server Deployment

#### 1. Server Setup
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Create application user
sudo useradd -m -s /bin/bash craigleads
sudo usermod -aG sudo craigleads

# Create directories
sudo mkdir -p /opt/craigleads
sudo chown craigleads:craigleads /opt/craigleads
```

#### 2. Install Application
```bash
# Switch to app user
sudo su - craigleads

# Clone repository
cd /opt/craigleads
git clone https://github.com/yourorg/craigleads.git .

# Setup backend
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Setup frontend
cd ../frontend
npm install
npm run build
```

#### 3. Configure Systemd Services

##### Backend Service
```ini
# /etc/systemd/system/craigleads-backend.service
[Unit]
Description=CraigLeads Backend API
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=craigleads
Group=craigleads
WorkingDirectory=/opt/craigleads/backend
Environment="PATH=/opt/craigleads/backend/venv/bin"
ExecStart=/opt/craigleads/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

##### Frontend Service
```ini
# /etc/systemd/system/craigleads-frontend.service
[Unit]
Description=CraigLeads Frontend
After=network.target

[Service]
Type=exec
User=craigleads
Group=craigleads
WorkingDirectory=/opt/craigleads/frontend
ExecStart=/usr/bin/npx serve -s dist -l 3000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

##### Start Services
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable craigleads-backend
sudo systemctl start craigleads-backend

sudo systemctl enable craigleads-frontend
sudo systemctl start craigleads-frontend

# Check status
sudo systemctl status craigleads-backend
sudo systemctl status craigleads-frontend
```

#### 4. Configure Nginx
```nginx
# /etc/nginx/sites-available/craigleads
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name craigleads.com www.craigleads.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name craigleads.com www.craigleads.com;

    ssl_certificate /etc/letsencrypt/live/craigleads.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/craigleads.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
    }

    # WebSocket
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

##### Enable Nginx Site
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/craigleads /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## Environment Configuration

### Backend Environment Variables
```bash
# .env
# Database
DATABASE_URL=postgresql://craigleads:password@localhost:5432/craigslist_leads
DATABASE_POOL_SIZE=20
DATABASE_POOL_OVERFLOW=10

# Redis (optional)
REDIS_URL=redis://localhost:6379
REDIS_MAX_CONNECTIONS=50

# Security
SECRET_KEY=your-secret-key-here-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
ALLOWED_HOSTS=["craigleads.com", "www.craigleads.com"]

# Scraping
SCRAPER_USER_AGENT="CraigLeads Bot 2.0"
SCRAPER_DELAY_SECONDS=1
SCRAPER_MAX_RETRIES=3
SCRAPER_TIMEOUT_SECONDS=30

# AI/ML (optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AI_PROVIDER=openai
AI_MODEL=gpt-4
AI_MAX_TOKENS=1000
AI_TEMPERATURE=0.7

# Features
AUTO_RESPONDER_ENABLED=true
RULE_ENGINE_ENABLED=true
ENABLE_REAL_TIME_NOTIFICATIONS=true
ENABLE_ADVANCED_ANALYTICS=true
ENABLE_AB_TESTING=true

# Limits
MAX_CONCURRENT_REQUESTS=100
EXPORT_MAX_RECORDS=10000
RESPONSE_TIMEOUT=30

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@craigleads.com

# Monitoring (optional)
SENTRY_DSN=https://...@sentry.io/...
DATADOG_API_KEY=...
```

### Frontend Environment Variables
```bash
# .env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_ENVIRONMENT=production
VITE_SENTRY_DSN=https://...@sentry.io/...
VITE_GA_TRACKING_ID=UA-...
```

---

## Database Management

### Migrations

#### Create New Migration
```bash
cd backend
source venv/bin/activate

# Auto-generate migration
alembic revision --autogenerate -m "Add new field to leads"

# Manual migration
alembic revision -m "Custom migration"
```

#### Apply Migrations
```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade +1

# Show current revision
alembic current

# Show history
alembic history
```

#### Rollback Migrations
```bash
# Rollback one revision
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123

# Rollback all
alembic downgrade base
```

### Database Backup

#### Manual Backup
```bash
# Full backup
pg_dump -h localhost -U craigleads -d craigslist_leads > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
pg_dump -h localhost -U craigleads -d craigslist_leads | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Custom format (recommended)
pg_dump -h localhost -U craigleads -d craigslist_leads -Fc > backup_$(date +%Y%m%d_%H%M%S).dump
```

#### Automated Backup Script
```bash
#!/bin/bash
# /opt/craigleads/scripts/backup.sh

BACKUP_DIR="/backups/postgres"
DB_NAME="craigslist_leads"
DB_USER="craigleads"
RETENTION_DAYS=30

# Create backup
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.dump"

pg_dump -h localhost -U $DB_USER -d $DB_NAME -Fc > $BACKUP_FILE

# Compress
gzip $BACKUP_FILE

# Upload to S3 (optional)
aws s3 cp $BACKUP_FILE.gz s3://your-bucket/backups/

# Remove old backups
find $BACKUP_DIR -name "backup_*.dump.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

#### Backup Cron Job
```bash
# Add to crontab
0 2 * * * /opt/craigleads/scripts/backup.sh >> /var/log/craigleads/backup.log 2>&1
```

### Database Restore

#### Restore from Backup
```bash
# From SQL file
psql -h localhost -U craigleads -d craigslist_leads < backup.sql

# From compressed file
gunzip -c backup.sql.gz | psql -h localhost -U craigleads -d craigslist_leads

# From custom format
pg_restore -h localhost -U craigleads -d craigslist_leads backup.dump

# Restore to new database
createdb -h localhost -U craigleads craigslist_leads_restore
pg_restore -h localhost -U craigleads -d craigslist_leads_restore backup.dump
```

---

## Monitoring & Logging

### Application Monitoring

#### Health Check Endpoints
```python
# Health check implementation
@app.get("/health")
async def health_check():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "scraper": await check_scraper_status()
    }
    
    status = "healthy" if all(checks.values()) else "unhealthy"
    
    return {
        "status": status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def metrics():
    return {
        "requests_total": metrics.requests_total,
        "requests_duration_seconds": metrics.request_duration,
        "active_connections": metrics.active_connections,
        "database_pool_size": engine.pool.size(),
        "cache_hit_rate": cache.hit_rate()
    }
```

#### Prometheus Integration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'craigleads'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

#### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "CraigLeads Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, requests_duration_seconds)"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(errors_total[5m])"
          }
        ]
      }
    ]
  }
}
```

### Logging Configuration

#### Python Logging
```python
# app/core/logging.py
import logging
import sys
from logging.handlers import RotatingFileHandler
import structlog

def setup_logging():
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure Python logging
    handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
```

#### Log Aggregation with ELK Stack
```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /opt/craigleads/backend/logs/*.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "craigleads-%{+yyyy.MM.dd}"

processors:
  - add_host_metadata:
      when.not.contains:
        tags: forwarded
```

### Error Tracking

#### Sentry Integration
```python
# app/core/sentry.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

def init_sentry():
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
        release=f"craigleads@{VERSION}"
    )
```

---

## Backup & Recovery

### Backup Strategy

#### Daily Backups
```bash
#!/bin/bash
# /opt/craigleads/scripts/daily_backup.sh

# Database backup
pg_dump -Fc craigslist_leads > /backups/db/daily_$(date +%Y%m%d).dump

# Application files backup
tar -czf /backups/app/app_$(date +%Y%m%d).tar.gz /opt/craigleads

# Redis backup
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb /backups/redis/dump_$(date +%Y%m%d).rdb

# Upload to S3
aws s3 sync /backups s3://craigleads-backups/$(date +%Y%m%d)/
```

#### Point-in-Time Recovery
```bash
# Enable WAL archiving in PostgreSQL
archive_mode = on
archive_command = 'test ! -f /archives/%f && cp %p /archives/%f'
wal_level = replica
max_wal_senders = 3
```

### Disaster Recovery

#### Recovery Procedures
```bash
# 1. Restore database
pg_restore -C -d postgres /backups/db/latest.dump

# 2. Restore application
tar -xzf /backups/app/latest.tar.gz -C /

# 3. Restore Redis
cp /backups/redis/latest.rdb /var/lib/redis/dump.rdb
systemctl restart redis

# 4. Verify services
systemctl status craigleads-backend
systemctl status craigleads-frontend
curl http://localhost:8000/health
```

#### Failover Process
```bash
# 1. Switch DNS to backup server
# Update A records to point to backup IP

# 2. Promote standby database
pg_ctl promote -D /var/lib/postgresql/15/standby

# 3. Update application configuration
sed -i 's/primary-db/standby-db/g' /opt/craigleads/backend/.env

# 4. Restart services
systemctl restart craigleads-backend
```

---

## Performance Tuning

### PostgreSQL Optimization

#### Configuration Tuning
```ini
# postgresql.conf
# Memory
shared_buffers = 4GB          # 25% of RAM
effective_cache_size = 12GB   # 75% of RAM
work_mem = 20MB
maintenance_work_mem = 1GB

# Connections
max_connections = 200
max_prepared_transactions = 100

# Write Performance
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1

# Query Planning
enable_partitionwise_join = on
enable_partitionwise_aggregate = on
```

#### Index Optimization
```sql
-- Analyze table statistics
ANALYZE leads;

-- Find missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename = 'leads'
ORDER BY n_distinct DESC;

-- Create optimized indexes
CREATE INDEX idx_leads_qualification_score ON leads(qualification_score DESC);
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX idx_leads_location_category ON leads(location_id, category);
CREATE INDEX idx_leads_search ON leads USING gin(to_tsvector('english', title || ' ' || description));
```

### Application Performance

#### Caching Strategy
```python
# Redis caching
from functools import wraps
import redis
import json

redis_client = redis.from_url(settings.REDIS_URL)

def cache(expire=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            redis_client.setex(
                cache_key,
                expire,
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator

# Usage
@cache(expire=300)
async def get_leads(location_id: int):
    # Expensive database query
    return await db.query(Lead).filter_by(location_id=location_id).all()
```

#### Connection Pooling
```python
# Database connection pooling
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo_pool=True
)
```

#### Async Optimization
```python
# Concurrent operations
import asyncio

async def process_leads(lead_ids: List[int]):
    # Process leads concurrently
    tasks = [process_single_lead(lead_id) for lead_id in lead_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle results
    successful = [r for r in results if not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]
    
    return {
        "processed": len(successful),
        "failed": len(failed),
        "results": successful
    }
```

---

## Security Hardening

### SSL/TLS Configuration

#### Generate SSL Certificates
```bash
# Using Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d craigleads.com -d www.craigleads.com

# Auto-renewal
sudo certbot renew --dry-run
```

#### Strong SSL Configuration
```nginx
# /etc/nginx/snippets/ssl-params.conf
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers off;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;
ssl_stapling on;
ssl_stapling_verify on;
add_header Strict-Transport-Security "max-age=63072000" always;
```

### Application Security

#### Input Validation
```python
from pydantic import BaseModel, validator, constr, conint

class LeadQueryParams(BaseModel):
    page: conint(ge=1, le=1000) = 1
    per_page: conint(ge=1, le=100) = 20
    search: constr(max_length=100, pattern=r'^[a-zA-Z0-9\s]+$') = None
    
    @validator('search')
    def sanitize_search(cls, v):
        if v:
            # Remove potential SQL injection attempts
            dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]
            for char in dangerous_chars:
                v = v.replace(char, "")
        return v
```

#### Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour"],
    storage_uri=settings.REDIS_URL
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/scraper/jobs")
@limiter.limit("10 per minute")
async def create_scraping_job():
    pass
```

### Firewall Configuration

#### UFW Setup
```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow PostgreSQL (only from app servers)
sudo ufw allow from 10.0.0.0/24 to any port 5432

# Allow Redis (only from localhost)
sudo ufw allow from 127.0.0.1 to any port 6379

# Check status
sudo ufw status verbose
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Kill idle connections
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < NOW() - INTERVAL '10 minutes';"

# Increase connection limit
sudo -u postgres psql -c "ALTER SYSTEM SET max_connections = 300;"
sudo systemctl restart postgresql
```

#### 2. Memory Issues
```bash
# Check memory usage
free -h
ps aux | sort -nrk 4 | head

# Clear cache
sync && echo 3 > /proc/sys/vm/drop_caches

# Check for memory leaks
valgrind --leak-check=full python app.main
```

#### 3. Scraping Failures
```python
# Debug scraping issues
import logging
logging.basicConfig(level=logging.DEBUG)

# Test scraper manually
from app.scrapers.craigslist_scraper import CraigslistScraper

async def test_scraper():
    scraper = CraigslistScraper()
    await scraper.initialize()
    
    try:
        results = await scraper.scrape_location(
            location_id=1,
            category="gigs",
            max_pages=1
        )
        print(f"Found {len(results)} leads")
    except Exception as e:
        print(f"Scraping failed: {e}")
    finally:
        await scraper.close()

# Run test
import asyncio
asyncio.run(test_scraper())
```

#### 4. Performance Issues
```bash
# Profile application
python -m cProfile -o profile.stats app.main

# Analyze profile
python -m pstats profile.stats
sort cumulative
stats 20

# Check slow queries
sudo -u postgres psql -c "SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

### Debug Mode

#### Enable Debug Logging
```python
# .env
DEBUG=true
LOG_LEVEL=DEBUG

# app/main.py
if settings.DEBUG:
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.DEBUG)
```

#### Debug Endpoints
```python
@app.get("/debug/info")
async def debug_info():
    if not settings.DEBUG:
        raise HTTPException(403, "Debug mode not enabled")
    
    return {
        "environment": settings.ENVIRONMENT,
        "database_pool": {
            "size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "overflow": engine.pool.overflow(),
            "total": engine.pool.total()
        },
        "memory": {
            "rss": psutil.Process().memory_info().rss / 1024 / 1024,
            "vms": psutil.Process().memory_info().vms / 1024 / 1024
        },
        "cpu": psutil.cpu_percent(),
        "disk": psutil.disk_usage('/').percent
    }
```

---

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily Tasks
```bash
#!/bin/bash
# /opt/craigleads/scripts/daily_maintenance.sh

echo "Starting daily maintenance - $(date)"

# 1. Clean old logs
find /opt/craigleads/logs -name "*.log" -mtime +30 -delete

# 2. Vacuum database
sudo -u postgres psql -d craigslist_leads -c "VACUUM ANALYZE;"

# 3. Clear expired sessions
redis-cli --scan --pattern "session:*" | xargs -L 100 redis-cli DEL

# 4. Check disk space
df -h | grep -E "^/dev/" | awk '$5+0 > 80 {print "Warning: " $6 " is " $5 " full"}'

echo "Daily maintenance completed - $(date)"
```

#### Weekly Tasks
```bash
#!/bin/bash
# /opt/craigleads/scripts/weekly_maintenance.sh

echo "Starting weekly maintenance - $(date)"

# 1. Full database backup
pg_dump -Fc craigslist_leads > /backups/weekly_$(date +%Y%m%d).dump

# 2. Reindex database
sudo -u postgres psql -d craigslist_leads -c "REINDEX DATABASE craigslist_leads;"

# 3. Update statistics
sudo -u postgres psql -d craigslist_leads -c "ANALYZE;"

# 4. Security updates
sudo apt-get update
sudo apt-get upgrade -y

# 5. Clean Docker images (if using Docker)
docker system prune -af

echo "Weekly maintenance completed - $(date)"
```

### Database Maintenance

#### Vacuum and Analyze
```sql
-- Manual vacuum
VACUUM ANALYZE leads;

-- Aggressive vacuum (locks table)
VACUUM FULL leads;

-- Auto-vacuum settings
ALTER TABLE leads SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE leads SET (autovacuum_analyze_scale_factor = 0.05);
```

#### Table Maintenance
```sql
-- Check table size
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan;

-- Find duplicate indexes
SELECT 
    pg_size_pretty(sum(pg_relation_size(idx))::bigint) AS size,
    (array_agg(idx))[1] AS idx1,
    (array_agg(idx))[2] AS idx2
FROM (
    SELECT 
        indexrelid::regclass AS idx,
        indrelid,
        indkey::text,
        indclass::text
    FROM pg_index
) sub
GROUP BY indrelid, indkey, indclass
HAVING count(*) > 1;
```

---

## Scaling Guidelines

### Horizontal Scaling

#### Load Balancing
```nginx
# /etc/nginx/conf.d/upstream.conf
upstream backend_cluster {
    least_conn;
    server backend1.internal:8000 weight=5;
    server backend2.internal:8000 weight=3;
    server backend3.internal:8000 weight=2;
    
    # Health checks
    keepalive 32;
}

server {
    location /api {
        proxy_pass http://backend_cluster;
        proxy_next_upstream error timeout http_500 http_502 http_503;
        proxy_connect_timeout 1s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }
}
```

#### Database Replication
```bash
# Master configuration
# postgresql.conf
wal_level = replica
max_wal_senders = 10
wal_keep_segments = 64
synchronous_commit = on

# pg_hba.conf
host replication replica_user 10.0.0.0/24 md5

# Standby configuration
# recovery.conf
standby_mode = 'on'
primary_conninfo = 'host=master.db port=5432 user=replica_user'
trigger_file = '/tmp/postgresql.trigger.5432'
```

### Vertical Scaling

#### Resource Monitoring
```python
# Monitor resource usage
import psutil

def get_system_metrics():
    return {
        "cpu": {
            "percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count(),
            "freq": psutil.cpu_freq().current
        },
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent
        },
        "disk": {
            "total": psutil.disk_usage('/').total,
            "used": psutil.disk_usage('/').used,
            "percent": psutil.disk_usage('/').percent
        },
        "network": {
            "bytes_sent": psutil.net_io_counters().bytes_sent,
            "bytes_recv": psutil.net_io_counters().bytes_recv
        }
    }
```

#### Scaling Triggers
```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Appendix

### Useful Commands

```bash
# Check all services
systemctl status craigleads-*

# View logs
journalctl -u craigleads-backend -f
tail -f /opt/craigleads/logs/app.log

# Database commands
psql -U craigleads -d craigslist_leads
\dt  # List tables
\d+ leads  # Describe table
\x  # Expanded display

# Redis commands
redis-cli
KEYS *
INFO
FLUSHDB  # Clear database

# Docker commands
docker-compose ps
docker-compose logs -f backend
docker exec -it craigleads-backend bash

# Performance testing
ab -n 1000 -c 10 http://localhost:8000/api/v1/leads
wrk -t4 -c100 -d30s --latency http://localhost:8000/api/v1/leads
```

### Support Contacts

- **Technical Support**: tech-support@craigleads.com
- **Emergency**: +1-555-CRAIGLEADS
- **Documentation**: https://docs.craigleads.com
- **Status Page**: https://status.craigleads.com

---

*Last Updated: August 23, 2024*
*Version: 2.0.0*