# Celery Setup Checklist

Use this checklist to get Celery workers up and running.

## Pre-Installation Checklist

- [ ] Python 3.8+ installed
- [ ] Backend virtual environment created
- [ ] Redis installed on system

## Installation Steps

### Step 1: Install Redis
```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo apt install redis-server
sudo systemctl start redis-server
```

- [ ] Redis installed
- [ ] Redis service started
- [ ] Verified: `redis-cli ping` returns "PONG"

### Step 2: Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

- [ ] Dependencies installed
- [ ] No installation errors
- [ ] Celery available: `celery --version`

### Step 3: Configure Environment
```bash
# Copy example config
cp .env.celery.example .env.celery

# Add to your .env file
cat .env.celery >> .env
```

- [ ] `.env` file exists
- [ ] Redis configuration added
- [ ] Celery settings configured

### Step 4: Test Configuration
```bash
cd backend
python -c "from celery_app import celery_app; print('✓ Celery configured correctly')"
```

- [ ] Configuration loads without errors
- [ ] No import errors

## Running Celery

### Basic Setup (Development)

Open 3 terminal windows:

**Terminal 1: Worker**
```bash
cd backend
./start_celery_worker.sh
```
- [ ] Worker started successfully
- [ ] No connection errors
- [ ] See "ready" message

**Terminal 2: Beat (Optional for scheduled tasks)**
```bash
cd backend
./start_celery_beat.sh
```
- [ ] Beat started successfully
- [ ] Schedule loaded
- [ ] No errors

**Terminal 3: Flower (Optional for monitoring)**
```bash
cd backend
./start_flower.sh
```
- [ ] Flower started
- [ ] Can access http://localhost:5555
- [ ] Dashboard loads

## Testing

### Test 1: Debug Task
```python
from celery_app import celery_app

task = celery_app.send_task('celery_app.debug_task')
result = task.get(timeout=10)
print(result)  # Should print "Celery is working!"
```

- [ ] Task queued successfully
- [ ] Task executed
- [ ] Result received

### Test 2: Email Task (TEST_MODE)
```python
from app.tasks.email_tasks import send_test_email

task = send_test_email.delay(
    to_email="test@example.com",
    test_mode=True
)
result = task.get(timeout=30)
print(result)
```

- [ ] Task queued
- [ ] Task executed
- [ ] Test email logged (not sent)

### Test 3: Check Worker Status
```bash
celery -A celery_app:celery_app inspect active
```

- [ ] Workers are registered
- [ ] No active tasks (if nothing running)
- [ ] Stats show correct queues

### Test 4: Check Flower
Visit: http://localhost:5555

- [ ] Dashboard loads
- [ ] Shows active workers
- [ ] Can see tasks

## Verification

### System Health Checks

```bash
# Redis
redis-cli ping
# Expected: PONG
```
- [ ] Redis responding

```bash
# Workers
celery -A celery_app:celery_app inspect active
# Expected: Worker list
```
- [ ] Workers active

```bash
# Registered tasks
celery -A celery_app:celery_app inspect registered
# Expected: 43 tasks
```
- [ ] All tasks registered

```bash
# Queue lengths
redis-cli LLEN celery
redis-cli LLEN email
redis-cli LLEN scraper
# Expected: 0 (if no tasks queued)
```
- [ ] Queues exist and accessible

## Production Deployment (Optional)

### Production Checklist

- [ ] Supervisor or Systemd configured
- [ ] Multiple workers per queue
- [ ] Redis persistence enabled
- [ ] Flower authentication configured
- [ ] Logging to files configured
- [ ] Log rotation set up
- [ ] Monitoring/alerts configured
- [ ] Backup strategy for Redis

### Production Testing

- [ ] Workers restart automatically on failure
- [ ] Beat scheduler restarts automatically
- [ ] Redis persists on restart
- [ ] Logs are being written
- [ ] Monitoring alerts working
- [ ] Load testing completed

## Troubleshooting

If something doesn't work:

### Redis Issues
```bash
# Check if Redis is running
ps aux | grep redis

# Check Redis logs
redis-cli info

# Restart Redis
brew services restart redis  # macOS
sudo systemctl restart redis-server  # Linux
```

### Worker Issues
```bash
# Check for errors in terminal output
# Common fixes:

# 1. PYTHONPATH issue
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# 2. Missing dependencies
pip install -r requirements.txt

# 3. Redis connection
# Check REDIS_HOST in .env
```

### Import Issues
```bash
# Make sure you're in backend directory
cd backend

# Check if modules import
python -c "from app.tasks.email_tasks import send_single_email; print('OK')"

# Reinstall if needed
pip install --force-reinstall -r requirements.txt
```

## Quick Commands Reference

```bash
# Start worker (all queues)
./start_celery_worker.sh

# Start worker (specific queue)
./start_celery_worker.sh email

# Start beat scheduler
./start_celery_beat.sh

# Start Flower
./start_flower.sh

# Check active tasks
celery -A celery_app:celery_app inspect active

# Check worker stats
celery -A celery_app:celery_app inspect stats

# Purge all tasks (CAREFUL!)
celery -A celery_app:celery_app purge

# Stop worker
# Press Ctrl+C in worker terminal
```

## Documentation

Read these files for more information:

- [ ] `CELERY_QUICK_START.md` - Quick start guide
- [ ] `CELERY_SETUP_GUIDE.md` - Complete documentation
- [ ] `CELERY_IMPLEMENTATION_SUMMARY.md` - Implementation details
- [ ] `.env.celery.example` - All configuration options

## Support

If you need help:

1. Check worker logs (terminal output)
2. Check Flower dashboard (http://localhost:5555)
3. Check Redis: `redis-cli monitor`
4. Review documentation files
5. Check task code in `app/tasks/`

## Final Verification

Everything working? Check these:

- [ ] ✅ Redis running and accessible
- [ ] ✅ Worker processing tasks
- [ ] ✅ Beat scheduling tasks (if enabled)
- [ ] ✅ Flower showing stats (if enabled)
- [ ] ✅ Test tasks execute successfully
- [ ] ✅ No errors in logs
- [ ] ✅ Email tasks work in TEST_MODE
- [ ] ✅ Can launch campaigns asynchronously
- [ ] ✅ Task results are stored and retrievable
- [ ] ✅ Scheduled tasks running (if Beat enabled)

## Success! 🎉

If all items are checked, your Celery setup is complete and working!

You can now:
- Send emails asynchronously
- Launch campaigns in the background
- Run scraping jobs
- Process AI tasks
- Generate demo sites

**Next Steps:**
1. Test with real campaigns
2. Monitor performance in Flower
3. Adjust concurrency based on load
4. Set up production deployment

---

**Need Help?** See `CELERY_SETUP_GUIDE.md` for detailed documentation.
