"""Repository for memory entities."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import Memory
from app.repositories.base_repository import BaseRepository


class MemoryRepository(BaseRepository[Memory]):
    """Repository for managing memory records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Memory)
