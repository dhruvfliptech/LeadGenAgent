# Craigslist Lead Generation System

A comprehensive web scraping and lead management system for Craigslist listings with AI-powered features.

## Features

### Core Functionality
- **Advanced Scraping**: Playwright-based scraper with CAPTCHA solving and email extraction
- **Location Management**: Full hierarchical location system (US, Canada, World regions)
- **Category Selection**: Structured category browsing with multi-select capabilities
- **Lead Management**: Store, categorize, and track leads with contact information
- **Job Queue**: Redis-based job queuing system for scalable scraping operations

### AI & Automation
- **Auto-Responder**: AI-powered email responses with personalization
- **Lead Scoring**: ML-based lead qualification and prioritization
- **Rule Engine**: Configurable business rules for lead processing
- **Notification System**: Multi-channel notifications (email, SMS, Slack, Discord)

### Technical Stack
- **Backend**: FastAPI (Python) with async/await support
- **Frontend**: React + TypeScript + Vite
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache/Queue**: Redis Cloud
- **Scraping**: Playwright with Chromium
- **AI**: OpenAI/Anthropic integration

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (local)
- Redis (local)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install Playwright browsers for scraping
playwright install chromium

# Create database tables
python create_tables_simple.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Environment Configuration
Create `.env` files in both `backend/` and `frontend/` directories (or rely on defaults set by `start_local.sh`):

**Backend (.env)**
```env
DATABASE_URL=postgresql://postgres@localhost:5432/craigslist_leads
REDIS_URL=redis://localhost:6379
OPENROUTER_API_KEY=your-openrouter-key  # For AI features
TWOCAPTCHA_API_KEY=your-2captcha-key    # For CAPTCHA solving
```

**Frontend (.env)**
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Running the Application

**Option 1: Using startup scripts (Recommended)**
```bash
# Start backend (from backend directory)
./start_backend.sh

# Start frontend (from frontend directory)
./start_frontend.sh
```

**Option 2: Manual startup**
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
DATABASE_URL="postgresql://postgres@localhost:5432/craigslist_leads" \
REDIS_URL="redis://localhost:6379" \
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
VITE_API_URL=http://localhost:8000 npm run dev
```

Access the application:
- **Frontend**: http://localhost:5176
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Usage

### Creating a Scrape Job
1. Navigate to the **Scraper** tab
2. Select locations using the hierarchical selector
3. Choose categories (optional)
4. Add keywords (optional)
5. Configure scraping parameters
6. Click "Start Scraping"

### Managing Leads
- View scraped leads in the **Leads** tab
- Filter and search through leads
- Export data in various formats
- Track lead status and interactions

### Setting Up Auto-Responses
1. Create response templates in the **Auto-Responder** section
2. Configure business rules for automatic responses
3. Set up notification preferences
4. Monitor response rates and conversions

## Architecture

### Backend Structure
```
backend/
├── app/
│   ├── api/endpoints/     # FastAPI route handlers
│   ├── core/             # Configuration and database
│   ├── models/           # SQLAlchemy models
│   ├── scrapers/         # Scraping logic
│   ├── services/         # Business logic
│   └── ml/              # Machine learning components
├── migrations/           # Database migrations
└── scripts/             # Utility scripts
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   ├── pages/           # Page components
│   ├── services/        # API clients
│   ├── hooks/           # Custom React hooks
│   └── types/           # TypeScript definitions
└── public/              # Static assets
```

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive Swagger API documentation.

### Key API Endpoints

**Health & Status**
- `GET /health` - System health check with service status

**Locations**
- `GET /api/v1/locations` - List all available locations

**Scraping**
- `GET /api/v1/scraper/categories` - Get Craigslist categories
- `POST /api/v1/scraper/jobs` - Create new scraping job
- `GET /api/v1/scraper/jobs` - List all scraping jobs
- `GET /api/v1/scraper/jobs/{job_id}` - Get job details

**Leads**
- `GET /api/v1/leads` - List all leads with filtering
- `GET /api/v1/leads/{lead_id}` - Get lead details
- `PUT /api/v1/leads/{lead_id}` - Update lead

**WebSocket**
- `WS /ws` - Real-time updates for scraping progress

## Troubleshooting

### Database Issues
**Problem**: `alembic upgrade head` fails
**Solution**: Use `python create_tables_simple.py` instead - this creates all tables directly from models

**Problem**: Connection refused to PostgreSQL
**Solution**: Ensure PostgreSQL is running and accessible at the configured URL

### Frontend Build Issues
**Problem**: TypeScript errors during build
**Solution**: Run `npm run type-check` to identify errors. All errors should be fixed in current version.

**Problem**: Frontend not connecting to backend
**Solution**: Verify `VITE_API_URL` in environment matches backend port (should be `http://localhost:8000`)

### Scraping Issues
**Problem**: CAPTCHA blocking scraping
**Solution**: Configure `TWOCAPTCHA_API_KEY` in backend environment

**Problem**: Playwright browser not found
**Solution**: Run `playwright install chromium` in the backend directory

### Common Setup Issues
**Problem**: Redis connection errors
**Solution**: Ensure Redis is running locally on port 6379

**Problem**: Port already in use
**Solution**: Backend uses 8000, frontend uses 5176. Check for conflicts with `lsof -i :8000` or `lsof -i :5176`

## Known Limitations

- **Alembic migrations**: Currently bypassed in favor of direct table creation via `create_tables_simple.py`
- **Multi-source scraping**: Only Craigslist is fully implemented (Google Maps, LinkedIn, Job Boards are planned)
- **AI features**: Require valid OpenRouter API key for full functionality
- **Location data**: Needs to be populated manually or via seed script (locations table starts empty)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

Private repository - All rights reserved.

## Support

For issues and questions, please create an issue in the repository.