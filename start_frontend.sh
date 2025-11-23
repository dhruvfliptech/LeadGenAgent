#!/bin/bash

# Navigate to frontend directory
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start the frontend development server
echo "Starting frontend development server on http://localhost:5176"
VITE_API_URL=http://localhost:8001 VITE_WS_URL=ws://localhost:8001 npm run dev -- --port 5176