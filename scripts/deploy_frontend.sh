#!/bin/bash

###############################################################################
# Frontend Deployment Script
# Deploys the React frontend to production/staging environments
#
# Usage: ./scripts/deploy_frontend.sh [environment]
# Example: ./scripts/deploy_frontend.sh production
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
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKUP_DIR="$PROJECT_ROOT/backups"
DEPLOY_DIR="/var/www/craigslist-leads"  # Adjust based on your setup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$PROJECT_ROOT/logs/frontend_deployment_${ENVIRONMENT}_${TIMESTAMP}.log"

# Service name (if using PM2 or systemd)
FRONTEND_SERVICE="craigslist-frontend"

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

    if [ -d "$BACKUP_DIR/frontend_${TIMESTAMP}" ]; then
        log "Restoring frontend from backup..."

        if [ -d "$DEPLOY_DIR" ]; then
            rm -rf "$DEPLOY_DIR"
            cp -r "$BACKUP_DIR/frontend_${TIMESTAMP}" "$DEPLOY_DIR"
        fi

        if [ -d "$FRONTEND_DIR/dist" ]; then
            rm -rf "$FRONTEND_DIR/dist"
            cp -r "$BACKUP_DIR/frontend_dist_${TIMESTAMP}" "$FRONTEND_DIR/dist"
        fi

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
log "Frontend Deployment - Environment: $ENVIRONMENT"
log "========================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    log_error "Node.js is not installed!"
    exit 1
fi

log "Node.js version: $(node --version)"
log "npm version: $(npm --version)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    log_error "npm is not installed!"
    exit 1
fi

# Create necessary directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$DEPLOY_DIR"

###############################################################################
# Backup Current Version
###############################################################################

log "Creating backup of current version..."

if [ -d "$DEPLOY_DIR" ]; then
    cp -r "$DEPLOY_DIR" "$BACKUP_DIR/frontend_${TIMESTAMP}"
    log_success "Deployment backup created"
fi

if [ -d "$FRONTEND_DIR/dist" ]; then
    cp -r "$FRONTEND_DIR/dist" "$BACKUP_DIR/frontend_dist_${TIMESTAMP}"
    log_success "Build backup created"
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

log "Installing npm dependencies..."

cd "$FRONTEND_DIR"

# Clean install for production
if [ "$ENVIRONMENT" = "production" ]; then
    log "Running clean install..."
    rm -rf node_modules package-lock.json
    npm ci
else
    npm install
fi

log_success "Dependencies installed"

###############################################################################
# Set Environment Variables
###############################################################################

log "Setting environment variables for build..."

# Set environment-specific variables
if [ "$ENVIRONMENT" = "production" ]; then
    export VITE_API_URL="https://api.yourdomain.com"
    export VITE_WS_URL="wss://api.yourdomain.com"
    export NODE_ENV="production"
else
    export VITE_API_URL="http://localhost:8000"
    export VITE_WS_URL="ws://localhost:8000"
    export NODE_ENV="development"
fi

log "VITE_API_URL: $VITE_API_URL"
log "VITE_WS_URL: $VITE_WS_URL"

# Create .env file for Vite
cat > "$FRONTEND_DIR/.env.$ENVIRONMENT" <<EOF
VITE_API_URL=$VITE_API_URL
VITE_WS_URL=$VITE_WS_URL
NODE_ENV=$NODE_ENV
EOF

# Use the environment-specific .env file
cp "$FRONTEND_DIR/.env.$ENVIRONMENT" "$FRONTEND_DIR/.env"

###############################################################################
# Run Linting
###############################################################################

if [ "$ENVIRONMENT" = "production" ]; then
    log "Running ESLint..."

    if npm run lint; then
        log_success "Linting passed"
    else
        log_warning "Linting found issues - continuing deployment"
    fi
fi

###############################################################################
# Type Checking
###############################################################################

if [ "$ENVIRONMENT" = "production" ]; then
    log "Running TypeScript type checking..."

    if npm run type-check; then
        log_success "Type checking passed"
    else
        log_error "Type checking failed!"
        exit 1
    fi
fi

###############################################################################
# Build Production Bundle
###############################################################################

log "Building production bundle..."

# Increase Node.js memory limit for large builds
export NODE_OPTIONS="--max-old-space-size=4096"

# Run production build
npm run build

# Verify build output
if [ ! -d "$FRONTEND_DIR/dist" ]; then
    log_error "Build failed - dist directory not created!"
    exit 1
fi

# Check if index.html exists
if [ ! -f "$FRONTEND_DIR/dist/index.html" ]; then
    log_error "Build failed - index.html not found!"
    exit 1
fi

log_success "Build completed successfully"

# Get build size
BUILD_SIZE=$(du -sh "$FRONTEND_DIR/dist" | cut -f1)
log "Build size: $BUILD_SIZE"

###############################################################################
# Optimize Build
###############################################################################

log "Optimizing build assets..."

# Compress assets (if not already compressed by Vite)
cd "$FRONTEND_DIR/dist"

# Find and count assets
TOTAL_FILES=$(find . -type f | wc -l)
log "Total files in build: $TOTAL_FILES"

# Create gzip versions of large files (for Nginx gzip_static)
if command -v gzip &> /dev/null; then
    find . -type f \( -name "*.js" -o -name "*.css" -o -name "*.html" \) -exec gzip -k -9 {} \;
    log_success "Created gzipped versions of assets"
fi

###############################################################################
# Deploy to Web Server
###############################################################################

log "Deploying to web server..."

# Copy build to deployment directory
rsync -av --delete "$FRONTEND_DIR/dist/" "$DEPLOY_DIR/"

# Set correct permissions
if [ "$ENVIRONMENT" = "production" ]; then
    sudo chown -R www-data:www-data "$DEPLOY_DIR"
    sudo chmod -R 755 "$DEPLOY_DIR"
fi

log_success "Files deployed to $DEPLOY_DIR"

###############################################################################
# Update Nginx Configuration (if needed)
###############################################################################

if [ "$ENVIRONMENT" = "production" ]; then
    log "Checking Nginx configuration..."

    # Test Nginx config
    if sudo nginx -t; then
        log_success "Nginx configuration valid"

        # Reload Nginx
        log "Reloading Nginx..."
        sudo systemctl reload nginx
        log_success "Nginx reloaded"
    else
        log_error "Nginx configuration test failed!"
        exit 1
    fi
fi

###############################################################################
# Restart Frontend Service (if using PM2 or systemd)
###############################################################################

# If serving with Node.js server (e.g., using Vite preview)
if systemctl is-active --quiet "$FRONTEND_SERVICE" 2>/dev/null; then
    log "Restarting frontend service..."
    sudo systemctl restart "$FRONTEND_SERVICE"

    if systemctl is-active --quiet "$FRONTEND_SERVICE"; then
        log_success "Frontend service restarted"
    else
        log_error "Frontend service failed to restart!"
        exit 1
    fi
fi

# If using PM2
if command -v pm2 &> /dev/null; then
    if pm2 list | grep -q "$FRONTEND_SERVICE"; then
        log "Restarting PM2 process..."
        pm2 restart "$FRONTEND_SERVICE"
        log_success "PM2 process restarted"
    fi
fi

###############################################################################
# Clear CDN Cache (if using Cloudflare, CloudFront, etc.)
###############################################################################

if [ "$ENVIRONMENT" = "production" ]; then
    log "Clearing CDN cache..."

    # Cloudflare cache purge (if configured)
    if [ -n "$CLOUDFLARE_ZONE_ID" ] && [ -n "$CLOUDFLARE_API_TOKEN" ]; then
        curl -X POST "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/purge_cache" \
            -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
            -H "Content-Type: application/json" \
            --data '{"purge_everything":true}'
        log_success "Cloudflare cache purged"
    fi

    # AWS CloudFront invalidation (if configured)
    if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ] && command -v aws &> /dev/null; then
        aws cloudfront create-invalidation \
            --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
            --paths "/*"
        log_success "CloudFront cache invalidated"
    fi
fi

###############################################################################
# Health Checks
###############################################################################

log "Running health checks..."

# Get frontend URL
if [ "$ENVIRONMENT" = "production" ]; then
    FRONTEND_URL="https://yourdomain.com"
else
    FRONTEND_URL="http://localhost:3000"
fi

# Wait for frontend to be ready
RETRY_COUNT=0
MAX_RETRIES=30

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -f -o /dev/null "$FRONTEND_URL"; then
        log_success "Frontend is accessible"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        log "Waiting for frontend to be ready... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 2
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "Frontend health check failed after $MAX_RETRIES attempts"
    exit 1
fi

# Check if index.html is being served
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL")
if [ "$HTTP_STATUS" = "200" ]; then
    log_success "Frontend health check passed (HTTP $HTTP_STATUS)"
else
    log_error "Frontend returned HTTP $HTTP_STATUS"
    exit 1
fi

# Verify API connectivity from frontend
log "Verifying API connectivity..."
API_RESPONSE=$(curl -s "$VITE_API_URL/health" || echo "failed")
if echo "$API_RESPONSE" | grep -q "healthy"; then
    log_success "API connectivity verified"
else
    log_warning "API may not be accessible from frontend"
fi

###############################################################################
# Performance Checks
###############################################################################

log "Running performance checks..."

# Check page load time
PAGE_LOAD_TIME=$(curl -o /dev/null -s -w '%{time_total}' "$FRONTEND_URL")
log "Page load time: ${PAGE_LOAD_TIME}s"

if (( $(echo "$PAGE_LOAD_TIME < 3.0" | bc -l) )); then
    log_success "Page load time is acceptable"
else
    log_warning "Page load time is slow: ${PAGE_LOAD_TIME}s"
fi

###############################################################################
# Cleanup Old Backups
###############################################################################

log "Cleaning up old backups..."

# Keep only last 10 backups
cd "$BACKUP_DIR"
ls -t | grep "frontend_" | tail -n +11 | xargs -r rm -rf

log_success "Old backups cleaned up"

###############################################################################
# Generate Deployment Report
###############################################################################

REPORT_FILE="$PROJECT_ROOT/logs/frontend_deployment_report_${TIMESTAMP}.txt"

cat > "$REPORT_FILE" <<EOF
========================================
Frontend Deployment Report
========================================
Environment: $ENVIRONMENT
Timestamp: $TIMESTAMP
Build Size: $BUILD_SIZE
Total Files: $TOTAL_FILES
Page Load Time: ${PAGE_LOAD_TIME}s
Node Version: $(node --version)
npm Version: $(npm --version)

Deployment URL: $FRONTEND_URL
API URL: $VITE_API_URL
WebSocket URL: $VITE_WS_URL

Status: SUCCESS
========================================
EOF

log "Deployment report saved to: $REPORT_FILE"

###############################################################################
# Deployment Summary
###############################################################################

log "========================================="
log_success "Frontend deployment completed successfully!"
log "========================================="
log "Environment: $ENVIRONMENT"
log "URL: $FRONTEND_URL"
log "Build size: $BUILD_SIZE"
log "Page load: ${PAGE_LOAD_TIME}s"
log "Timestamp: $TIMESTAMP"
log "Log file: $LOG_FILE"
log "Backup: $BACKUP_DIR/frontend_${TIMESTAMP}"
log "========================================="

# Send deployment notification (optional)
if [ -n "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"✓ Frontend deployed to $ENVIRONMENT - Load time: ${PAGE_LOAD_TIME}s\"}"
fi

# Disable error trap
trap - ERR

exit 0
