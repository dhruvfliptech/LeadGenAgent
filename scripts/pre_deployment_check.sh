#!/bin/bash

###############################################################################
# Pre-Deployment Verification Script
# Validates that the system is ready for production deployment
#
# Usage: ./scripts/pre_deployment_check.sh [environment]
# Example: ./scripts/pre_deployment_check.sh production
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Environment
ENVIRONMENT=${1:-production}

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env.$ENVIRONMENT"

# Track results
ERRORS=0
WARNINGS=0
PASSED=0

###############################################################################
# Helper Functions
###############################################################################

log() {
    echo -e "${BLUE}[CHECK]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    PASSED=$((PASSED + 1))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ERRORS=$((ERRORS + 1))
}

check_command() {
    if command -v "$1" &> /dev/null; then
        log_pass "$1 is installed"
    else
        log_fail "$1 is not installed"
    fi
}

check_service() {
    if systemctl is-active --quiet "$1" 2>/dev/null; then
        log_pass "$1 service is running"
    else
        log_warn "$1 service is not running"
    fi
}

###############################################################################
# Start Checks
###############################################################################

echo "========================================"
echo "Pre-Deployment Verification"
echo "Environment: $ENVIRONMENT"
echo "========================================"
echo

###############################################################################
# 1. System Requirements
###############################################################################

log "Checking system requirements..."

# Check OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    log_pass "Operating System: $PRETTY_NAME"
else
    log_warn "Could not determine OS version"
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
    log_pass "Python version: $PYTHON_VERSION"
else
    log_fail "Python 3.11+ required (found: $PYTHON_VERSION)"
fi

# Check Node.js version
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    NODE_MAJOR=$(echo $NODE_VERSION | sed 's/v//' | cut -d. -f1)

    if [ "$NODE_MAJOR" -ge 18 ]; then
        log_pass "Node.js version: $NODE_VERSION"
    else
        log_fail "Node.js 18+ required (found: $NODE_VERSION)"
    fi
else
    log_fail "Node.js is not installed"
fi

# Check disk space
DISK_AVAIL=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$DISK_AVAIL" -ge 50 ]; then
    log_pass "Disk space available: ${DISK_AVAIL}GB"
elif [ "$DISK_AVAIL" -ge 20 ]; then
    log_warn "Disk space: ${DISK_AVAIL}GB (recommend 50GB+)"
else
    log_fail "Insufficient disk space: ${DISK_AVAIL}GB (need 50GB+)"
fi

# Check memory
if command -v free &> /dev/null; then
    MEMORY_GB=$(free -g | awk 'NR==2 {print $2}')
    if [ "$MEMORY_GB" -ge 4 ]; then
        log_pass "Memory: ${MEMORY_GB}GB"
    elif [ "$MEMORY_GB" -ge 2 ]; then
        log_warn "Memory: ${MEMORY_GB}GB (recommend 4GB+)"
    else
        log_fail "Insufficient memory: ${MEMORY_GB}GB (need 4GB+)"
    fi
fi

echo

###############################################################################
# 2. Required Commands
###############################################################################

log "Checking required commands..."

check_command "git"
check_command "python3"
check_command "pip3"
check_command "node"
check_command "npm"
check_command "psql"
check_command "redis-cli"
check_command "nginx"
check_command "systemctl"
check_command "curl"

echo

###############################################################################
# 3. Database Checks
###############################################################################

log "Checking PostgreSQL..."

# Check PostgreSQL is running
if systemctl is-active --quiet postgresql 2>/dev/null; then
    log_pass "PostgreSQL service is running"

    # Check PostgreSQL version
    PG_VERSION=$(psql --version | awk '{print $3}' | cut -d. -f1)
    if [ "$PG_VERSION" -ge 14 ]; then
        log_pass "PostgreSQL version: $PG_VERSION"
    else
        log_fail "PostgreSQL 14+ required (found: $PG_VERSION)"
    fi
else
    log_fail "PostgreSQL service is not running"
fi

# Check if database exists (if env file exists)
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"

    if [ -n "$DATABASE_URL" ]; then
        DB_NAME=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')

        if psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
            log_pass "Database '$DB_NAME' exists"

            # Check pgvector extension
            if psql -U postgres -d "$DB_NAME" -c "SELECT * FROM pg_extension WHERE extname = 'vector';" 2>/dev/null | grep -q "vector"; then
                log_pass "pgvector extension is installed"
            else
                log_fail "pgvector extension is not installed"
            fi
        else
            log_warn "Database '$DB_NAME' does not exist yet"
        fi
    fi
fi

echo

###############################################################################
# 4. Redis Checks
###############################################################################

log "Checking Redis..."

if systemctl is-active --quiet redis 2>/dev/null || systemctl is-active --quiet redis-server 2>/dev/null; then
    log_pass "Redis service is running"

    # Check Redis version
    if command -v redis-cli &> /dev/null; then
        REDIS_VERSION=$(redis-cli --version | awk '{print $2}' | cut -d. -f1)
        if [ "$REDIS_VERSION" -ge 6 ]; then
            log_pass "Redis version: $REDIS_VERSION"
        else
            log_warn "Redis 6+ recommended (found: $REDIS_VERSION)"
        fi

        # Test Redis connection
        if redis-cli ping &> /dev/null; then
            log_pass "Redis connection test successful"
        else
            log_fail "Cannot connect to Redis"
        fi
    fi
else
    log_fail "Redis service is not running"
fi

echo

###############################################################################
# 5. Environment File Checks
###############################################################################

log "Checking environment configuration..."

if [ -f "$ENV_FILE" ]; then
    log_pass "Environment file exists: $ENV_FILE"

    source "$ENV_FILE"

    # Check critical variables
    if [ -n "$SECRET_KEY" ] && [ "$SECRET_KEY" != "your-secret-key-here-change-in-production" ] && [ "$SECRET_KEY" != "CHANGE_ME_TO_SECURE_RANDOM_VALUE" ]; then
        log_pass "SECRET_KEY is set"
    else
        log_fail "SECRET_KEY not set or using default value"
    fi

    if [ "$ENVIRONMENT" = "$ENVIRONMENT" ]; then
        log_pass "ENVIRONMENT is set to: $ENVIRONMENT"
    else
        log_fail "ENVIRONMENT variable mismatch"
    fi

    if [ "$DEBUG" = "false" ] && [ "$ENVIRONMENT" = "production" ]; then
        log_pass "DEBUG is disabled for production"
    elif [ "$ENVIRONMENT" = "production" ]; then
        log_fail "DEBUG must be false in production"
    fi

    if [ -n "$DATABASE_URL" ]; then
        log_pass "DATABASE_URL is set"
    else
        log_fail "DATABASE_URL is not set"
    fi

    if [ -n "$REDIS_URL" ]; then
        log_pass "REDIS_URL is set"
    else
        log_fail "REDIS_URL is not set"
    fi

    # Check CORS
    if [[ "$ALLOWED_HOSTS" != *"*"* ]] && [[ "$ALLOWED_HOSTS" != *"localhost"* ]] && [ "$ENVIRONMENT" = "production" ]; then
        log_pass "ALLOWED_HOSTS is properly configured"
    elif [ "$ENVIRONMENT" = "production" ]; then
        log_fail "ALLOWED_HOSTS contains wildcards or localhost in production"
    fi

    # Check AI provider
    if [ -n "$OPENAI_API_KEY" ] || [ -n "$ANTHROPIC_API_KEY" ] || [ -n "$OPENROUTER_API_KEY" ]; then
        log_pass "AI provider API key is configured"
    else
        log_warn "No AI provider API key configured"
    fi

    # Check email configuration
    if [ -n "$SMTP_HOST" ] && [ -n "$SMTP_USERNAME" ]; then
        log_pass "Email (SMTP) is configured"
    elif [ -n "$SENDGRID_API_KEY" ] || [ -n "$MAILGUN_API_KEY" ] || [ -n "$RESEND_API_KEY" ]; then
        log_pass "Email API provider is configured"
    else
        log_warn "No email provider configured"
    fi

else
    log_fail "Environment file not found: $ENV_FILE"
fi

echo

###############################################################################
# 6. SSL Certificate Checks (Production Only)
###############################################################################

if [ "$ENVIRONMENT" = "production" ]; then
    log "Checking SSL certificates..."

    if [ -d "/etc/letsencrypt/live" ]; then
        CERT_DIRS=$(ls -d /etc/letsencrypt/live/*/ 2>/dev/null | wc -l)
        if [ "$CERT_DIRS" -gt 0 ]; then
            log_pass "SSL certificates found"

            # Check certificate expiration
            for cert_dir in /etc/letsencrypt/live/*/; do
                DOMAIN=$(basename "$cert_dir")
                if [ -f "${cert_dir}cert.pem" ]; then
                    EXPIRY=$(openssl x509 -enddate -noout -in "${cert_dir}cert.pem" | cut -d= -f2)
                    EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$EXPIRY" +%s)
                    CURRENT_EPOCH=$(date +%s)
                    DAYS_LEFT=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))

                    if [ $DAYS_LEFT -gt 30 ]; then
                        log_pass "SSL for $DOMAIN: ${DAYS_LEFT} days remaining"
                    elif [ $DAYS_LEFT -gt 7 ]; then
                        log_warn "SSL for $DOMAIN: ${DAYS_LEFT} days remaining (renew soon)"
                    else
                        log_fail "SSL for $DOMAIN: ${DAYS_LEFT} days remaining (URGENT)"
                    fi
                fi
            done
        else
            log_warn "No SSL certificates found"
        fi
    else
        log_warn "Let's Encrypt directory not found"
    fi

    echo
fi

###############################################################################
# 7. Nginx Configuration
###############################################################################

log "Checking Nginx configuration..."

if command -v nginx &> /dev/null; then
    if nginx -t &> /dev/null; then
        log_pass "Nginx configuration is valid"
    else
        log_fail "Nginx configuration has errors"
    fi

    if [ -f "/etc/nginx/sites-enabled/craigslist-leads.conf" ] || [ -f "/etc/nginx/sites-enabled/craigslist-leads" ]; then
        log_pass "Craigslist Leads site is enabled in Nginx"
    else
        log_warn "Craigslist Leads site not enabled in Nginx"
    fi
else
    log_fail "Nginx is not installed"
fi

echo

###############################################################################
# 8. Application Files
###############################################################################

log "Checking application files..."

if [ -d "$PROJECT_ROOT/backend" ]; then
    log_pass "Backend directory exists"

    # Check requirements.txt
    if [ -f "$PROJECT_ROOT/backend/requirements.txt" ]; then
        log_pass "requirements.txt exists"
    else
        log_fail "requirements.txt not found"
    fi

    # Check alembic
    if [ -f "$PROJECT_ROOT/backend/alembic.ini" ]; then
        log_pass "alembic.ini exists"
    else
        log_warn "alembic.ini not found"
    fi

    # Check virtual environment
    if [ -d "$PROJECT_ROOT/backend/venv" ]; then
        log_pass "Virtual environment exists"
    else
        log_warn "Virtual environment not found"
    fi
else
    log_fail "Backend directory not found"
fi

if [ -d "$PROJECT_ROOT/frontend" ]; then
    log_pass "Frontend directory exists"

    # Check package.json
    if [ -f "$PROJECT_ROOT/frontend/package.json" ]; then
        log_pass "package.json exists"
    else
        log_fail "package.json not found"
    fi

    # Check node_modules
    if [ -d "$PROJECT_ROOT/frontend/node_modules" ]; then
        log_pass "node_modules directory exists"
    else
        log_warn "node_modules not installed"
    fi
else
    log_fail "Frontend directory not found"
fi

echo

###############################################################################
# 9. Deployment Scripts
###############################################################################

log "Checking deployment scripts..."

if [ -x "$PROJECT_ROOT/scripts/deploy_backend.sh" ]; then
    log_pass "deploy_backend.sh is executable"
else
    log_warn "deploy_backend.sh not executable or not found"
fi

if [ -x "$PROJECT_ROOT/scripts/deploy_frontend.sh" ]; then
    log_pass "deploy_frontend.sh is executable"
else
    log_warn "deploy_frontend.sh not executable or not found"
fi

if [ -x "$PROJECT_ROOT/scripts/health_check.sh" ]; then
    log_pass "health_check.sh is executable"
else
    log_warn "health_check.sh not executable or not found"
fi

if [ -x "$PROJECT_ROOT/scripts/rollback.sh" ]; then
    log_pass "rollback.sh is executable"
else
    log_warn "rollback.sh not executable or not found"
fi

echo

###############################################################################
# 10. Firewall & Ports
###############################################################################

log "Checking network configuration..."

# Check if firewall is enabled
if command -v ufw &> /dev/null; then
    if ufw status | grep -q "Status: active"; then
        log_pass "Firewall (UFW) is enabled"

        # Check required ports
        if ufw status | grep -q "80"; then
            log_pass "Port 80 (HTTP) is allowed"
        else
            log_warn "Port 80 (HTTP) not allowed"
        fi

        if ufw status | grep -q "443"; then
            log_pass "Port 443 (HTTPS) is allowed"
        else
            log_warn "Port 443 (HTTPS) not allowed"
        fi
    else
        log_warn "Firewall (UFW) is not enabled"
    fi
fi

# Check if ports are in use
if netstat -tuln 2>/dev/null | grep -q ":80 "; then
    log_pass "Port 80 is in use (likely Nginx)"
else
    log_warn "Port 80 is not in use"
fi

if netstat -tuln 2>/dev/null | grep -q ":443 "; then
    log_pass "Port 443 is in use (likely Nginx)"
else
    log_warn "Port 443 is not in use"
fi

echo

###############################################################################
# Summary
###############################################################################

echo "========================================"
echo "Verification Summary"
echo "========================================"
echo -e "${GREEN}Passed:${NC}   $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failures:${NC} $ERRORS"
echo "========================================"

if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}✓ System is ready for deployment!${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ System is ready but has warnings. Review and fix if possible.${NC}"
        exit 0
    fi
else
    echo -e "${RED}✗ System is NOT ready for deployment. Fix errors before proceeding.${NC}"
    exit 1
fi
