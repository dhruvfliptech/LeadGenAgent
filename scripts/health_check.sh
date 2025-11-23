#!/bin/bash

###############################################################################
# Health Check Script
# Comprehensive post-deployment verification
#
# Usage: ./scripts/health_check.sh [environment]
# Example: ./scripts/health_check.sh production
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default environment
ENVIRONMENT=${1:-production}

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$PROJECT_ROOT/logs/health_check_${ENVIRONMENT}_${TIMESTAMP}.txt"

# URLs based on environment
if [ "$ENVIRONMENT" = "production" ]; then
    API_URL="https://api.yourdomain.com"
    FRONTEND_URL="https://yourdomain.com"
else
    API_URL="http://localhost:8000"
    FRONTEND_URL="http://localhost:3000"
fi

###############################################################################
# Helper Functions
###############################################################################

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$REPORT_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓ $1${NC}" | tee -a "$REPORT_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠ $1${NC}" | tee -a "$REPORT_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗ $1${NC}" | tee -a "$REPORT_FILE"
}

# Track failures
FAILURES=0
WARNINGS=0

###############################################################################
# Start Health Check
###############################################################################

log "========================================="
log "Health Check - Environment: $ENVIRONMENT"
log "========================================="

mkdir -p "$PROJECT_ROOT/logs"

###############################################################################
# 1. Backend API Health
###############################################################################

log "Checking Backend API..."

# Basic connectivity
if curl -s -f "$API_URL/health" > /dev/null; then
    log_success "API is reachable"
else
    log_error "API is not reachable at $API_URL"
    FAILURES=$((FAILURES + 1))
fi

# Detailed health check
HEALTH_RESPONSE=$(curl -s "$API_URL/health" || echo '{"status":"error"}')

# Parse health status
API_STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

if [ "$API_STATUS" = "healthy" ]; then
    log_success "API status: healthy"
else
    log_error "API status: $API_STATUS"
    FAILURES=$((FAILURES + 1))
fi

# Check database connection
DB_STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"database".*"status":"[^"]*"' | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

if [ "$DB_STATUS" = "healthy" ]; then
    log_success "Database: healthy"
else
    log_error "Database: $DB_STATUS"
    FAILURES=$((FAILURES + 1))
fi

# Check Redis connection
REDIS_STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"redis".*"status":"[^"]*"' | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

if [ "$REDIS_STATUS" = "healthy" ]; then
    log_success "Redis: healthy"
elif [ -z "$REDIS_STATUS" ]; then
    log_warning "Redis: not configured"
    WARNINGS=$((WARNINGS + 1))
else
    log_warning "Redis: $REDIS_STATUS"
    WARNINGS=$((WARNINGS + 1))
fi

# Get API version
API_VERSION=$(curl -s "$API_URL/" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
log "API Version: $API_VERSION"

###############################################################################
# 2. API Endpoint Tests
###############################################################################

log "Testing critical API endpoints..."

# Array of endpoints to test
declare -a ENDPOINTS=(
    "/api/v1/leads"
    "/api/v1/scraper/status"
    "/api/v1/templates"
    "/system/info"
)

for endpoint in "${ENDPOINTS[@]}"; do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL$endpoint")

    if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "401" ]; then
        log_success "Endpoint $endpoint: HTTP $HTTP_STATUS"
    else
        log_error "Endpoint $endpoint: HTTP $HTTP_STATUS"
        FAILURES=$((FAILURES + 1))
    fi
done

###############################################################################
# 3. API Performance
###############################################################################

log "Testing API performance..."

# Response time test
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' "$API_URL/health")
log "API response time: ${RESPONSE_TIME}s"

if (( $(echo "$RESPONSE_TIME < 1.0" | bc -l) )); then
    log_success "API response time is good"
elif (( $(echo "$RESPONSE_TIME < 3.0" | bc -l) )); then
    log_warning "API response time is acceptable but could be improved"
    WARNINGS=$((WARNINGS + 1))
else
    log_error "API response time is too slow: ${RESPONSE_TIME}s"
    FAILURES=$((FAILURES + 1))
fi

###############################################################################
# 4. Frontend Health
###############################################################################

log "Checking Frontend..."

# Basic connectivity
if curl -s -f -o /dev/null "$FRONTEND_URL"; then
    log_success "Frontend is reachable"
else
    log_error "Frontend is not reachable at $FRONTEND_URL"
    FAILURES=$((FAILURES + 1))
fi

# Check HTTP status
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL")

if [ "$FRONTEND_STATUS" = "200" ]; then
    log_success "Frontend HTTP status: $FRONTEND_STATUS"
else
    log_error "Frontend HTTP status: $FRONTEND_STATUS"
    FAILURES=$((FAILURES + 1))
fi

# Check page load time
FRONTEND_LOAD_TIME=$(curl -o /dev/null -s -w '%{time_total}' "$FRONTEND_URL")
log "Frontend load time: ${FRONTEND_LOAD_TIME}s"

if (( $(echo "$FRONTEND_LOAD_TIME < 2.0" | bc -l) )); then
    log_success "Frontend load time is good"
elif (( $(echo "$FRONTEND_LOAD_TIME < 5.0" | bc -l) )); then
    log_warning "Frontend load time is acceptable"
    WARNINGS=$((WARNINGS + 1))
else
    log_error "Frontend load time is too slow"
    FAILURES=$((FAILURES + 1))
fi

###############################################################################
# 5. Service Status (Backend Services)
###############################################################################

log "Checking backend services..."

# Backend API service
BACKEND_SERVICE="craigslist-backend"
if systemctl is-active --quiet "$BACKEND_SERVICE" 2>/dev/null; then
    log_success "Backend service is running"

    # Get service uptime
    UPTIME=$(systemctl status "$BACKEND_SERVICE" | grep "Active:" | sed 's/.*Active: //')
    log "Service uptime: $UPTIME"
else
    log_error "Backend service is not running!"
    FAILURES=$((FAILURES + 1))
fi

# Celery worker
CELERY_WORKER="craigslist-celery"
if systemctl is-active --quiet "$CELERY_WORKER" 2>/dev/null; then
    log_success "Celery worker is running"
else
    log_warning "Celery worker is not running"
    WARNINGS=$((WARNINGS + 1))
fi

# Celery beat
CELERY_BEAT="craigslist-celery-beat"
if systemctl is-active --quiet "$CELERY_BEAT" 2>/dev/null; then
    log_success "Celery beat is running"
else
    log_warning "Celery beat is not running"
    WARNINGS=$((WARNINGS + 1))
fi

###############################################################################
# 6. Database Health
###############################################################################

log "Checking database health..."

# Load database URL from environment
if [ -f "$PROJECT_ROOT/.env.$ENVIRONMENT" ]; then
    source "$PROJECT_ROOT/.env.$ENVIRONMENT"
fi

if [ -n "$DATABASE_URL" ]; then
    # Extract database details
    DB_HOST=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    DB_NAME=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')

    # Test database connection
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" > /dev/null 2>&1; then
        log_success "Database server is ready"

        # Count total connections
        TOTAL_CONNECTIONS=$(psql "$DATABASE_URL" -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null || echo "N/A")
        log "Database connections: $TOTAL_CONNECTIONS"

        # Check database size
        DB_SIZE=$(psql "$DATABASE_URL" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null || echo "N/A")
        log "Database size: $DB_SIZE"
    else
        log_error "Database server is not responding"
        FAILURES=$((FAILURES + 1))
    fi
else
    log_warning "DATABASE_URL not configured"
    WARNINGS=$((WARNINGS + 1))
fi

###############################################################################
# 7. Redis Health
###############################################################################

log "Checking Redis health..."

if [ -n "$REDIS_URL" ]; then
    if redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; then
        log_success "Redis is responding"

        # Get Redis info
        REDIS_MEMORY=$(redis-cli -u "$REDIS_URL" info memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
        log "Redis memory usage: $REDIS_MEMORY"

        REDIS_KEYS=$(redis-cli -u "$REDIS_URL" dbsize | cut -d: -f2 | tr -d '\r')
        log "Redis keys: $REDIS_KEYS"
    else
        log_warning "Redis is not responding"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    log_warning "Redis URL not configured"
    WARNINGS=$((WARNINGS + 1))
fi

###############################################################################
# 8. SSL/TLS Certificate (Production Only)
###############################################################################

if [ "$ENVIRONMENT" = "production" ]; then
    log "Checking SSL certificate..."

    # Extract domain from URL
    DOMAIN=$(echo "$API_URL" | sed -n 's/https:\/\/\([^/]*\).*/\1/p')

    if [ -n "$DOMAIN" ]; then
        # Check certificate expiration
        CERT_EXPIRY=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -dates | grep "notAfter" | cut -d= -f2)

        log "SSL certificate expires: $CERT_EXPIRY"

        # Calculate days until expiry
        EXPIRY_EPOCH=$(date -d "$CERT_EXPIRY" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$CERT_EXPIRY" +%s)
        CURRENT_EPOCH=$(date +%s)
        DAYS_UNTIL_EXPIRY=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))

        if [ $DAYS_UNTIL_EXPIRY -gt 30 ]; then
            log_success "SSL certificate valid for $DAYS_UNTIL_EXPIRY days"
        elif [ $DAYS_UNTIL_EXPIRY -gt 7 ]; then
            log_warning "SSL certificate expires in $DAYS_UNTIL_EXPIRY days - renew soon!"
            WARNINGS=$((WARNINGS + 1))
        else
            log_error "SSL certificate expires in $DAYS_UNTIL_EXPIRY days - URGENT!"
            FAILURES=$((FAILURES + 1))
        fi
    fi
fi

###############################################################################
# 9. Disk Space
###############################################################################

log "Checking disk space..."

DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')

log "Disk usage: $DISK_USAGE%"

if [ "$DISK_USAGE" -lt 70 ]; then
    log_success "Disk usage is healthy"
elif [ "$DISK_USAGE" -lt 85 ]; then
    log_warning "Disk usage is approaching limit"
    WARNINGS=$((WARNINGS + 1))
else
    log_error "Disk usage is critically high!"
    FAILURES=$((FAILURES + 1))
fi

###############################################################################
# 10. Memory Usage
###############################################################################

log "Checking memory usage..."

if command -v free &> /dev/null; then
    MEMORY_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
    log "Memory usage: $MEMORY_USAGE%"

    if [ "$MEMORY_USAGE" -lt 70 ]; then
        log_success "Memory usage is healthy"
    elif [ "$MEMORY_USAGE" -lt 85 ]; then
        log_warning "Memory usage is approaching limit"
        WARNINGS=$((WARNINGS + 1))
    else
        log_error "Memory usage is critically high!"
        FAILURES=$((FAILURES + 1))
    fi
fi

###############################################################################
# 11. Log File Check
###############################################################################

log "Checking for recent errors in logs..."

LOG_DIR="$PROJECT_ROOT/logs"

if [ -d "$LOG_DIR" ]; then
    # Check for recent errors (last hour)
    ERROR_COUNT=$(find "$LOG_DIR" -name "*.log" -mmin -60 -exec grep -c "ERROR" {} \; 2>/dev/null | awk '{s+=$1} END {print s}')

    if [ -z "$ERROR_COUNT" ]; then
        ERROR_COUNT=0
    fi

    log "Recent errors in logs: $ERROR_COUNT"

    if [ "$ERROR_COUNT" -eq 0 ]; then
        log_success "No recent errors found"
    elif [ "$ERROR_COUNT" -lt 10 ]; then
        log_warning "Some errors found in logs"
        WARNINGS=$((WARNINGS + 1))
    else
        log_error "High number of errors in logs!"
        FAILURES=$((FAILURES + 1))
    fi
else
    log_warning "Log directory not found"
    WARNINGS=$((WARNINGS + 1))
fi

###############################################################################
# Summary
###############################################################################

log "========================================="

if [ $FAILURES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    log_success "All health checks passed!"
    EXIT_CODE=0
elif [ $FAILURES -eq 0 ]; then
    log_warning "Health checks passed with $WARNINGS warning(s)"
    EXIT_CODE=0
else
    log_error "Health checks failed! $FAILURES failure(s), $WARNINGS warning(s)"
    EXIT_CODE=1
fi

log "========================================="
log "Summary:"
log "  Failures: $FAILURES"
log "  Warnings: $WARNINGS"
log "  Report: $REPORT_FILE"
log "========================================="

# Send alert if failures detected
if [ $FAILURES -gt 0 ] && [ -n "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"⚠ Health check failed on $ENVIRONMENT - $FAILURES failures, $WARNINGS warnings\"}"
fi

exit $EXIT_CODE
