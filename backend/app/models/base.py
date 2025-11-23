"""
Shared Base for all SQLAlchemy models.

This module provides a single declarative_base instance that all models
must use to avoid circular import issues and ensure proper model registry.
"""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
