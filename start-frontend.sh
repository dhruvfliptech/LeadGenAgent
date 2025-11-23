#!/bin/bash

# CraigLeads Pro - Frontend Startup Script
# Run this to start the frontend dev server

set -e

echo "🚀 Starting CraigLeads Pro Frontend..."

# Navigate to frontend directory
cd "$(dirname "$0")/frontend"

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📥 Installing dependencies (this takes 2-3 minutes)..."
    npm install
fi

# Start the dev server
echo "✅ Starting frontend dev server..."
echo "🌐 Frontend will be available at: http://localhost:5176"
echo ""
echo "Press Ctrl+C to stop"
echo ""

npm run dev
