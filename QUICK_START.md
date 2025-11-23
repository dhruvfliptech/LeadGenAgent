# CraigLeads Pro - Quick Start Guide

Get your CraigLeads Pro application running locally in 5 minutes!

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] PostgreSQL installed and running
- [ ] Redis installed and running (optional but recommended)
- [ ] Git installed

## Quick Setup (5 Minutes)

### 1. Install System Dependencies

**macOS**:
```bash
brew install postgresql@15 redis
brew services start postgresql@15
brew services start redis
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib redis-server
sudo systemctl start postgresql redis
```

**Windows**:
- Download PostgreSQL from: https://www.postgresql.org/download/windows/
- Download Redis from: https://github.com/microsoftarchive/redis/releases
- Or use Docker (recommended for Windows)

### 2. Create Database

```bash
# Connect to PostgreSQL
psql postgres

# Run these commands in psql:
CREATE DATABASE craigleads;
\q
```

### 3. Setup Backend (2 minutes)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies (this takes ~1-2 minutes)
pip install -r requirements.txt

# Install browser for web scraping
playwright install chromium

# Create database tables
cd ..
python create_tables.py

# Start backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**✅ Backend should now be running on http://localhost:8000**

Test it: Open http://localhost:8000/docs in your browser

### 4. Setup Frontend (2 minutes)

Open a NEW terminal window:

```bash
cd frontend

# Install dependencies (this takes ~1-2 minutes)
npm install

# Start frontend
npm run dev
```

**✅ Frontend should now be running on http://localhost:5176**

Test it: Open http://localhost:5176 in your browser

## Verify Everything Works

1. **Backend Health Check**:
   - Visit: http://localhost:8000/health
   - Should see: `{"status": "healthy", ...}`

2. **API Documentation**:
   - Visit: http://localhost:8000/docs
   - Should see: Interactive Swagger UI

3. **Frontend**:
   - Visit: http://localhost:5176
   - Should see: CraigLeads Pro dashboard
   - Check browser console (F12) - should have no errors

## Common Issues & Quick Fixes

### "Database connection failed"

```bash
# Check if PostgreSQL is running
# macOS:
brew services list

# Linux:
sudo systemctl status postgresql

# If not running, start it:
brew services start postgresql@15  # macOS
sudo systemctl start postgresql    # Linux
```

### "Redis connection failed"

Redis is optional but recommended. If you don't have Redis:

Edit `backend/.env` and comment out:
```bash
# REDIS_URL=redis://localhost:6379/0
```

### "Port already in use"

Backend (8000):
```bash
lsof -ti:8000 | xargs kill -9
```

Frontend (5176):
```bash
lsof -ti:5176 | xargs kill -9
```

### "Module not found"

Backend:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

Frontend:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Environment Configuration

### Backend Configuration (`backend/.env`)

The `.env` file is pre-configured for local development. Key settings:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/craigleads
REDIS_URL=redis://localhost:6379/0
ENVIRONMENT=development
DEBUG=true
```

**Optional**: Add API keys for AI features:
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-...
```

### Frontend Configuration (`frontend/.env.development`)

Pre-configured to connect to local backend:

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_USE_MOCK_DATA=false
```

## Testing the Application

### 1. Test API Endpoints

Visit http://localhost:8000/docs and try these endpoints:

- **GET /health** - Check system health
- **GET /api/v1/locations** - Get locations
- **GET /api/v1/scraper/categories** - Get Craigslist categories

### 2. Test Frontend Features

1. **Navigation**: Click through all tabs (Dashboard, Leads, Scraper, etc.)
2. **API Connectivity**: Check browser Network tab for successful API calls
3. **WebSocket**: Should see WS connection in Network tab
4. **UI Rendering**: No blank pages or errors

## Development Workflow

### Making Changes

**Backend**:
1. Edit files in `backend/app/`
2. Save - server auto-reloads (uvicorn --reload)
3. Test changes in browser or API docs

**Frontend**:
1. Edit files in `frontend/src/`
2. Save - Vite hot-reloads automatically
3. See changes instantly in browser

### Checking Logs

**Backend**:
- Logs appear in terminal where uvicorn is running
- Check for errors after each request

**Frontend**:
- Open browser DevTools (F12) → Console
- Check for JavaScript errors

## Next Steps

After confirming everything works locally:

1. **Explore Features**:
   - Read [README.md](README.md) for feature overview
   - Check [REQUIREMENTS.md](REQUIREMENTS.md) for detailed specs

2. **Deploy to Production**:
   - Follow [DEPLOYMENT_INSTRUCTIONS.md](DEPLOYMENT_INSTRUCTIONS.md)
   - Deploy backend to Render
   - Deploy frontend to Netlify

3. **Configure Advanced Features**:
   - Add AI API keys for auto-responder
   - Set up email integration
   - Configure notification services

## Quick Commands Reference

### Backend

```bash
# Activate virtual environment
cd backend && source venv/bin/activate

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run database migrations
python create_tables.py

# Install new dependency
pip install <package-name>
pip freeze > requirements.txt
```

### Frontend

```bash
# Start dev server
cd frontend && npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type check
npm run type-check

# Lint
npm run lint
```

### Database

```bash
# Connect to database
psql craigleads

# View tables
\dt

# View table structure
\d leads

# Exit
\q
```

### Redis

```bash
# Connect to Redis
redis-cli

# Check connection
PING  # Should return "PONG"

# View keys
KEYS *

# Exit
exit
```

## Stopping the Application

1. **Backend**: Press `Ctrl+C` in backend terminal
2. **Frontend**: Press `Ctrl+C` in frontend terminal
3. **Services** (optional):
   ```bash
   # macOS
   brew services stop postgresql@15
   brew services stop redis

   # Linux
   sudo systemctl stop postgresql
   sudo systemctl stop redis
   ```

## Getting Help

If you encounter issues:

1. Check this guide's "Common Issues" section
2. Review error messages in terminal/console
3. Check logs in browser DevTools
4. Review [DEPLOYMENT_INSTRUCTIONS.md](DEPLOYMENT_INSTRUCTIONS.md) for more details
5. Check [PRODUCTION_ISSUES_ANALYSIS.md](PRODUCTION_ISSUES_ANALYSIS.md) for known issues

## Success Checklist

- [x] PostgreSQL installed and running
- [x] Redis installed and running (optional)
- [x] Database created (`craigleads`)
- [x] Backend dependencies installed
- [x] Backend running on http://localhost:8000
- [x] Backend health check passes
- [x] Frontend dependencies installed
- [x] Frontend running on http://localhost:5176
- [x] Frontend loads without errors
- [x] API calls working (check Network tab)
- [x] No console errors in browser

**Congratulations!** 🎉 You're ready to start developing or deploy to production!

---

## Alternative: Using Docker (Advanced)

If you prefer Docker, create these files:

**docker-compose.yml** (in root):
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: craigleads
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

Start services:
```bash
docker-compose up -d
```

Then follow the regular setup steps for backend and frontend.
