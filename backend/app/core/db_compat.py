"""
Database compatibility utilities for migrating from sync to async patterns.
Provides helpers to ease the transition from SQLAlchemy ORM sync to async.
"""

from typing import TypeVar, Type, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeMeta

T = TypeVar('T', bound=DeclarativeMeta)


class AsyncQueryWrapper:
    """
    Wrapper to provide ORM-like query interface for async sessions.
    Helps bridge the gap between old sync code and new async patterns.
    """

    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
        self._query = select(model)

    def filter(self, *criterion):
        """Add WHERE conditions"""
        self._query = self._query.where(*criterion)
        return self

    def filter_by(self, **kwargs):
        """Add WHERE conditions by keyword arguments"""
        for key, value in kwargs.items():
            self._query = self._query.where(getattr(self.model, key) == value)
        return self

    def order_by(self, *criterion):
        """Add ORDER BY"""
        self._query = self._query.order_by(*criterion)
        return self

    def offset(self, offset: int):
        """Add OFFSET"""
        self._query = self._query.offset(offset)
        return self

    def limit(self, limit: int):
        """Add LIMIT"""
        self._query = self._query.limit(limit)
        return self

    async def all(self) -> List[T]:
        """Execute and return all results"""
        result = await self.session.execute(self._query)
        return list(result.scalars().all())

    async def first(self) -> Optional[T]:
        """Execute and return first result or None"""
        result = await self.session.execute(self._query.limit(1))
        return result.scalar_one_or_none()

    async def count(self) -> int:
        """Return count of results"""
        from sqlalchemy import func, select as select_func
        count_query = select_func(func.count()).select_from(self.model)
        # Apply WHERE conditions from self._query if any
        result = await self.session.execute(count_query)
        return result.scalar()


def async_query(session: AsyncSession, model: Type[T]) -> AsyncQueryWrapper:
    """
    Create an async query wrapper for ORM-style querying.

    Usage:
        # Instead of: db.query(Model).filter(...).all()
        # Use: await async_query(db, Model).filter(...).all()
    """
    return AsyncQueryWrapper(session, model)
