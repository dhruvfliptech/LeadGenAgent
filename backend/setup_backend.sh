#!/bin/bash

# CraigLeads Pro - Backend Setup Script
# This script sets up the backend environment

set -e  # Exit on error

echo "======================================"
echo "CraigLeads Pro - Backend Setup"
echo "======================================"
echo ""

# Step 1: Check Python version
echo "[1/7] Checking Python installation..."
python3 --version || { echo "Error: Python 3 not found. Please install Python 3.11+"; exit 1; }
echo "✓ Python found"
echo ""

# Step 2: Create virtual environment
echo "[2/7] Creating Python virtual environment..."
if [ -d "venv" ]; then
    echo "⚠ Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi
echo ""

# Step 3: Activate virtual environment
echo "[3/7] Activating virtual environment..."
source venv/bin/activate || { echo "Error: Failed to activate virtual environment"; exit 1; }
echo "✓ Virtual environment activated"
echo ""

# Step 4: Upgrade pip
echo "[4/7] Upgrading pip..."
pip install --upgrade pip
echo "✓ pip upgraded"
echo ""

# Step 5: Install dependencies
echo "[5/7] Installing Python dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Step 6: Install Playwright browsers
echo "[6/7] Installing Playwright browsers (Chromium for scraping)..."
playwright install chromium
echo "✓ Playwright browsers installed"
echo ""

# Step 7: Create .env file
echo "[7/7] Setting up environment configuration..."
if [ -f ".env" ]; then
    echo "⚠ .env file already exists. Skipping..."
else
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠ IMPORTANT: You need to configure the .env file with your settings:"
    echo "   - DATABASE_URL (PostgreSQL connection string)"
    echo "   - REDIS_URL (Redis connection string)"
    echo "   - SECRET_KEY (generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))')"
    echo "   - API keys for external services (OpenAI, Anthropic, etc.)"
fi
echo ""

echo "======================================"
echo "Backend Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Configure your .env file with actual values"
echo "2. Start PostgreSQL and Redis"
echo "3. Run: python create_tables_simple.py  (to create database tables)"
echo "4. Run: uvicorn app.main:app --reload  (to start the server)"
echo ""
echo "For production deployment, see: QUICK_FIX_GUIDE.md"
echo ""
