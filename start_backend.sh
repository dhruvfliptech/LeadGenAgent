#!/bin/bash

# Export environment variables for local development
export DATABASE_URL="postgresql://postgres@localhost:5432/craigslist_leads"
export REDIS_URL="redis://localhost:6379"
export ENVIRONMENT="development"
export SECRET_KEY="dev-secret-key-change-in-production"
export DEBUG="true"

# Export optional API keys (use existing values or empty string)
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"
export POSTMARK_SERVER_TOKEN="${POSTMARK_SERVER_TOKEN:-}"
export POSTMARK_FROM_EMAIL="${POSTMARK_FROM_EMAIL:-sales@yourcompany.com}"

# Validation warnings for required services
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "⚠️  WARNING: OPENROUTER_API_KEY not set - AI features will fail"
    echo "   Set it with: export OPENROUTER_API_KEY=sk-or-v1-..."
fi

if [ -z "$POSTMARK_SERVER_TOKEN" ]; then
    echo "⚠️  WARNING: POSTMARK_SERVER_TOKEN not set - Email sending will fail"
    echo "   Set it with: export POSTMARK_SERVER_TOKEN=..."
fi

# Navigate to backend directory
cd backend

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the FastAPI server
echo "Starting FastAPI server on http://localhost:8001"
echo "API Documentation available at http://localhost:8001/docs"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001