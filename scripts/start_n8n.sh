#!/bin/bash

###############################################################################
# n8n Startup Script for CraigLeads Pro
# This script starts the n8n workflow automation platform
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  CraigLeads Pro - n8n Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker is running"

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} docker-compose not found. Installing..."

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install docker-compose
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi

    echo -e "${GREEN}✓${NC} docker-compose installed"
fi

# Create necessary directories
echo ""
echo -e "${BLUE}Creating n8n directories...${NC}"

mkdir -p "$PROJECT_ROOT/n8n/workflows"
mkdir -p "$PROJECT_ROOT/n8n/custom-nodes"
mkdir -p "$PROJECT_ROOT/n8n/config"
mkdir -p "$PROJECT_ROOT/n8n/credentials"
mkdir -p "$PROJECT_ROOT/n8n/backups"

echo -e "${GREEN}✓${NC} Directories created"

# Check if .env.n8n exists
if [ ! -f "$PROJECT_ROOT/.env.n8n" ]; then
    echo -e "${YELLOW}⚠${NC} .env.n8n not found, using defaults"
    echo "You should create .env.n8n with your configuration"
fi

# Stop any existing n8n containers
echo ""
echo -e "${BLUE}Stopping existing n8n containers...${NC}"
cd "$PROJECT_ROOT"
docker-compose -f docker-compose.n8n.yml down --remove-orphans 2>/dev/null || true
echo -e "${GREEN}✓${NC} Cleaned up existing containers"

# Pull latest images
echo ""
echo -e "${BLUE}Pulling latest Docker images...${NC}"
docker-compose -f docker-compose.n8n.yml pull

# Start n8n
echo ""
echo -e "${BLUE}Starting n8n services...${NC}"
docker-compose -f docker-compose.n8n.yml up -d

# Wait for services to be healthy
echo ""
echo -e "${BLUE}Waiting for services to start...${NC}"
echo -n "PostgreSQL: "
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if docker-compose -f docker-compose.n8n.yml ps postgres 2>/dev/null | grep -q "healthy"; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    sleep 2
    counter=$((counter + 2))
    echo -n "."
done

if [ $counter -ge $timeout ]; then
    echo -e "${RED}✗${NC}"
    echo -e "${RED}Error: PostgreSQL failed to start${NC}"
    docker-compose -f docker-compose.n8n.yml logs postgres
    exit 1
fi

echo -n "Redis: "
counter=0
while [ $counter -lt $timeout ]; do
    if docker-compose -f docker-compose.n8n.yml ps redis 2>/dev/null | grep -q "healthy"; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    sleep 2
    counter=$((counter + 2))
    echo -n "."
done

if [ $counter -ge $timeout ]; then
    echo -e "${RED}✗${NC}"
    echo -e "${RED}Error: Redis failed to start${NC}"
    docker-compose -f docker-compose.n8n.yml logs redis
    exit 1
fi

echo -n "n8n: "
counter=0
while [ $counter -lt $timeout ]; do
    if curl -s http://localhost:5678/healthz > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    sleep 2
    counter=$((counter + 2))
    echo -n "."
done

if [ $counter -ge $timeout ]; then
    echo -e "${YELLOW}⚠${NC} n8n is taking longer than expected to start"
    echo "Check logs with: docker-compose -f docker-compose.n8n.yml logs n8n"
fi

# Display status
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  n8n is running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "  n8n UI:      ${GREEN}http://localhost:5678${NC}"
echo -e "  Webhook URL: ${GREEN}http://localhost:5678/webhook${NC}"
echo ""
echo -e "${BLUE}Default Credentials:${NC}"
echo -e "  Username: ${YELLOW}admin${NC}"
echo -e "  Password: ${YELLOW}changeme${NC}"
echo ""
echo -e "${RED}⚠ IMPORTANT: Change password after first login!${NC}"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo -e "  View logs:    ${YELLOW}docker-compose -f docker-compose.n8n.yml logs -f${NC}"
echo -e "  Stop n8n:     ${YELLOW}docker-compose -f docker-compose.n8n.yml down${NC}"
echo -e "  Restart n8n:  ${YELLOW}docker-compose -f docker-compose.n8n.yml restart n8n${NC}"
echo -e "  Database CLI: ${YELLOW}docker-compose -f docker-compose.n8n.yml exec postgres psql -U n8n${NC}"
echo ""

# Check if backend is running
if curl -s http://localhost:8000/api/v1/n8n-webhooks/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend webhook endpoints are accessible"
else
    echo -e "${YELLOW}⚠${NC} Backend is not running. Start it with: ./start_backend.sh"
fi

echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Open ${GREEN}http://localhost:5678${NC} in your browser"
echo -e "  2. Log in with default credentials"
echo -e "  3. Change your password in Settings"
echo -e "  4. Import workflow templates from ${YELLOW}n8n/workflows/${NC}"
echo -e "  5. Configure CraigLeads Pro API credentials"
echo ""
echo -e "${GREEN}Setup complete!${NC}"
