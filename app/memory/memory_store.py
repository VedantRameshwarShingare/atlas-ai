"""Storage abstractions for the Atlas AI memory subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.memory.memory_types import MemoryRecord


class MemoryStore(ABC):
    """Interface for persistent memory storage without implementation details."""

    @abstractmethod
    async def load(self, *, user_id: str, category: str | None = None, key: str | None = None, limit: int = 50) -> list[MemoryRecord]:
        """Load memory entries matching the supplied filters."""

    @abstractmethod
    async def save(self, record: MemoryRecord) -> MemoryRecord:
        """Persist a memory record."""

    @abstractmethod
    async def update(self, record_id: str, *, values: dict[str, Any]) -> MemoryRecord:
        """Update a persisted memory record."""

    @abstractmethod
    async def delete(self, record_id: str) -> None:
        """Delete a persisted memory record."""

    @abstractmethod
    async def search(self, *, user_id: str, query: str, limit: int = 10) -> list[MemoryRecord]:
        """Search persisted memory entries by text query."""
