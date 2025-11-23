#!/bin/bash

###############################################################################
# Backend Deployment Script
# Deploys the FastAPI backend to production/staging environments
#
# Usage: ./scripts/deploy_backend.sh [environment]
# Example: ./scripts/deploy_backend.sh production
###############################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default environment
ENVIRONMENT=${1:-staging}

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
BACKUP_DIR="$PROJECT_ROOT/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$PROJECT_ROOT/logs/deployment_${ENVIRONMENT}_${TIMESTAMP}.log"

# Service names (adjust based on your systemd service names)
BACKEND_SERVICE="craigslist-backend"
CELERY_WORKER_SERVICE="craigslist-celery"
CELERY_BEAT_SERVICE="craigslist-celery-beat"

###############################################################################
# Helper Functions
###############################################################################

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠ $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗ $1${NC}" | tee -a "$LOG_FILE"
}

# Rollback function
rollback() {
    log_error "Deployment failed! Rolling back to previous version..."

    if [ -d "$BACKUP_DIR/backend_${TIMESTAMP}" ]; then
        log "Restoring backend code from backup..."
        rm -rf "$BACKEND_DIR"
        cp -r "$BACKUP_DIR/backend_${TIMESTAMP}" "$BACKEND_DIR"

        log "Restarting services..."
        sudo systemctl restart "$BACKEND_SERVICE"
        sudo systemctl restart "$CELERY_WORKER_SERVICE"
        sudo systemctl restart "$CELERY_BEAT_SERVICE"

        log_success "Rollback completed"
    else
        log_error "Backup not found! Manual intervention required."
        exit 1
    fi

    exit 1
}

# Set up error trap
trap rollback ERR

###############################################################################
# Pre-Deployment Checks
###############################################################################

log "========================================="
log "Backend Deployment - Environment: $ENVIRONMENT"
log "========================================="

# Check if running as correct user
if [ "$ENVIRONMENT" = "production" ] && [ "$EUID" -eq 0 ]; then
    log_error "Do not run production deployments as root!"
    exit 1
fi

# Check if environment file exists
ENV_FILE="$PROJECT_ROOT/.env.$ENVIRONMENT"
if [ ! -f "$ENV_FILE" ]; then
    log_error "Environment file not found: $ENV_FILE"
    exit 1
fi

log "Using environment file: $ENV_FILE"

# Create necessary directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$PROJECT_ROOT/logs"

# Validate environment file
log "Validating environment configuration..."

# Check critical variables
source "$ENV_FILE"

if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-secret-key-here-change-in-production" ]; then
    log_error "SECRET_KEY not set or using default value!"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    log_error "DATABASE_URL not set!"
    exit 1
fi

if [ "$ENVIRONMENT" = "production" ]; then
    if [ "$DEBUG" = "true" ]; then
        log_error "DEBUG must be false in production!"
        exit 1
    fi

    if [[ "$ALLOWED_HOSTS" == *"localhost"* ]] || [[ "$ALLOWED_HOSTS" == *"*"* ]]; then
        log_error "ALLOWED_HOSTS contains localhost or wildcard in production!"
        exit 1
    fi
fi

log_success "Environment validation passed"

###############################################################################
# Backup Current Version
###############################################################################

log "Creating backup of current version..."

if [ -d "$BACKEND_DIR" ]; then
    cp -r "$BACKEND_DIR" "$BACKUP_DIR/backend_${TIMESTAMP}"
    log_success "Backup created at: $BACKUP_DIR/backend_${TIMESTAMP}"
else
    log_warning "No existing backend directory to backup"
fi

###############################################################################
# Pull Latest Code
###############################################################################

log "Pulling latest code from Git..."

cd "$PROJECT_ROOT"

# Check if git repository
if [ -d ".git" ]; then
    # Stash any local changes
    git stash

    # Pull latest code
    if [ "$ENVIRONMENT" = "production" ]; then
        git fetch origin
        git checkout main
        git pull origin main
    else
        git fetch origin
        git checkout develop || git checkout main
        git pull
    fi

    log_success "Code updated successfully"
else
    log_warning "Not a git repository - skipping git pull"
fi

###############################################################################
# Install Dependencies
###############################################################################

log "Installing Python dependencies..."

cd "$BACKEND_DIR"

# Activate virtual environment or create one
if [ ! -d "venv" ]; then
    log "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

log_success "Dependencies installed"

###############################################################################
# Run Database Migrations
###############################################################################

log "Running database migrations..."

# Set database URL from environment file
export DATABASE_URL

# Check current migration version
CURRENT_VERSION=$(alembic current 2>/dev/null || echo "none")
log "Current migration version: $CURRENT_VERSION"

# Run migrations
alembic upgrade head

NEW_VERSION=$(alembic current 2>/dev/null || echo "none")
log_success "Migrations completed. New version: $NEW_VERSION"

###############################################################################
# Run Tests (if in staging)
###############################################################################

if [ "$ENVIRONMENT" = "staging" ]; then
    log "Running backend tests..."

    # Run pytest
    if pytest tests/ -v --maxfail=5; then
        log_success "All tests passed"
    else
        log_warning "Some tests failed - continuing deployment (staging)"
    fi
fi

###############################################################################
# Deploy Static Files
###############################################################################

log "Collecting static files..."

# Create static directory if it doesn't exist
mkdir -p "$BACKEND_DIR/static"

# Copy any static assets
if [ -d "$BACKEND_DIR/app/static" ]; then
    cp -r "$BACKEND_DIR/app/static/"* "$BACKEND_DIR/static/"
    log_success "Static files collected"
fi

###############################################################################
# Update Environment File
###############################################################################

log "Updating environment configuration..."

# Backup current .env
if [ -f "$BACKEND_DIR/.env" ]; then
    cp "$BACKEND_DIR/.env" "$BACKEND_DIR/.env.backup"
fi

# Copy environment-specific .env file
cp "$ENV_FILE" "$BACKEND_DIR/.env"

log_success "Environment configuration updated"

###############################################################################
# Restart Services
###############################################################################

log "Restarting backend services..."

# Stop services gracefully
if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    log "Stopping backend service..."
    sudo systemctl stop "$BACKEND_SERVICE"
fi

if systemctl is-active --quiet "$CELERY_WORKER_SERVICE"; then
    log "Stopping Celery worker..."
    sudo systemctl stop "$CELERY_WORKER_SERVICE"
fi

if systemctl is-active --quiet "$CELERY_BEAT_SERVICE"; then
    log "Stopping Celery beat..."
    sudo systemctl stop "$CELERY_BEAT_SERVICE"
fi

# Wait for services to stop
sleep 3

# Start services
log "Starting backend service..."
sudo systemctl start "$BACKEND_SERVICE"

log "Starting Celery worker..."
sudo systemctl start "$CELERY_WORKER_SERVICE"

log "Starting Celery beat..."
sudo systemctl start "$CELERY_BEAT_SERVICE"

# Wait for services to start
sleep 5

# Check service status
if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    log_success "Backend service started successfully"
else
    log_error "Backend service failed to start!"
    sudo systemctl status "$BACKEND_SERVICE"
    exit 1
fi

if systemctl is-active --quiet "$CELERY_WORKER_SERVICE"; then
    log_success "Celery worker started successfully"
else
    log_warning "Celery worker failed to start"
fi

if systemctl is-active --quiet "$CELERY_BEAT_SERVICE"; then
    log_success "Celery beat started successfully"
else
    log_warning "Celery beat failed to start"
fi

###############################################################################
# Health Checks
###############################################################################

log "Running health checks..."

# Get API URL from environment
if [ "$ENVIRONMENT" = "production" ]; then
    API_URL="https://api.yourdomain.com"
else
    API_URL="http://localhost:8000"
fi

# Wait for API to be ready
RETRY_COUNT=0
MAX_RETRIES=30

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -f "$API_URL/health" > /dev/null 2>&1; then
        log_success "Health check passed"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        log "Waiting for API to be ready... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 2
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "Health check failed after $MAX_RETRIES attempts"
    exit 1
fi

# Detailed health check
HEALTH_RESPONSE=$(curl -s "$API_URL/health")
log "Health check response: $HEALTH_RESPONSE"

# Check if all services are healthy
if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
    log_success "All services healthy"
else
    log_warning "Some services may be degraded - check health response"
fi

###############################################################################
# Post-Deployment Verification
###############################################################################

log "Running post-deployment verification..."

# Check API version
API_VERSION=$(curl -s "$API_URL/" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
log "API Version: $API_VERSION"

# Check database connection
if echo "$HEALTH_RESPONSE" | grep -q '"database".*"healthy"'; then
    log_success "Database connection verified"
else
    log_error "Database connection failed!"
    exit 1
fi

# Check Redis connection
if echo "$HEALTH_RESPONSE" | grep -q '"redis".*"healthy"'; then
    log_success "Redis connection verified"
else
    log_warning "Redis connection failed or not configured"
fi

###############################################################################
# Cleanup Old Backups
###############################################################################

log "Cleaning up old backups..."

# Keep only last 10 backups
cd "$BACKUP_DIR"
ls -t | grep "backend_" | tail -n +11 | xargs -r rm -rf

log_success "Old backups cleaned up"

###############################################################################
# Deployment Summary
###############################################################################

log "========================================="
log_success "Backend deployment completed successfully!"
log "========================================="
log "Environment: $ENVIRONMENT"
log "API Version: $API_VERSION"
log "Timestamp: $TIMESTAMP"
log "Log file: $LOG_FILE"
log "Backup: $BACKUP_DIR/backend_${TIMESTAMP}"
log "========================================="

# Send deployment notification (optional)
if [ -n "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"✓ Backend deployed to $ENVIRONMENT - Version: $API_VERSION\"}"
fi

# Disable error trap
trap - ERR

exit 0
