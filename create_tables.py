"""
Create all database tables directly from SQLAlchemy models.
This bypasses broken Alembic migrations for dev environment.
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env
backend_path = Path(__file__).parent / "backend"
env_path = backend_path / ".env"
load_dotenv(env_path)

# Add backend to path
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine
from app.models.base import Base
from app.core.config import settings

# Import all models so they're registered with Base.metadata
from app.models import *

def create_all_tables():
    """Create all tables defined in models."""
    # Use sync engine for table creation
    DATABASE_URL = settings.DATABASE_URL.replace('+asyncpg', '')
    engine = create_engine(DATABASE_URL, echo=True)

    print("Creating all tables from models...")
    print(f"Database URL: {DATABASE_URL.replace('postgres:', 'postgres:PASSWORD@')}")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("\n✅ All tables created successfully!")

    # List all created tables
    print("\nCreated tables:")
    for table_name in sorted(Base.metadata.tables.keys()):
        print(f"  - {table_name}")

if __name__ == "__main__":
    create_all_tables()
