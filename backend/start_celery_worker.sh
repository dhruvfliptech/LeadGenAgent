#!/bin/bash

###############################################################################
# Celery Worker Startup Script for FlipTech Pro
#
# This script starts Celery workers for background task processing.
# You can customize the number of workers, queues, and concurrency settings.
#
# Usage:
#   ./start_celery_worker.sh [queue_name]
#
# Examples:
#   ./start_celery_worker.sh              # Start default worker (all queues)
#   ./start_celery_worker.sh email        # Start worker for email queue only
#   ./start_celery_worker.sh scraper      # Start worker for scraper queue only
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
CONCURRENCY="${CELERY_CONCURRENCY:-4}"

# Parse queue argument
QUEUE="${1:-default,email,scraper,ai,demo}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting Celery Worker for FlipTech Pro${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Project Dir:  ${PROJECT_DIR}"
echo -e "  Queue(s):     ${QUEUE}"
echo -e "  Concurrency:  ${CONCURRENCY}"
echo -e "  Log Level:    ${LOG_LEVEL}"
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
    echo -e "${RED}Celery requires Redis as a message broker.${NC}"
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

# Start Celery worker
echo -e "${GREEN}Starting Celery worker...${NC}"
echo ""

# Set PYTHONPATH to include the backend directory
export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}"

# Start worker
celery -A ${CELERY_APP} worker \
    --queues="${QUEUE}" \
    --concurrency="${CONCURRENCY}" \
    --loglevel="${LOG_LEVEL}" \
    --autoscale=10,3 \
    --max-tasks-per-child=1000 \
    --task-events \
    --without-gossip \
    --without-mingle \
    --without-heartbeat \
    -n "worker-${QUEUE}@%h"

# Note: The script will block here while the worker runs
# Use Ctrl+C to stop the worker

echo ""
echo -e "${YELLOW}Celery worker stopped.${NC}"
