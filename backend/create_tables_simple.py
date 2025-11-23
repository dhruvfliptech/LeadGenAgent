"""
Create all database tables directly from SQLAlchemy models.
This bypasses broken Alembic migrations for dev environment.
"""

from sqlalchemy import create_engine
from app.models import Base  # Base is defined in __init__.py
from app.core.config import settings

# Import all models so they're registered with Base.metadata
from app.models import *

def create_all_tables():
    """Create all tables defined in models."""
    # Use sync engine for table creation
    DATABASE_URL = str(settings.DATABASE_URL).replace('+asyncpg', '')
    engine = create_engine(DATABASE_URL, echo=True)

    print("Creating all tables from models...")
    print(f"Database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'localhost'}")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("\n✅ All tables created successfully!")

    # List all created tables
    print("\nCreated tables:")
    for table_name in sorted(Base.metadata.tables.keys()):
        print(f"  - {table_name}")

if __name__ == "__main__":
    create_all_tables()
