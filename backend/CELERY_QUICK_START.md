# Celery Quick Start Guide

Get Celery workers running in 5 minutes!

## Prerequisites

✅ Python 3.8+
✅ Redis installed and running
✅ Backend dependencies installed

## Setup Steps

### 1. Install Redis (if not installed)

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
```

**Verify:**
```bash
redis-cli ping
# Should return: PONG
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file in `backend/` directory (if not exists):

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
```

### 4. Start Workers

Open 3 terminal windows:

**Terminal 1 - Celery Worker:**
```bash
cd backend
./start_celery_worker.sh
```

**Terminal 2 - Celery Beat (Scheduler):**
```bash
cd backend
./start_celery_beat.sh
```

**Terminal 3 - Flower (Monitoring) - Optional:**
```bash
cd backend
./start_flower.sh
```

### 5. Verify Everything is Running

```bash
# Check worker status
celery -A celery_app:celery_app inspect active

# Check Redis
redis-cli ping

# View Flower dashboard
# Open: http://localhost:5555
```

## Test Celery

### Python Test

```python
# In Python shell or script
from app.tasks.email_tasks import send_test_email

# Queue a test email
task = send_test_email.delay(
    to_email="test@example.com",
    test_mode=True
)

print(f"Task ID: {task.id}")
print(f"Status: {task.status}")

# Get result (will block until complete)
result = task.get(timeout=30)
print(result)
```

### API Test

```bash
# Using the API to send email asynchronously
curl -X POST http://localhost:8000/api/campaigns/123/launch
```

## Common Commands

### Worker Management

```bash
# Start worker for specific queue
./start_celery_worker.sh email

# Start worker for scraper queue
./start_celery_worker.sh scraper

# Stop worker
# Press Ctrl+C in terminal where worker is running
```

### Monitor Tasks

```bash
# Active tasks
celery -A celery_app:celery_app inspect active

# Worker stats
celery -A celery_app:celery_app inspect stats

# Registered tasks
celery -A celery_app:celery_app inspect registered
```

### Redis Commands

```bash
# Check queue length
redis-cli LLEN celery

# Monitor Redis
redis-cli monitor

# Clear all tasks (CAREFUL!)
celery -A celery_app:celery_app purge
```

## Troubleshooting

### Redis not running
```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis-server
```

### ImportError: No module named 'celery'
```bash
pip install -r requirements.txt
```

### Workers not processing tasks
```bash
# Check if Redis is accessible
redis-cli ping

# Check if workers are registered
celery -A celery_app:celery_app inspect active

# Restart workers
# Ctrl+C to stop, then run start script again
```

### Can't find celery_app
```bash
# Make sure you're in backend directory
cd backend

# Check PYTHONPATH
export PYTHONPATH="${PWD}:${PYTHONPATH}"
```

## Queue Overview

| Queue     | Purpose                           | Workers Needed |
|-----------|-----------------------------------|----------------|
| `email`   | Email sending, campaigns          | 1-2            |
| `scraper` | Web scraping                      | 1              |
| `ai`      | AI/ML processing                  | 1              |
| `demo`    | Demo site generation              | 1              |
| `default` | General tasks                     | 1              |

## Production Deployment

For production, see: `CELERY_SETUP_GUIDE.md`

Key differences:
- Use Supervisor or Systemd
- Run multiple workers per queue
- Set up monitoring and alerts
- Configure Redis persistence
- Use separate Redis instances for broker/backend

## Need Help?

1. Check logs in worker terminal output
2. View Flower dashboard: http://localhost:5555
3. Check Redis: `redis-cli monitor`
4. Review `CELERY_SETUP_GUIDE.md` for detailed docs
5. Check task code in `app/tasks/`

---

**Happy Task Processing! 🎉**
