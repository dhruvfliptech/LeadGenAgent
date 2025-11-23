#!/bin/bash

# Production Deployment Script (Deprecated Docker Flow)
# NOTE: Docker-based deployment has been deprecated in favor of native/server installs.
# This script remains for historical reference only and will exit with guidance.

set -e  # Exit on any error

echo "⚠️  Docker deployment is deprecated. Use native/systemd or your platform's buildpack."
echo "See backend/DEPLOYMENT_OPERATIONS_GUIDE.md for current guidance."
exit 1

# Check if we're in the right directory
# The legacy Docker steps are intentionally disabled.

# Check for production environment file
if [ ! -f "deployment/.env.prod" ]; then
    echo "❌ Production environment file not found!"
    echo "Please copy deployment/.env.prod.example to deployment/.env.prod and configure it"
    exit 1
fi

# Load production environment
source deployment/.env.prod

# Validate required environment variables
required_vars=("POSTGRES_PASSWORD" "SECRET_KEY" "FRONTEND_DOMAIN" "BACKEND_DOMAIN")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set"
        exit 1
    fi
done

# Build production images
echo "🐳 Building production Docker images..."
docker-compose -f deployment/docker-compose.prod.yml build

# Stop existing production containers
echo "🛑 Stopping existing production containers..."
docker-compose -f deployment/docker-compose.prod.yml down || true

# Start production services
echo "🚀 Starting production services..."
docker-compose -f deployment/docker-compose.prod.yml up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 15

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f deployment/docker-compose.prod.yml exec -T backend alembic upgrade head

# Check service health
echo "🔍 Checking service health..."
sleep 10

# Backend health check
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker-compose -f deployment/docker-compose.prod.yml logs backend
    exit 1
fi

# Frontend health check
if curl -f http://localhost &> /dev/null; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend health check failed"
    docker-compose -f deployment/docker-compose.prod.yml logs frontend
    exit 1
fi

echo ""
echo "🎉 Production deployment complete!"
echo ""
echo "🌐 Your application is now running:"
echo "   - Frontend: https://$FRONTEND_DOMAIN (or http://localhost)"
echo "   - Backend: https://$BACKEND_DOMAIN (or http://localhost:8000)"
echo ""
echo "🔧 Production management commands:"
echo "   - View logs: docker-compose -f deployment/docker-compose.prod.yml logs -f"
echo "   - Stop: docker-compose -f deployment/docker-compose.prod.yml down"
echo "   - Restart: docker-compose -f deployment/docker-compose.prod.yml restart"
echo "   - Update: git pull && ./scripts/deploy.sh"
echo ""
echo "⚠️  Don't forget to:"
echo "   - Set up SSL certificates for HTTPS"
echo "   - Configure your domain DNS"
echo "   - Set up monitoring and backups"
echo "   - Review security settings"