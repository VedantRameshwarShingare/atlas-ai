"""Generic repository implementation for database entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base


class BaseRepository[T: Base]:
    """Provide common CRUD operations for ORM models."""

    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self.session = session
        self.model = model

    async def create(self, obj: T) -> T:
        """Create and persist a new model instance."""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: T) -> T:
        """Update a persisted model instance."""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: T) -> None:
        """Delete a model instance."""
        await self.session.delete(obj)
        await self.session.commit()

    async def get(self, obj_id: UUID) -> T | None:
        """Retrieve a model instance by identifier."""
        return await self.session.get(self.model, obj_id)

    async def list(self, offset: int = 0, limit: int = 100) -> list[T]:
        """List model instances with pagination."""
        result = await self.session.execute(select(self.model).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def exists(self, obj_id: UUID) -> bool:
        """Check whether a model instance exists."""
        return await self.get(obj_id) is not None

    async def count(self) -> int:
        """Count all model instances."""
        result = await self.session.execute(select(self.model))
        return len(result.scalars().all())
