#!/bin/bash

#############################################################################
# CraigLeads Pro - Netlify Deployment Script
#
# Automates the deployment process to Netlify with pre-deployment checks
# and verification steps.
#
# Usage:
#   ./scripts/deploy-to-netlify.sh [OPTIONS]
#
# Options:
#   --prod              Deploy to production (default: draft)
#   --skip-checks       Skip pre-deployment checks
#   --skip-build        Skip local build test
#   --skip-tests        Skip test suite
#   --auto-confirm      Skip confirmation prompts
#
# Examples:
#   ./scripts/deploy-to-netlify.sh              # Draft deploy
#   ./scripts/deploy-to-netlify.sh --prod       # Production deploy
#   ./scripts/deploy-to-netlify.sh --prod --auto-confirm
#
#############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
DEPLOY_PROD=false
SKIP_CHECKS=false
SKIP_BUILD=false
SKIP_TESTS=false
AUTO_CONFIRM=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --prod)
      DEPLOY_PROD=true
      shift
      ;;
    --skip-checks)
      SKIP_CHECKS=true
      shift
      ;;
    --skip-build)
      SKIP_BUILD=true
      shift
      ;;
    --skip-tests)
      SKIP_TESTS=true
      shift
      ;;
    --auto-confirm)
      AUTO_CONFIRM=true
      shift
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}║         CraigLeads Pro - Netlify Deployment Script        ║${NC}"
echo -e "${BLUE}║                                                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print section headers
print_section() {
  echo ""
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}  $1${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
}

# Function to print success messages
print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

# Function to print warning messages
print_warning() {
  echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to print error messages
print_error() {
  echo -e "${RED}✗ $1${NC}"
}

# Function to print info messages
print_info() {
  echo -e "${BLUE}ℹ $1${NC}"
}

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Pre-deployment checks
if [ "$SKIP_CHECKS" = false ]; then
  print_section "Pre-Deployment Checks"

  # Check if we're in the right directory
  if [ ! -f "$PROJECT_ROOT/package.json" ] && [ ! -f "$FRONTEND_DIR/package.json" ]; then
    print_error "Cannot find package.json. Are you in the correct directory?"
    exit 1
  fi
  print_success "Project structure verified"

  # Check if Node.js is installed
  if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
  fi
  NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
  if [ "$NODE_VERSION" -lt 18 ]; then
    print_error "Node.js version 18 or higher is required. Current version: $(node -v)"
    exit 1
  fi
  print_success "Node.js $(node -v) detected"

  # Check if npm is installed
  if ! command_exists npm; then
    print_error "npm is not installed."
    exit 1
  fi
  print_success "npm $(npm -v) detected"

  # Check if Netlify CLI is installed
  if ! command_exists netlify; then
    print_warning "Netlify CLI is not installed."
    print_info "Installing Netlify CLI globally..."
    npm install -g netlify-cli
    if [ $? -eq 0 ]; then
      print_success "Netlify CLI installed"
    else
      print_error "Failed to install Netlify CLI"
      exit 1
    fi
  else
    print_success "Netlify CLI detected"
  fi

  # Check if Git is installed
  if ! command_exists git; then
    print_warning "Git is not installed. Version tracking will be limited."
  else
    print_success "Git $(git --version | cut -d' ' -f3) detected"
  fi

  # Check Git status
  if command_exists git && [ -d "$PROJECT_ROOT/.git" ]; then
    cd "$PROJECT_ROOT"

    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
      print_warning "You have uncommitted changes:"
      git status --short

      if [ "$AUTO_CONFIRM" = false ]; then
        read -p "Continue with deployment? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
          print_error "Deployment cancelled"
          exit 1
        fi
      fi
    else
      print_success "Git working directory is clean"
    fi

    # Show current branch
    CURRENT_BRANCH=$(git branch --show-current)
    print_info "Current branch: $CURRENT_BRANCH"
  fi

  # Check if frontend directory exists
  if [ ! -d "$FRONTEND_DIR" ]; then
    print_error "Frontend directory not found: $FRONTEND_DIR"
    exit 1
  fi
  print_success "Frontend directory found"

  # Check if node_modules exists
  if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    print_warning "node_modules not found. Running npm install..."
    cd "$FRONTEND_DIR"
    npm install
    if [ $? -eq 0 ]; then
      print_success "Dependencies installed"
    else
      print_error "Failed to install dependencies"
      exit 1
    fi
  else
    print_success "Dependencies installed"
  fi

  # Check for required configuration files
  REQUIRED_FILES=(
    "$FRONTEND_DIR/package.json"
    "$FRONTEND_DIR/vite.config.ts"
    "$FRONTEND_DIR/netlify.toml"
    "$FRONTEND_DIR/public/_redirects"
  )

  for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
      print_error "Required file not found: $(basename $file)"
      exit 1
    fi
  done
  print_success "Required configuration files present"

  # Check for environment variables
  if [ ! -f "$FRONTEND_DIR/.env" ] && [ ! -f "$FRONTEND_DIR/.env.local" ]; then
    print_warning "No .env file found. Environment variables should be set in Netlify dashboard."
  fi

  print_success "All pre-deployment checks passed"
fi

# Run tests
if [ "$SKIP_TESTS" = false ]; then
  print_section "Running Tests"

  cd "$FRONTEND_DIR"

  # Check if test script exists
  if grep -q '"test"' package.json; then
    print_info "Running test suite..."
    npm test -- --passWithNoTests
    if [ $? -eq 0 ]; then
      print_success "All tests passed"
    else
      print_error "Tests failed"

      if [ "$AUTO_CONFIRM" = false ]; then
        read -p "Continue with deployment despite test failures? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
          print_error "Deployment cancelled"
          exit 1
        fi
      fi
    fi
  else
    print_info "No test script found. Skipping tests."
  fi
fi

# Local build test
if [ "$SKIP_BUILD" = false ]; then
  print_section "Testing Local Build"

  cd "$FRONTEND_DIR"

  print_info "Building production bundle..."
  npm run build

  if [ $? -eq 0 ]; then
    print_success "Build succeeded"

    # Check build size
    if [ -d "$FRONTEND_DIR/dist" ]; then
      BUILD_SIZE=$(du -sh "$FRONTEND_DIR/dist" | cut -f1)
      print_info "Build size: $BUILD_SIZE"

      # Warn if build is too large (> 10MB)
      BUILD_SIZE_BYTES=$(du -s "$FRONTEND_DIR/dist" | cut -f1)
      if [ "$BUILD_SIZE_BYTES" -gt 10240 ]; then
        print_warning "Build size is quite large ($BUILD_SIZE). Consider optimizing."
      fi
    fi
  else
    print_error "Build failed"
    exit 1
  fi
fi

# Deployment confirmation
print_section "Deployment Summary"

if [ "$DEPLOY_PROD" = true ]; then
  print_info "Deployment target: ${GREEN}PRODUCTION${NC}"
  print_warning "This will deploy to your live site!"
else
  print_info "Deployment target: ${YELLOW}DRAFT${NC}"
  print_info "A draft URL will be provided for preview"
fi

print_info "Frontend directory: $FRONTEND_DIR"
print_info "Build directory: $FRONTEND_DIR/dist"

if [ "$AUTO_CONFIRM" = false ]; then
  echo ""
  read -p "Proceed with deployment? (y/n) " -n 1 -r
  echo ""
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Deployment cancelled"
    exit 1
  fi
fi

# Deploy to Netlify
print_section "Deploying to Netlify"

cd "$FRONTEND_DIR"

# Check if site is linked
if [ ! -f ".netlify/state.json" ]; then
  print_warning "Site not linked to Netlify."
  print_info "Running netlify init..."
  netlify init
fi

# Deploy
print_info "Starting deployment..."

if [ "$DEPLOY_PROD" = true ]; then
  netlify deploy --prod --dir=dist
else
  netlify deploy --dir=dist
fi

DEPLOY_EXIT_CODE=$?

if [ $DEPLOY_EXIT_CODE -eq 0 ]; then
  print_section "Deployment Successful"

  print_success "Deployment completed successfully!"

  if [ "$DEPLOY_PROD" = true ]; then
    print_info "Your site is now live at your production URL"
    print_info "Run 'netlify open' to view in browser"
  else
    print_info "Draft deployment created"
    print_info "Check the output above for the draft URL"
  fi

  # Post-deployment checks
  print_info ""
  print_info "Post-Deployment Checklist:"
  echo "  [ ] Visit site and verify it loads correctly"
  echo "  [ ] Check that API connection is working"
  echo "  [ ] Test WebSocket connection"
  echo "  [ ] Verify all routes work (no 404s)"
  echo "  [ ] Check browser console for errors"
  echo "  [ ] Test on mobile devices"

  print_info ""
  print_info "Useful commands:"
  echo "  netlify open        - Open site in browser"
  echo "  netlify logs        - View deployment logs"
  echo "  netlify status      - Check site status"
  echo "  netlify env:list    - List environment variables"

else
  print_section "Deployment Failed"

  print_error "Deployment failed with exit code $DEPLOY_EXIT_CODE"
  print_info "Check the error messages above for details"
  print_info "Common issues:"
  echo "  - Build command failed"
  echo "  - Missing environment variables"
  echo "  - Authentication issues"
  echo "  - Network problems"

  exit $DEPLOY_EXIT_CODE
fi

print_section "Deployment Complete"

exit 0
