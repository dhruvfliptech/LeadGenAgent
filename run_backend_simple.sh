#!/bin/bash

# Simple backend runner without pandas for testing
export DATABASE_URL="postgresql://postgres:postgres@localhost:5433/craigslist_leads"
export REDIS_URL="redis://localhost:6380"
export ENVIRONMENT="development"
export SECRET_KEY="dev-secret-key-for-testing"
export DEBUG="true"

cd backend

# Install minimal deps using pip3 with user flag
pip3 install --user fastapi uvicorn sqlalchemy alembic asyncpg psycopg2-binary redis python-dotenv pydantic pydantic-settings

# Try to run migrations (might fail but that's ok for now)
python3 -m alembic upgrade head 2>/dev/null || echo "Migrations skipped"

# Start server
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000