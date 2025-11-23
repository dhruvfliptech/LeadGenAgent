# Celery Setup Guide for FlipTech Pro

This guide covers the setup, configuration, and operation of Celery workers for background task processing in FlipTech Pro.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Starting Workers](#starting-workers)
7. [Task Categories](#task-categories)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Production Deployment](#production-deployment)

---

## Overview

FlipTech Pro uses Celery for asynchronous task processing, enabling:

- **Email Campaigns**: Send thousands of emails without blocking the main application
- **Web Scraping**: Run long-running scraper jobs in the background
- **AI Processing**: Process AI tasks without timeout issues
- **Demo Generation**: Generate personalized demo sites and videos
- **Scheduled Tasks**: Run periodic tasks like campaign scheduling and metrics updates

### Key Components

- **Celery App** (`celery_app.py`): Main Celery application configuration
- **Task Modules** (`app/tasks/`): Organized task definitions by category
- **Redis**: Message broker and result backend
- **Workers**: Process tasks from queues
- **Beat**: Scheduler for periodic tasks
- **Flower**: Web-based monitoring tool

---

## Architecture

### Queue Structure

FlipTech Pro uses multiple queues for task prioritization:

| Queue     | Priority | Purpose                              | Concurrency |
|-----------|----------|--------------------------------------|-------------|
| `email`   | 10 (High)| Email sending, campaign management   | 4           |
| `ai`      | 6 (Med)  | AI/ML processing                     | 4           |
| `default` | 5 (Med)  | General tasks                        | 4           |
| `scraper` | 3 (Low)  | Web scraping operations              | 2           |
| `demo`    | 2 (Low)  | Demo site generation, video creation | 2           |

### Task Flow

```
API Request → Queue Task → Redis → Worker → Execute → Store Result → API Response
```

### Scheduled Tasks (Celery Beat)

| Task                           | Schedule           | Purpose                              |
|--------------------------------|--------------------|--------------------------------------|
| process-scheduled-campaigns    | Every minute       | Launch scheduled campaigns           |
| retry-failed-emails            | Every 15 minutes   | Retry failed email sends             |
| update-campaign-metrics        | Every 5 minutes    | Update campaign statistics           |
| cleanup-task-results           | Every hour         | Clean old task results from Redis    |
| monitor-scraper-jobs           | Every 10 minutes   | Monitor scraper job status           |
| cleanup-old-scraper-data       | Daily at 3 AM      | Clean old scraped data               |
| generate-daily-analytics       | Daily at 1 AM      | Generate analytics reports           |

---

## Prerequisites

### System Requirements

- Python 3.8+
- Redis 6.0+
- PostgreSQL 12+ (for database)
- 4GB+ RAM (recommended)
- Multi-core CPU (recommended)

### Install Redis

**macOS (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Verify Redis:**
```bash
redis-cli ping
# Should return: PONG
```

---

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `celery==5.3.4` - Celery task queue
- `celery[redis]==5.3.4` - Redis support
- `flower==2.0.1` - Monitoring tool
- `kombu==5.3.4` - Messaging library
- `redis==5.0.1` - Redis client

### 2. Configure Environment

Create or update `.env` file:

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB_BROKER=0
REDIS_DB_BACKEND=1

# Celery Configuration
CELERY_LOG_LEVEL=info
CELERY_CONCURRENCY=4

# Email Configuration
EMAIL_BATCH_SIZE=50
EMAIL_BATCH_DELAY=2

# Scraper Configuration
SCRAPER_TIMEOUT=300
SCRAPER_RETRY_DELAY=120

# AI Configuration
AI_TIMEOUT=180
AI_RETRY_DELAY=60

# Demo Configuration
DEMO_TIMEOUT=1800
VIDEO_PROCESSING_TIMEOUT=3600
```

### 3. Test Configuration

```bash
cd backend
python -c "from celery_app import celery_app; print(celery_app.conf)"
```

---

## Configuration

### Celery App Configuration

The main configuration is in `backend/celery_app.py`:

**Key Settings:**

```python
# Task serialization (JSON for safety)
task_serializer = "json"
accept_content = ["json"]

# Task execution
task_acks_late = True
task_reject_on_worker_lost = True

# Time limits
task_soft_time_limit = 600  # 10 minutes
task_time_limit = 900       # 15 minutes

# Worker settings
worker_prefetch_multiplier = 4
worker_max_tasks_per_child = 1000

# Retry settings
task_default_retry_delay = 60
task_max_retries = 3
```

### Task Routes

Tasks are automatically routed to queues:

```python
task_routes = {
    "app.tasks.email_tasks.*": {"queue": "email"},
    "app.tasks.campaign_tasks.*": {"queue": "email"},
    "app.tasks.scraper_tasks.*": {"queue": "scraper"},
    "app.tasks.ai_tasks.*": {"queue": "ai"},
    "app.tasks.demo_tasks.*": {"queue": "demo"},
}
```

### Rate Limits

Some tasks have rate limits:

```python
task_annotations = {
    "app.tasks.email_tasks.send_single_email": {"rate_limit": "50/m"},
    "app.tasks.scraper_tasks.scrape_craigslist": {"rate_limit": "10/m"},
    "app.tasks.ai_tasks.generate_ai_response": {"rate_limit": "30/m"},
}
```

---

## Starting Workers

### Quick Start (Development)

Start all workers with one command:

```bash
cd backend

# Terminal 1: Start worker for all queues
./start_celery_worker.sh

# Terminal 2: Start beat scheduler
./start_celery_beat.sh

# Terminal 3: Start Flower monitoring (optional)
./start_flower.sh
```

### Start Specific Queue Workers

For production, run dedicated workers per queue:

```bash
# High-priority email worker
./start_celery_worker.sh email

# Scraper worker
./start_celery_worker.sh scraper

# AI worker (consider GPU if available)
./start_celery_worker.sh ai

# Demo worker
./start_celery_worker.sh demo

# Default worker
./start_celery_worker.sh default
```

### Manual Start (Advanced)

```bash
# Worker with custom settings
celery -A celery_app:celery_app worker \
  --queues=email,default \
  --concurrency=8 \
  --loglevel=info \
  --autoscale=10,3 \
  -n worker1@%h

# Beat scheduler
celery -A celery_app:celery_app beat \
  --loglevel=info \
  --schedule=celerybeat-schedule

# Flower monitoring
celery -A celery_app:celery_app flower \
  --port=5555 \
  --persistent=True
```

### Verify Workers are Running

```bash
# Check worker status
celery -A celery_app:celery_app inspect active

# Check registered tasks
celery -A celery_app:celery_app inspect registered

# Check queue stats
celery -A celery_app:celery_app inspect stats
```

---

## Task Categories

### Email Tasks

**Location:** `app/tasks/email_tasks.py`

| Task                  | Description                          | Queue   |
|-----------------------|--------------------------------------|---------|
| send_single_email     | Send individual email                | email   |
| send_batch_emails     | Send batch of emails with rate limit | email   |
| send_campaign_email   | Send campaign email with tracking    | email   |
| retry_failed_emails   | Retry failed emails (scheduled)      | email   |
| send_test_email       | Send test email for verification     | email   |

**Usage Example:**

```python
from app.tasks.email_tasks import send_single_email

# Queue email for sending
task = send_single_email.delay(
    to_email="user@example.com",
    subject="Hello from FlipTech Pro",
    html_body="<p>Hello World!</p>"
)

# Check task status
print(task.status)  # PENDING, STARTED, SUCCESS, FAILURE

# Get result (blocking)
result = task.get(timeout=30)
print(result)
```

### Campaign Tasks

**Location:** `app/tasks/campaign_tasks.py`

| Task                          | Description                      | Queue   |
|-------------------------------|----------------------------------|---------|
| send_campaign_emails          | Send all emails for campaign     | email   |
| launch_campaign_async         | Launch campaign                  | email   |
| process_scheduled_campaigns   | Process scheduled campaigns      | email   |
| update_campaign_metrics       | Update campaign statistics       | email   |
| pause_campaign_async          | Pause running campaign           | email   |
| resume_campaign_async         | Resume paused campaign           | email   |

### Scraper Tasks

**Location:** `app/tasks/scraper_tasks.py`

| Task                      | Description                      | Queue    |
|---------------------------|----------------------------------|----------|
| scrape_craigslist         | Scrape Craigslist leads          | scraper  |
| scrape_google_maps        | Scrape Google Maps businesses    | scraper  |
| scrape_linkedin           | Scrape LinkedIn profiles         | scraper  |
| scrape_job_boards         | Scrape job board listings        | scraper  |
| scrape_multi_source       | Scrape multiple sources parallel | scraper  |
| monitor_scraper_jobs      | Monitor scraper job status       | scraper  |
| export_leads              | Export leads to file             | scraper  |

**Usage Example:**

```python
from app.tasks.scraper_tasks import scrape_craigslist

# Start scraping job
task = scrape_craigslist.delay(
    location="sfbay",
    category="bbb",
    max_results=100
)

# Check progress
print(f"Task ID: {task.id}")
print(f"Status: {task.status}")

# Get result when done
result = task.get(timeout=600)  # Wait up to 10 minutes
print(f"Scraped {result['leads_created']} leads")
```

### AI Tasks

**Location:** `app/tasks/ai_tasks.py`

| Task                      | Description                      | Queue   |
|---------------------------|----------------------------------|---------|
| generate_ai_response      | Generate AI response             | ai      |
| analyze_lead              | Analyze lead quality             | ai      |
| process_conversation      | Process conversation thread      | ai      |
| batch_analyze_leads       | Analyze multiple leads           | ai      |
| generate_email_content    | Generate personalized email      | ai      |
| predict_lead_conversion   | Predict conversion probability   | ai      |
| train_ml_model            | Train ML models                  | ai      |

### Demo Tasks

**Location:** `app/tasks/demo_tasks.py`

| Task                      | Description                      | Queue   |
|---------------------------|----------------------------------|---------|
| generate_demo_site        | Generate personalized demo site  | demo    |
| compose_video             | Compose video from recordings    | demo    |
| generate_voiceover        | Generate TTS voiceover           | demo    |
| capture_screen_recording  | Capture screen recording         | demo    |
| optimize_video            | Optimize video for web           | demo    |
| upload_to_hosting         | Upload files to hosting          | demo    |

---

## Monitoring

### Flower Web UI

Access Flower at: **http://localhost:5555**

Features:
- Real-time task monitoring
- Worker statistics
- Task history and details
- Queue inspection
- Worker management

### Command Line Monitoring

```bash
# Active tasks
celery -A celery_app:celery_app inspect active

# Scheduled tasks
celery -A celery_app:celery_app inspect scheduled

# Worker stats
celery -A celery_app:celery_app inspect stats

# Registered tasks
celery -A celery_app:celery_app inspect registered

# Revoke a task
celery -A celery_app:celery_app control revoke <task_id>

# Purge all tasks
celery -A celery_app:celery_app purge
```

### Redis Monitoring

```bash
# Connect to Redis CLI
redis-cli

# Check queue lengths
LLEN celery

# Monitor Redis in real-time
redis-cli --stat

# Monitor commands in real-time
redis-cli monitor
```

---

## Troubleshooting

### Workers Not Starting

**Check Redis:**
```bash
redis-cli ping
# Should return: PONG
```

**Check Configuration:**
```bash
cd backend
python -c "from celery_app import celery_app; print('OK')"
```

**Check Dependencies:**
```bash
pip list | grep celery
pip list | grep redis
```

### Tasks Not Executing

**Check Worker Logs:**
```bash
# Look for errors in worker output
tail -f celery_worker.log
```

**Check Task Registration:**
```bash
celery -A celery_app:celery_app inspect registered
```

**Check Queue:**
```bash
redis-cli LLEN celery
redis-cli LLEN email
redis-cli LLEN scraper
```

### Memory Issues

**Reduce Concurrency:**
```bash
# Edit .env
CELERY_CONCURRENCY=2
```

**Restart Workers More Frequently:**
```python
# In celery_app.py
worker_max_tasks_per_child = 500  # Instead of 1000
```

### Task Failures

**Check Task Logs:**
```bash
# View in Flower UI
# Or check worker output
```

**Manual Retry:**
```python
from celery_app import celery_app
task = celery_app.send_task('app.tasks.email_tasks.send_single_email', args=[...])
```

**Revoke Failed Task:**
```bash
celery -A celery_app:celery_app control revoke <task_id>
```

---

## Production Deployment

### Supervisor Configuration

Use Supervisor to manage Celery processes:

**`/etc/supervisor/conf.d/celery.conf`:**

```ini
[program:celery-worker-email]
command=/path/to/venv/bin/celery -A celery_app:celery_app worker --queues=email --concurrency=8 -n worker-email@%%h
directory=/path/to/backend
user=fliptechpro
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/worker-email.log

[program:celery-worker-scraper]
command=/path/to/venv/bin/celery -A celery_app:celery_app worker --queues=scraper --concurrency=4 -n worker-scraper@%%h
directory=/path/to/backend
user=fliptechpro
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/worker-scraper.log

[program:celery-beat]
command=/path/to/venv/bin/celery -A celery_app:celery_app beat --loglevel=info
directory=/path/to/backend
user=fliptechpro
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/beat.log

[program:flower]
command=/path/to/venv/bin/celery -A celery_app:celery_app flower --port=5555
directory=/path/to/backend
user=fliptechpro
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/flower.log
```

**Reload Supervisor:**
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status
```

### Systemd Service

**`/etc/systemd/system/celery-worker@.service`:**

```ini
[Unit]
Description=Celery Worker %i
After=network.target redis.service

[Service]
Type=forking
User=fliptechpro
Group=fliptechpro
WorkingDirectory=/path/to/backend
ExecStart=/path/to/venv/bin/celery -A celery_app:celery_app worker \
    --queues=%i --concurrency=4 -n worker-%i@%%h \
    --logfile=/var/log/celery/worker-%i.log --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable Services:**
```bash
sudo systemctl enable celery-worker@email
sudo systemctl enable celery-worker@scraper
sudo systemctl start celery-worker@email
sudo systemctl start celery-worker@scraper
```

### Docker Deployment

**`docker-compose.yml`:**

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  celery-worker:
    build: .
    command: celery -A celery_app:celery_app worker --queues=email,default --loglevel=info
    volumes:
      - .:/app
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis

  celery-beat:
    build: .
    command: celery -A celery_app:celery_app beat --loglevel=info
    volumes:
      - .:/app
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis

  flower:
    build: .
    command: celery -A celery_app:celery_app flower --port=5555
    ports:
      - "5555:5555"
    volumes:
      - .:/app
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis

volumes:
  redis_data:
```

### Performance Tuning

**Optimize Redis:**
```bash
# /etc/redis/redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

**Optimize Workers:**
```bash
# Use multiple workers per queue
celery multi start 4 -A celery_app:celery_app -Q:1-2 email -Q:3-4 default

# Use autoscaling
celery -A celery_app:celery_app worker --autoscale=10,3
```

**Database Connection Pooling:**
```python
# In celery_app.py
from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=40)
```

---

## Best Practices

### Task Design

1. **Idempotency**: Tasks should be safe to retry
2. **Atomicity**: Each task should do one thing well
3. **Error Handling**: Use try/except and proper logging
4. **Timeouts**: Set appropriate time limits
5. **Results**: Store results only when needed

### Monitoring

1. **Set up alerts** for worker failures
2. **Monitor queue lengths** to prevent backlog
3. **Track task execution times**
4. **Review error logs regularly**

### Security

1. **Secure Redis**: Use password authentication
2. **Secure Flower**: Add authentication in production
3. **Rate Limiting**: Prevent task flooding
4. **Input Validation**: Validate all task inputs

---

## Support

For issues or questions:
- Check logs in `/var/log/celery/`
- Review Flower dashboard at http://localhost:5555
- Check Redis with `redis-cli`
- Review task code in `app/tasks/`

---

## Quick Reference

### Start/Stop Commands

```bash
# Development
./start_celery_worker.sh [queue]
./start_celery_beat.sh
./start_flower.sh

# Production (Supervisor)
sudo supervisorctl start celery-worker-email
sudo supervisorctl stop celery-worker-email
sudo supervisorctl restart celery-worker-email

# Production (Systemd)
sudo systemctl start celery-worker@email
sudo systemctl stop celery-worker@email
sudo systemctl restart celery-worker@email
```

### Important Files

- `backend/celery_app.py` - Main Celery configuration
- `backend/app/tasks/` - Task definitions
- `backend/start_celery_worker.sh` - Worker startup script
- `backend/start_celery_beat.sh` - Beat startup script
- `backend/start_flower.sh` - Flower startup script
- `.env` - Environment configuration

### URLs

- Flower: http://localhost:5555
- API: http://localhost:8000
- Frontend: http://localhost:3000

---

**Version:** 1.0
**Last Updated:** 2024-11-05
**Author:** FlipTech Pro Team
