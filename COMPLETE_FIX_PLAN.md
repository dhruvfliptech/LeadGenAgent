# Complete Fix Plan - Executable Steps

This document provides exact commands and code changes to fix all critical bugs.

---

## Progress So Far (Completed)

✅ **Import errors fixed**:
- `auto_responder.py` - Fixed templates import
- `export_service.py` - Commented out non-existent model imports

✅ **Feature flags set correctly**:
- All broken features now return `False`

✅ **Redis initialization graceful**:
- Won't crash if Redis unavailable (partial - needs completion)

---

## Remaining Critical Fixes (Order of Execution)

### Fix 1: Disable Broken Services Temporarily (5 min)

The fastest path is to disable broken services until they can be properly refactored.

```bash
cd /Users/greenmachine2.0/Craigslist/backend

# Rename broken service files so they don't load
mv app/services/auto_responder.py app/services/auto_responder.py.BROKEN
mv app/services/export_service.py app/services/export_service.py.BROKEN
mv app/services/notification_service.py app/services/notification_service.py.BROKEN 2>/dev/null || true
```

**Result**: Server can start, but auto-responder/export features disabled

---

### Fix 2: Update Main App to Handle Missing Services (5 min)

Edit `backend/app/main.py` - comment out broken routers:

```python
# Line 234-239: Comment out broken Phase 3 routers
# Include routers - Phase 3 (DISABLED - services need refactoring)
# app.include_router(templates.router, prefix="/api/v1/templates", tags=["templates"])
# app.include_router(rules.router, prefix="/api/v1/rules", tags=["rules"])
# app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
# app.include_router(schedule.router, prefix="/api/v1/schedules", tags=["schedules"])
# app.include_router(export.router, prefix="/api/v1/exports", tags=["exports"])
app.include_router(websocket.router, tags=["websocket"])
```

**Result**: Server starts without import errors

---

### Fix 3: Fix Response Generator Hardcoded Data (10 min)

Edit `backend/app/services/response_generator.py` around line 32:

**Current (WRONG)**:
```python
self.user_profile = {
    'user_name': settings.USER_NAME if hasattr(settings, 'USER_NAME') else 'John Doe',
    'user_email': settings.USER_EMAIL if hasattr(settings, 'USER_EMAIL') else 'john@example.com',
    'user_phone': settings.USER_PHONE if hasattr(settings, 'USER_PHONE') else '555-0100',
}
```

**Fixed**:
```python
# Fail explicitly if user profile not configured
if not settings.USER_NAME or not settings.USER_EMAIL:
    logger.warning("USER_NAME and USER_EMAIL not configured - response generation may fail")
    self.user_profile = {
        'user_name': '',
        'user_email': '',
        'user_phone': '',
    }
else:
    self.user_profile = {
        'user_name': settings.USER_NAME,
        'user_email': settings.USER_EMAIL,
        'user_phone': settings.USER_PHONE or '',
    }
```

**Result**: No fake data in responses

---

### Fix 4: Complete Redis Fix in Scraper (30 min)

This requires updating all `redis_client` usages. Create a wrapper that handles None:

Add to `backend/app/api/endpoints/scraper.py` after the `get_redis_client()` function:

```python
def redis_get(key: str) -> Optional[str]:
    """Safe Redis get - returns None if Redis unavailable."""
    rc = get_redis_client()
    if rc is None:
        return None
    try:
        return rc.get(key)
    except Exception as e:
        logger.error(f"Redis get error: {e}")
        return None

def redis_set(key: str, value: str, ex: Optional[int] = None) -> bool:
    """Safe Redis set - returns False if Redis unavailable."""
    rc = get_redis_client()
    if rc is None:
        return False
    try:
        if ex:
            rc.setex(key, ex, value)
        else:
            rc.set(key, value)
        return True
    except Exception as e:
        logger.error(f"Redis set error: {e}")
        return False

def redis_hset(name: str, mapping: dict) -> bool:
    """Safe Redis hset."""
    rc = get_redis_client()
    if rc is None:
        return False
    try:
        rc.hset(name, mapping=mapping)
        return True
    except Exception as e:
        logger.error(f"Redis hset error: {e}")
        return False

def redis_hget(name: str, key: str) -> Optional[str]:
    """Safe Redis hget."""
    rc = get_redis_client()
    if rc is None:
        return None
    try:
        return rc.hget(name, key)
    except Exception as e:
        logger.error(f"Redis hget error: {e}")
        return None
```

Then search and replace in the file:
- `redis_client.get(` → `redis_get(`
- `redis_client.setex(` → `redis_set(..., ex=`
- `redis_client.hset(` → `redis_hset(`
- `redis_client.hget(` → `redis_hget(`

**Result**: Scraper degrades gracefully without Redis

---

### Fix 5: Fix Scraper Background Task Session (20 min)

Edit `backend/app/api/endpoints/scraper.py` - the `process_scrape_job` function:

**Current (WRONG)** - around line 300:
```python
background_tasks.add_task(process_scrape_job, job_id, updated_job, db)
```

**Fixed**:
```python
# Don't pass db session to background task!
background_tasks.add_task(process_scrape_job, job_id, updated_job)
```

Then in `process_scrape_job` function (around line 410):
```python
async def process_scrape_job(job_id: str, job_data: ScrapeJobCreate):
    """Background task to process scrape job - creates its own DB session."""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            # ... existing scraping logic ...
            # When saving leads:
            await save_lead_to_db(db, lead_data)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Scrape job {job_id} failed: {e}")
```

**Result**: Background tasks have proper database sessions

---

### Fix 6: Fix Scraper job_info Payload (15 min)

Edit `backend/app/api/endpoints/scraper.py` around line 378-409.

**Current (WRONG)**:
```python
job_info = {
    "job_id": job_id,
    "status": "running",
    "started_at": datetime.now().isoformat(),
    "progress": 0
}
```

**Fixed**:
```python
job_info = {
    "job_id": job_id,
    "status": "running",
    "started_at": datetime.now().isoformat(),
    "progress": 0,
    "errors": [],  # REQUIRED
    "results": {
        "leads_found": 0,
        "leads_saved": 0,
        "leads_skipped": 0
    },
    "locations": job_data.get("locations", []),
    "categories": job_data.get("categories", []),
    "enable_email_extraction": job_data.get("enable_email_extraction", False),
    "captcha_api_key": job_data.get("captcha_api_key")
}
```

**Result**: No KeyErrors when scraper logs errors

---

### Fix 7: Fix Frontend API Mismatches (30 min)

Edit `frontend/src/services/phase3Api.ts`:

Add feature flag checks:

```typescript
// At top of file
const FEATURES_ENABLED = {
  templates: false,  // Disabled until backend fixed
  abTesting: false,
  analytics: false,
  notifications: false,
  schedules: false,
  exports: false,
};

// Wrap each API call
export const phase3Api = {
  // Templates - disabled
  getTemplates: () =>
    FEATURES_ENABLED.templates
      ? api.get<Template[]>('/api/v1/templates')
      : Promise.resolve({ data: [] }),

  // Similarly for all other calls...
  // Return empty data or throw clear error
};
```

**Result**: No 404 errors, features gracefully disabled

---

### Fix 8: Fix WebSocket Endpoint Mismatches (15 min)

Edit `frontend/src/hooks/useWebSocket.ts`:

**Current (WRONG)**:
```typescript
const wsUrl = `${wsEnv}/ws/notifications`
```

**Fixed**:
```typescript
// Use the main WebSocket endpoint that actually exists
const wsUrl = `${wsEnv}/ws`  // Backend has this one
```

Or disable WebSocket completely if not needed:
```typescript
// Return null connection if WebSocket not critical
return {
  isConnected: false,
  lastMessage: null,
  sendMessage: () => {},
};
```

**Result**: No WebSocket errors in console

---

### Fix 9: Add Startup Health Checks (20 min)

Edit `backend/app/main.py` in the `lifespan` function:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager with health checks."""
    # Startup
    logger.info("Starting up CraigLeads Pro API...")

    # Health check 1: Database
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✓ Database connected and tables verified")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        raise

    # Health check 2: Redis (optional)
    try:
        if settings.REDIS_URL:
            import redis
            rc = redis.Redis.from_url(settings.REDIS_URL)
            rc.ping()
            logger.info("✓ Redis connected")
        else:
            logger.warning("⚠ Redis not configured - job queue disabled")
    except Exception as e:
        logger.warning(f"⚠ Redis connection failed: {e} - continuing without cache")

    # Health check 3: Required environment variables
    missing_vars = []
    if settings.ENVIRONMENT == "production":
        if not settings.SECRET_KEY:
            missing_vars.append("SECRET_KEY")
        if "*" in settings.ALLOWED_HOSTS:
            logger.error("✗ ALLOWED_HOSTS contains wildcard in production!")
            raise ValueError("ALLOWED_HOSTS cannot use wildcards in production")

    if missing_vars:
        logger.error(f"✗ Missing required environment variables: {missing_vars}")
        raise ValueError(f"Missing: {missing_vars}")

    logger.info("✓ All health checks passed")
    logger.info("CraigLeads Pro API startup completed successfully")

    yield

    # Shutdown (existing code...)
```

**Result**: Clear feedback about what's working/broken on startup

---

### Fix 10: Create Smoke Tests (45 min)

Create `backend/tests/test_smoke.py`:

```python
"""
Smoke tests - verify basic functionality works.
Run with: pytest tests/test_smoke.py -v
"""

import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check returns 200."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]

@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

@pytest.mark.asyncio
async def test_api_docs():
    """Test API docs are accessible."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/docs")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_leads():
    """Test leads endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/leads/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_locations():
    """Test locations endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/locations/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

# Add more tests as features are fixed...
```

Create `backend/tests/conftest.py`:

```python
"""Pytest configuration."""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.main import app

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres@localhost:5432/craigslist_leads_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """Create test database."""
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(test_db):
    """Get test database session."""
    AsyncTestSession = sessionmaker(
        test_db, class_=AsyncSession, expire_on_commit=False
    )
    async with AsyncTestSession() as session:
        yield session
```

Run tests:
```bash
cd backend
pytest tests/test_smoke.py -v
```

**Result**: Automated verification that basic features work

---

## Execution Order

1. **Immediate (15 min)**:
   - Fix 1: Disable broken services
   - Fix 2: Comment out broken routers
   - Try to start server

2. **Core Fixes (1.5 hours)**:
   - Fix 3: Response generator
   - Fix 4: Redis wrappers
   - Fix 5: Background task sessions
   - Fix 6: job_info payload

3. **Frontend Alignment (45 min)**:
   - Fix 7: API mismatches
   - Fix 8: WebSocket endpoints

4. **Verification (1 hour)**:
   - Fix 9: Health checks
   - Fix 10: Smoke tests
   - Manual testing

**Total time: ~3.5 hours of focused work**

---

## Testing Checklist

After all fixes:

- [ ] Server starts without errors
- [ ] Health check returns 200
- [ ] Can view leads page
- [ ] Can view locations
- [ ] Frontend loads without console errors
- [ ] API docs accessible
- [ ] Smoke tests pass
- [ ] (Optional) Can create a scrape job if Redis configured

---

## What Will Still Need Work

These are larger refactoring efforts beyond immediate fixes:

1. **Singleton services** → Request-scoped (4-6 hours)
2. **Phase 3 endpoints** → Full implementation (8-12 hours)
3. **Complete test coverage** → Unit + integration (8-12 hours)
4. **Authentication** → Add to all endpoints (3-4 hours)

But the system will be **functional and stable** after the above fixes.

---

**Next**: Shall I execute these fixes now?
