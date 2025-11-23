#!/bin/bash

###############################################################################
# Flower Monitoring Tool Startup Script for FlipTech Pro
#
# This script starts Flower, a web-based monitoring tool for Celery.
# Access it at http://localhost:5555
#
# Usage:
#   ./start_flower.sh
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
FLOWER_PORT="${FLOWER_PORT:-5555}"
FLOWER_ADDRESS="${FLOWER_ADDRESS:-0.0.0.0}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting Flower for FlipTech Pro${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Project Dir:  ${PROJECT_DIR}"
echo -e "  Address:      ${FLOWER_ADDRESS}:${FLOWER_PORT}"
echo -e "  URL:          http://localhost:${FLOWER_PORT}"
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
    echo -e "${RED}Flower requires Redis to monitor Celery.${NC}"
    echo ""
    echo -e "${YELLOW}To start Redis:${NC}"
    echo -e "  brew services start redis    (macOS)"
    echo -e "  sudo systemctl start redis   (Linux)"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ Redis is running${NC}"
echo ""

# Check if flower is installed
if ! command -v celery &> /dev/null; then
    echo -e "${RED}ERROR: Celery/Flower not installed!${NC}"
    echo -e "${RED}Install with: pip install flower${NC}"
    exit 1
fi

# Start Flower
echo -e "${GREEN}Starting Flower monitoring tool...${NC}"
echo ""
echo -e "${YELLOW}Access Flower at: ${GREEN}http://localhost:${FLOWER_PORT}${NC}"
echo ""

# Set PYTHONPATH to include the backend directory
export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}"

# Start flower
celery -A ${CELERY_APP} flower \
    --address="${FLOWER_ADDRESS}" \
    --port="${FLOWER_PORT}" \
    --max_tasks=10000 \
    --persistent=True \
    --db="${PROJECT_DIR}/flower.db"

# Note: The script will block here while flower runs
# Use Ctrl+C to stop flower

echo ""
echo -e "${YELLOW}Flower stopped.${NC}"
