#!/bin/bash

###############################################################################
# Celery Beat Startup Script for FlipTech Pro
#
# This script starts Celery Beat scheduler for periodic tasks.
# Beat manages scheduled tasks defined in celery_app.py
#
# Usage:
#   ./start_celery_beat.sh
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CELERY_APP="celery_app:celery_app"
LOG_LEVEL="${CELERY_LOG_LEVEL:-info}"
SCHEDULE_FILE="${PROJECT_DIR}/celerybeat-schedule"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting Celery Beat for FlipTech Pro${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Project Dir:    ${PROJECT_DIR}"
echo -e "  Log Level:      ${LOG_LEVEL}"
echo -e "  Schedule File:  ${SCHEDULE_FILE}"
echo ""

# Change to project directory
cd "${PROJECT_DIR}"

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Warning: No virtual environment found. Make sure dependencies are installed.${NC}"
    echo -e "${YELLOW}Run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt${NC}"
    echo ""
fi

# Activate virtual environment if exists
if [ -d "venv" ]; then
    echo -e "${GREEN}Activating virtual environment (venv)...${NC}"
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo -e "${GREEN}Activating virtual environment (.venv)...${NC}"
    source .venv/bin/activate
fi

# Check if Redis is running
echo -e "${YELLOW}Checking Redis connection...${NC}"
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Redis is not running!${NC}"
    echo -e "${RED}Celery Beat requires Redis as a message broker.${NC}"
    echo ""
    echo -e "${YELLOW}To start Redis:${NC}"
    echo -e "  brew services start redis    (macOS)"
    echo -e "  sudo systemctl start redis   (Linux)"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ Redis is running${NC}"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Using default configuration.${NC}"
    echo ""
fi

# Remove old schedule file if it exists
if [ -f "${SCHEDULE_FILE}" ]; then
    echo -e "${YELLOW}Removing old schedule file...${NC}"
    rm -f "${SCHEDULE_FILE}"
fi

# Start Celery beat
echo -e "${GREEN}Starting Celery Beat scheduler...${NC}"
echo ""
echo -e "${YELLOW}Scheduled tasks:${NC}"
echo -e "  - Process scheduled campaigns (every minute)"
echo -e "  - Retry failed emails (every 15 minutes)"
echo -e "  - Update campaign metrics (every 5 minutes)"
echo -e "  - Cleanup old task results (every hour)"
echo -e "  - Monitor scraper jobs (every 10 minutes)"
echo -e "  - Cleanup old scraper data (daily at 3 AM)"
echo -e "  - Generate daily analytics (daily at 1 AM)"
echo ""

# Set PYTHONPATH to include the backend directory
export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}"

# Start beat
celery -A ${CELERY_APP} beat \
    --loglevel="${LOG_LEVEL}" \
    --schedule="${SCHEDULE_FILE}" \
    --pidfile="${PROJECT_DIR}/celerybeat.pid"

# Note: The script will block here while beat runs
# Use Ctrl+C to stop beat

echo ""
echo -e "${YELLOW}Celery Beat stopped.${NC}"

# Cleanup PID file
if [ -f "${PROJECT_DIR}/celerybeat.pid" ]; then
    rm -f "${PROJECT_DIR}/celerybeat.pid"
fi
