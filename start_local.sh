#!/bin/bash

# Local Development Startup Script (No Docker)
# This script starts all services locally without Docker

echo "🚀 Starting Craigslist Lead Scraper (Local Mode)"
echo "================================================"
echo ""

# Check if PostgreSQL and Redis are running
echo "✓ Checking services..."
if ! brew services list | grep -q "postgresql@15.*started"; then
    echo "Starting PostgreSQL..."
    brew services start postgresql@15
fi

if ! brew services list | grep -q "redis.*started"; then
    echo "Starting Redis..."
    brew services start redis
fi

# Create database if it doesn't exist
echo "✓ Setting up database..."
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
createdb craigslist_leads 2>/dev/null || echo "Database already exists"
createuser -s postgres 2>/dev/null || echo "User already exists"

# Initialize database schema
psql -U postgres -d craigslist_leads -f database/init.sql 2>/dev/null || echo "Schema already initialized"

# Start backend
echo ""
echo "Starting Backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3.11 -m venv venv
fi

source venv/bin/activate
echo "Installing/updating backend dependencies..."
pip install -q -r requirements.txt
pip install -q aiohttp croniter openai  # Additional dependencies

export DATABASE_URL="postgresql://postgres@localhost:5432/craigslist_leads"
export REDIS_URL="redis://localhost:6379"

echo "Starting backend server on port 8001..."
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!
cd ..

# Start frontend
echo ""
echo "Starting Frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

export VITE_API_URL="http://localhost:8001"
export VITE_WS_URL="ws://localhost:8001"

echo "Starting frontend server on port 5176..."
npm run dev -- --port 5176 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ All services started successfully!"
echo ""
echo "📝 Service URLs:"
echo "   - Frontend: http://localhost:5176"
echo "   - Backend API: http://localhost:8001"
echo "   - Backend Docs: http://localhost:8001/docs"
echo "   - PostgreSQL: localhost:5432"
echo "   - Redis: localhost:6379"
echo ""
echo "📊 Process IDs:"
echo "   - Backend PID: $BACKEND_PID"
echo "   - Frontend PID: $FRONTEND_PID"
echo ""
echo "🛑 To stop all services:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   brew services stop postgresql@15 redis"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait