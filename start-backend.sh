#!/bin/bash

# CraigLeads Pro - Backend Startup Script
# Run this to start the backend server

set -e

echo "🚀 Starting CraigLeads Pro Backend..."

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if [ ! -f "venv/.dependencies_installed" ]; then
    echo "📥 Installing dependencies (this takes 2-3 minutes)..."
    pip install --upgrade pip
    pip install -r requirements.txt
    playwright install chromium
    touch venv/.dependencies_installed
fi

# Check if database tables exist
echo "🗄️  Checking database tables..."
cd ..
python3 create_tables.py || echo "⚠️  Tables may already exist"
cd backend

# Start the server
echo "✅ Starting backend server..."
echo "📡 Backend will be available at: http://localhost:8000"
echo "📚 API Documentation at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
