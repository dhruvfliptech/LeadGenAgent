"""
FastAPI dependencies for database sessions and authentication.
"""

# Import get_db from core.database where it's already defined
from app.core.database import get_db

__all__ = ["get_db"]
