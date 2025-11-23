#!/bin/bash

# Craigslist Lead Generation Dashboard Setup Script
# This script helps set up the development environment

set -e  # Exit on any error

echo "🚀 Setting up Craigslist Lead Generation Dashboard..."

# Docker is no longer required for local setup.
# This script prepares folders and .env files for native development.

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file. Please review and update the values as needed."
fi

# Create directories that might be needed
echo "📁 Creating required directories..."
mkdir -p backend/logs
mkdir -p frontend/dist
mkdir -p database/backups

# Generate a random secret key if not set
if grep -q "your-secret-key-change-in-production" .env; then
    echo "🔐 Generating secure secret key..."
    if command -v openssl &> /dev/null; then
        SECRET_KEY=$(openssl rand -hex 32)
        sed -i.bak "s/your-secret-key-change-in-production-use-openssl-rand-hex-32/$SECRET_KEY/" .env
        rm .env.bak
        echo "✅ Generated and set secure secret key"
    else
        echo "⚠️  OpenSSL not found. Please manually update SECRET_KEY in .env file"
    fi
fi

echo "✅ Setup complete. To run locally, use:"
echo "   bash start_local.sh"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📊 Expected local services after start_local.sh:"
echo "   - Frontend: http://localhost:5176"
echo "   - Backend API: http://localhost:8001"
echo "   - API Docs: http://localhost:8001/docs"
echo "   - Database: localhost:5432"
echo "   - Redis: localhost:6379"
echo ""
echo "🔧 Useful commands:"
echo "   - Start: bash start_local.sh"
echo "   - Backend logs: cd backend && tail -f logs/app.log"
echo "   - Access database: psql -U postgres -d craigslist_leads"
echo ""
echo "📖 Check the README.md for more information!"