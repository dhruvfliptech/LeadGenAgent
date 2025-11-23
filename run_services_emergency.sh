#!/bin/bash

# Emergency startup script for Craigslist services
# Use when Docker is having issues

echo "🚨 Emergency Service Startup Script"
echo "===================================="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "✓ Checking prerequisites..."
if ! command_exists docker; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

# Try to clean up any hanging containers
echo "🧹 Cleaning up old containers..."
docker rm -f craigslist_postgres craigslist_redis craigslist_backend craigslist_frontend 2>/dev/null || true

# Remove problematic volumes if they exist
echo "🗑️  Removing old volumes..."
docker volume rm craigslist_postgres_data craigslist_redis_data 2>/dev/null || true

# Check Docker daemon
echo "🔍 Checking Docker daemon..."
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker daemon is not running!"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# Check disk space
echo "💾 Checking disk space..."
AVAILABLE_SPACE=$(df -h / | tail -1 | awk '{print $4}')
echo "Available space: $AVAILABLE_SPACE"

# Start services with reduced resource requirements
echo ""
echo "🚀 Starting services with minimal resources..."
echo ""

# Create network if it doesn't exist
docker network create craigslist_network 2>/dev/null || true

# Start PostgreSQL with minimal memory
echo "1️⃣  Starting PostgreSQL..."
docker run -d \
    --name craigslist_postgres \
    --network craigslist_network \
    -e POSTGRES_DB=craigslist_leads \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -p 5433:5432 \
    --memory="256m" \
    --restart unless-stopped \
    postgres:15-alpine

# Wait for PostgreSQL
echo "   Waiting for PostgreSQL to be ready..."
sleep 5

# Start Redis with minimal memory
echo "2️⃣  Starting Redis..."
docker run -d \
    --name craigslist_redis \
    --network craigslist_network \
    -p 6380:6379 \
    --memory="128m" \
    --restart unless-stopped \
    redis:7-alpine

# Wait for Redis
sleep 3

# Check if backend directory exists
if [ -d "./backend" ]; then
    echo "3️⃣  Starting Backend (non-Docker mode)..."
    echo "   Installing Python dependencies..."
    cd backend
    python3 -m venv venv 2>/dev/null || true
    source venv/bin/activate
    pip install -q -r requirements.txt
    
    # Export environment variables
    export DATABASE_URL="postgresql://postgres:postgres@localhost:5433/craigslist_leads"
    export REDIS_URL="redis://localhost:6380"
    export ENVIRONMENT="development"
    
    # Start backend in background
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
    echo "   Backend PID: $!"
    cd ..
else
    echo "⚠️  Backend directory not found, skipping..."
fi

# Check if frontend directory exists
if [ -d "./frontend" ]; then
    echo "4️⃣  Starting Frontend (non-Docker mode)..."
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "   Installing npm dependencies..."
        npm install
    fi
    
    # Export environment variables
    export VITE_API_URL="http://localhost:8000"
    export VITE_WS_URL="ws://localhost:8000"
    
    # Start frontend in background
    nohup npm run dev > ../frontend.log 2>&1 &
    echo "   Frontend PID: $!"
    cd ..
else
    echo "⚠️  Frontend directory not found, skipping..."
fi

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📝 Service URLs:"
echo "   - Frontend: http://localhost:5173"
echo "   - Backend API: http://localhost:8000"
echo "   - Backend Docs: http://localhost:8000/docs"
echo "   - PostgreSQL: localhost:5433"
echo "   - Redis: localhost:6380"
echo ""
echo "📊 Check logs:"
echo "   - Backend: tail -f backend.log"
echo "   - Frontend: tail -f frontend.log"
echo ""
echo "🛑 To stop services:"
echo "   docker stop craigslist_postgres craigslist_redis"
echo "   pkill -f uvicorn"
echo "   pkill -f 'npm run dev'"