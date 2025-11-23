#!/bin/bash

# Run backend natively when Docker issues persist
set -e

cd "$(dirname "$0")/backend"

echo "🐍 Starting Backend Natively (Backup Solution)"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "📋 Installing/updating dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set environment variables for local development
export DATABASE_URL="postgresql://postgres:postgres@localhost:5433/craigslist_leads"
export REDIS_URL="redis://localhost:6380"
export ENVIRONMENT="development"
export PYTHONPATH="${PWD}"

echo "🚀 Starting FastAPI server..."
echo "Backend will be available at: http://localhost:8000"
echo ""
echo "⚠️  Make sure PostgreSQL and Redis are running:"
echo "   - PostgreSQL on port 5433"  
echo "   - Redis on port 6380"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload