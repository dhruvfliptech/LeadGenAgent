#!/bin/bash

###############################################################################
# Rollback Script
# Emergency rollback for backend, frontend, or database
#
# Usage: ./scripts/rollback.sh [component] [options]
# Examples:
#   ./scripts/rollback.sh backend --last-good
#   ./scripts/rollback.sh frontend --version v1.9.0
#   ./scripts/rollback.sh database --revision abc123
#   ./scripts/rollback.sh --all --emergency
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKUP_DIR="$PROJECT_ROOT/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$PROJECT_ROOT/logs/rollback_${TIMESTAMP}.log"

# Component to rollback
COMPONENT=${1:-all}
shift || true

# Default options
EMERGENCY=false
LAST_GOOD=false
VERSION=""
REVISION=""

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

confirm() {
    if [ "$EMERGENCY" = true ]; then
        return 0  # Skip confirmation in emergency mode
    fi

    read -p "$1 (yes/no): " response
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

###############################################################################
# Parse Options
###############################################################################

while [[ $# -gt 0 ]]; do
    case $1 in
        --emergency)
            EMERGENCY=true
            shift
            ;;
        --last-good)
            LAST_GOOD=true
            shift
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --revision)
            REVISION="$2"
            shift 2
            ;;
        --all)
            COMPONENT="all"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

###############################################################################
# Show Warning
###############################################################################

log "========================================="
log "ROLLBACK OPERATION"
log "========================================="
log "Component: $COMPONENT"
log "Emergency Mode: $EMERGENCY"
log "Last Good: $LAST_GOOD"
[ -n "$VERSION" ] && log "Version: $VERSION"
[ -n "$REVISION" ] && log "Revision: $REVISION"
log "========================================="

if [ "$EMERGENCY" = false ]; then
    log_warning "This will rollback your application to a previous state!"
    log_warning "Make sure you understand the implications before proceeding."

    if ! confirm "Are you sure you want to continue?"; then
        log "Rollback cancelled by user"
        exit 0
    fi
fi

mkdir -p "$PROJECT_ROOT/logs"

###############################################################################
# Rollback Backend
###############################################################################

rollback_backend() {
    log "Rolling back backend..."

    # Find backup to restore
    BACKUP_TO_RESTORE=""

    if [ "$LAST_GOOD" = true ]; then
        # Find last successful deployment
        BACKUP_TO_RESTORE=$(ls -t "$BACKUP_DIR" | grep "backend_" | head -n 1)
    elif [ -n "$VERSION" ]; then
        # Find backup matching version
        # This assumes backup directory names include version or timestamp
        BACKUP_TO_RESTORE=$(ls -t "$BACKUP_DIR" | grep "backend_.*$VERSION" | head -n 1)
    else
        # Use most recent backup
        BACKUP_TO_RESTORE=$(ls -t "$BACKUP_DIR" | grep "backend_" | head -n 1)
    fi

    if [ -z "$BACKUP_TO_RESTORE" ]; then
        log_error "No backend backup found!"
        return 1
    fi

    log "Restoring from backup: $BACKUP_TO_RESTORE"

    # Stop backend services
    log "Stopping backend services..."
    sudo systemctl stop craigslist-backend || log_warning "Backend service not running"
    sudo systemctl stop craigslist-celery || log_warning "Celery worker not running"
    sudo systemctl stop craigslist-celery-beat || log_warning "Celery beat not running"

    # Create backup of current state (before rollback)
    if [ -d "$BACKEND_DIR" ]; then
        log "Creating backup of current state..."
        cp -r "$BACKEND_DIR" "$BACKUP_DIR/backend_before_rollback_${TIMESTAMP}"
    fi

    # Restore backend code
    log "Restoring backend code..."
    rm -rf "$BACKEND_DIR"
    cp -r "$BACKUP_DIR/$BACKUP_TO_RESTORE" "$BACKEND_DIR"

    # Restore virtual environment (if it exists in backup)
    if [ -d "$BACKUP_DIR/$BACKUP_TO_RESTORE/venv" ]; then
        log "Restoring virtual environment..."
    else
        log_warning "Virtual environment not in backup - recreating..."
        cd "$BACKEND_DIR"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    fi

    # Start services
    log "Starting backend services..."
    sudo systemctl start craigslist-backend
    sudo systemctl start craigslist-celery
    sudo systemctl start craigslist-celery-beat

    # Wait for services to start
    sleep 5

    # Verify services are running
    if systemctl is-active --quiet craigslist-backend; then
        log_success "Backend service started"
    else
        log_error "Backend service failed to start!"
        return 1
    fi

    log_success "Backend rollback completed"
}

###############################################################################
# Rollback Frontend
###############################################################################

rollback_frontend() {
    log "Rolling back frontend..."

    # Find backup to restore
    BACKUP_TO_RESTORE=""

    if [ "$LAST_GOOD" = true ]; then
        BACKUP_TO_RESTORE=$(ls -t "$BACKUP_DIR" | grep "frontend_" | head -n 1)
    elif [ -n "$VERSION" ]; then
        BACKUP_TO_RESTORE=$(ls -t "$BACKUP_DIR" | grep "frontend_.*$VERSION" | head -n 1)
    else
        BACKUP_TO_RESTORE=$(ls -t "$BACKUP_DIR" | grep "frontend_" | head -n 1)
    fi

    if [ -z "$BACKUP_TO_RESTORE" ]; then
        log_error "No frontend backup found!"
        return 1
    fi

    log "Restoring from backup: $BACKUP_TO_RESTORE"

    DEPLOY_DIR="/var/www/craigslist-leads"

    # Create backup of current state
    if [ -d "$DEPLOY_DIR" ]; then
        log "Creating backup of current state..."
        cp -r "$DEPLOY_DIR" "$BACKUP_DIR/frontend_before_rollback_${TIMESTAMP}"
    fi

    # Restore frontend
    log "Restoring frontend files..."
    rm -rf "$DEPLOY_DIR"
    cp -r "$BACKUP_DIR/$BACKUP_TO_RESTORE" "$DEPLOY_DIR"

    # Set permissions
    sudo chown -R www-data:www-data "$DEPLOY_DIR" 2>/dev/null || true
    sudo chmod -R 755 "$DEPLOY_DIR" 2>/dev/null || true

    # Reload Nginx
    log "Reloading Nginx..."
    sudo systemctl reload nginx

    log_success "Frontend rollback completed"
}

###############################################################################
# Rollback Database
###############################################################################

rollback_database() {
    log "Rolling back database..."

    # Load database URL
    if [ -f "$PROJECT_ROOT/.env.production" ]; then
        source "$PROJECT_ROOT/.env.production"
    fi

    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL not set!"
        return 1
    fi

    cd "$BACKEND_DIR"

    if [ -n "$REVISION" ]; then
        # Rollback to specific revision
        log "Rolling back to revision: $REVISION"

        if ! confirm "This will modify the database schema. Continue?"; then
            log "Database rollback cancelled"
            return 0
        fi

        # Create database backup before rollback
        log "Creating database backup..."
        BACKUP_FILE="$BACKUP_DIR/db_before_rollback_${TIMESTAMP}.dump"
        pg_dump "$DATABASE_URL" -F c -f "$BACKUP_FILE"
        log_success "Database backup created: $BACKUP_FILE"

        # Execute rollback
        log "Executing database rollback..."
        alembic downgrade "$REVISION"

        log_success "Database rolled back to revision: $REVISION"
    else
        # Rollback one migration
        log "Rolling back one migration..."

        if ! confirm "This will undo the last database migration. Continue?"; then
            log "Database rollback cancelled"
            return 0
        fi

        # Create database backup
        log "Creating database backup..."
        BACKUP_FILE="$BACKUP_DIR/db_before_rollback_${TIMESTAMP}.dump"
        pg_dump "$DATABASE_URL" -F c -f "$BACKUP_FILE"
        log_success "Database backup created: $BACKUP_FILE"

        # Rollback one migration
        log "Rolling back one migration..."
        alembic downgrade -1

        log_success "Database migration rolled back"
    fi

    # Verify current version
    CURRENT_VERSION=$(alembic current)
    log "Current database version: $CURRENT_VERSION"
}

###############################################################################
# Full Database Restore
###############################################################################

restore_database_from_backup() {
    log "Restoring database from backup..."

    # Find most recent backup
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/db_*.dump 2>/dev/null | head -n 1)

    if [ -z "$BACKUP_FILE" ]; then
        log_error "No database backup found!"
        return 1
    fi

    log "Restoring from: $BACKUP_FILE"

    if ! confirm "This will completely restore the database. ALL CURRENT DATA WILL BE LOST. Continue?"; then
        log "Database restore cancelled"
        return 0
    fi

    # Load database URL
    source "$PROJECT_ROOT/.env.production"

    # Drop and recreate database
    log_warning "Dropping current database..."

    DB_NAME=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')

    psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
    psql -h localhost -U postgres -c "CREATE DATABASE $DB_NAME;"

    # Restore from backup
    log "Restoring database..."
    pg_restore -h localhost -U postgres -d "$DB_NAME" "$BACKUP_FILE"

    log_success "Database restored from backup"
}

###############################################################################
# Execute Rollback
###############################################################################

case $COMPONENT in
    backend)
        rollback_backend
        ;;

    frontend)
        rollback_frontend
        ;;

    database)
        if [ "$EMERGENCY" = true ]; then
            restore_database_from_backup
        else
            rollback_database
        fi
        ;;

    all)
        log "Rolling back entire system..."

        if [ "$EMERGENCY" = true ]; then
            log_warning "EMERGENCY ROLLBACK - Restoring all components from backups"

            # Stop all services
            log "Stopping all services..."
            sudo systemctl stop craigslist-backend || true
            sudo systemctl stop craigslist-celery || true
            sudo systemctl stop craigslist-celery-beat || true

            # Rollback database first
            restore_database_from_backup

            # Rollback backend
            rollback_backend

            # Rollback frontend
            rollback_frontend

            log_success "Emergency rollback completed"
        else
            # Normal rollback (code only, not data)
            rollback_backend
            rollback_frontend

            log_success "System rollback completed"
        fi
        ;;

    *)
        log_error "Invalid component: $COMPONENT"
        log "Valid components: backend, frontend, database, all"
        exit 1
        ;;
esac

###############################################################################
# Post-Rollback Verification
###############################################################################

log "Running post-rollback verification..."

# Run health checks
if [ -f "$PROJECT_ROOT/scripts/health_check.sh" ]; then
    log "Running health checks..."
    "$PROJECT_ROOT/scripts/health_check.sh" production

    if [ $? -eq 0 ]; then
        log_success "Health checks passed"
    else
        log_error "Health checks failed - manual intervention may be required"
    fi
else
    log_warning "Health check script not found - skipping verification"
fi

###############################################################################
# Summary
###############################################################################

log "========================================="
log_success "Rollback completed successfully!"
log "========================================="
log "Component: $COMPONENT"
log "Timestamp: $TIMESTAMP"
log "Log file: $LOG_FILE"
log "========================================="

# Send notification
if [ -n "$SLACK_WEBHOOK_URL" ]; then
    curl -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"⚠ Rollback executed: $COMPONENT - Timestamp: $TIMESTAMP\"}"
fi

exit 0
