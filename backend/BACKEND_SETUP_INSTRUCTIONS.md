# Backend Setup Instructions

## Quick Start (Automated)

Run the setup script:
```bash
cd /Users/deepaliraithatha/Developer/craigslist-leads-full-main/backend
./setup_backend.sh
```

---

## Manual Setup (Step-by-Step)

### Step 1: Create Virtual Environment

```bash
cd /Users/deepaliraithatha/Developer/craigslist-leads-full-main/backend
python3 -m venv venv
```

**Expected output:** Creates a `venv/` directory

---

### Step 2: Activate Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

**You should see** `(venv)` prefix in your terminal prompt.

---

### Step 3: Upgrade pip

```bash
pip install --upgrade pip
```

---

### Step 4: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Expected:** Installs ~50-60 packages including:
- FastAPI
- SQLAlchemy
- PostgreSQL drivers
- Redis clients
- AI SDKs (OpenAI, Anthropic)
- Celery
- And more...

**This may take 2-5 minutes.**

---

### Step 5: Install Playwright Browsers

```bash
playwright install chromium
```

**Expected:** Downloads Chromium browser (~100MB) for web scraping.

---

### Step 6: Create Environment File

```bash
cp .env.example .env
```

Then **EDIT** the `.env` file with your actual configuration.

---

### Step 7: Configure .env File

Open `.env` in a text editor and configure these **required** settings:

#### Database Configuration (REQUIRED)

```env
DATABASE_URL=postgresql://username:password@localhost:5432/craigleads
```

**If you don't have PostgreSQL installed:**

**On macOS (using Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb craigleads
```

**On Ubuntu/Debian:**
```bash
sudo apt-get install postgresql-15
sudo systemctl start postgresql
sudo -u postgres createdb craigleads
```

**Using Docker:**
```bash
docker run --name craigleads-postgres \
  -e POSTGRES_PASSWORD=yourpassword \
  -e POSTGRES_DB=craigleads \
  -p 5432:5432 \
  -d postgres:15

# Then use:
# DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/craigleads
```

---

#### Redis Configuration (OPTIONAL but recommended)

```env
REDIS_URL=redis://localhost:6379/0
```

**If you don't have Redis installed:**

**On macOS:**
```bash
brew install redis
brew services start redis
```

**On Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

**Using Docker:**
```bash
docker run --name craigleads-redis \
  -p 6379:6379 \
  -d redis:7

# Then use:
# REDIS_URL=redis://localhost:6379/0
```

---

#### Security Settings (REQUIRED)

Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Then add to `.env`:
```env
SECRET_KEY=<paste-the-generated-key-here>
```

---

#### CORS Configuration (REQUIRED for frontend)

```env
ALLOWED_HOSTS=http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5176
```

---

#### AI Service API Keys (OPTIONAL - for AI features)

```env
# OpenAI (for GPT-4, GPT-3.5, embeddings)
OPENAI_API_KEY=sk-...

# Anthropic (for Claude)
ANTHROPIC_API_KEY=sk-ant-...

# OpenRouter (for multi-model access)
OPENROUTER_API_KEY=sk-or-...

# ElevenLabs (for voice synthesis)
ELEVENLABS_API_KEY=...

# Hunter.io (for email finding)
HUNTER_API_KEY=...
```

---

#### Other Optional Services

```env
# 2Captcha (for CAPTCHA solving)
TWOCAPTCHA_API_KEY=...

# Vercel (for demo site deployment)
VERCEL_TOKEN=...

# Piloterr (for LinkedIn scraping)
PILOTERR_API_KEY=...
```

---

### Step 8: Create Database Tables

```bash
python create_tables_simple.py
```

**Expected output:**
```
Creating database tables...
✓ Tables created successfully
✓ Database initialized
```

---

### Step 9: Start the Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**The server is now running!**

Open your browser and go to:
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Main Endpoint:** http://localhost:8000/

---

## Troubleshooting

### Issue: "pg_config executable not found"

**Fix:** Install PostgreSQL development headers
```bash
# macOS
brew install postgresql

# Ubuntu/Debian
sudo apt-get install libpq-dev python3-dev
```

Then reinstall dependencies:
```bash
pip install -r requirements.txt
```

---

### Issue: "Can't connect to database"

**Check:**
1. Is PostgreSQL running?
   ```bash
   # macOS
   brew services list | grep postgresql

   # Linux
   sudo systemctl status postgresql
   ```

2. Is DATABASE_URL correct in `.env`?

3. Can you connect manually?
   ```bash
   psql postgresql://username:password@localhost:5432/craigleads
   ```

---

### Issue: "ModuleNotFoundError"

**Fix:** Make sure virtual environment is activated
```bash
source venv/bin/activate  # You should see (venv) prefix
pip install -r requirements.txt
```

---

### Issue: "Redis connection failed"

Redis is **optional** for basic operation. The application will work without it but:
- Job queue will be disabled
- Caching will be disabled

To install Redis:
```bash
# macOS
brew install redis
brew services start redis

# Or use Docker
docker run -p 6379:6379 -d redis:7
```

---

### Issue: "Port 8000 already in use"

**Fix:** Change the port
```bash
uvicorn app.main:app --reload --port 8080
```

---

## Verification Checklist

After setup, verify everything works:

- [ ] **Virtual environment created** (`venv/` directory exists)
- [ ] **Dependencies installed** (`pip list` shows packages)
- [ ] **Playwright installed** (`playwright --version` works)
- [ ] **Environment file created** (`.env` exists and configured)
- [ ] **Database created** (tables exist)
- [ ] **Server starts** (http://localhost:8000 accessible)
- [ ] **API docs load** (http://localhost:8000/docs opens)
- [ ] **Health check passes** (http://localhost:8000/health returns healthy)

---

## Next Steps

Once the backend is running:

1. **Test API endpoints** using the Swagger UI at http://localhost:8000/docs

2. **Setup frontend** (in separate terminal):
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```

3. **Apply production fixes** from [QUICK_FIX_GUIDE.md](../QUICK_FIX_GUIDE.md)

4. **Start background workers** (optional):
   ```bash
   # In separate terminals
   celery -A celery_app worker --loglevel=info
   celery -A celery_app beat --loglevel=info
   ```

---

## Production Deployment

For production deployment, see:
- [QUICK_FIX_GUIDE.md](../QUICK_FIX_GUIDE.md) - Critical fixes before deployment
- [PRODUCTION_ISSUES_ANALYSIS.md](../PRODUCTION_ISSUES_ANALYSIS.md) - Complete analysis
- [DEPLOYMENT_OPERATIONS_GUIDE.md](./DEPLOYMENT_OPERATIONS_GUIDE.md) - Deployment guide

---

## Need Help?

**Common commands:**
```bash
# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn app.main:app --reload

# Check logs
tail -f app.log

# Database shell
psql $DATABASE_URL
```

**Documentation:**
- `/docs` - API documentation
- `TECHNICAL_PROJECT_OVERVIEW.md` - Architecture overview
- `API_DOCUMENTATION_COMPLETE.md` - Complete API reference

---

**Last Updated:** November 9, 2025
