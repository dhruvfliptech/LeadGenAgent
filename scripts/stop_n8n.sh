#!/bin/bash

###############################################################################
# n8n Stop Script for CraigLeads Pro
# This script stops the n8n workflow automation platform
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Stopping n8n Services${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cd "$PROJECT_ROOT"

# Stop n8n services
echo -e "${BLUE}Stopping n8n containers...${NC}"
docker-compose -f docker-compose.n8n.yml down

echo -e "${GREEN}✓${NC} n8n services stopped"

# Option to remove volumes (data)
read -p "Do you want to remove data volumes? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Removing volumes...${NC}"
    docker-compose -f docker-compose.n8n.yml down -v
    echo -e "${GREEN}✓${NC} Volumes removed"
else
    echo -e "${BLUE}Data volumes preserved${NC}"
fi

echo ""
echo -e "${GREEN}n8n has been stopped${NC}"
