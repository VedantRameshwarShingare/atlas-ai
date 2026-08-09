"""Memory management interface for AI orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class _MemoryEntry:
    """A durable, user-scoped memory entry managed by the AI layer."""

    key: str
    value: Any
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class MemoryManager:
    """Interface for loading, storing, updating, and forgetting memory entries."""

    async def load(
        self, *, user_id: str | None = None, key: str | None = None, query: str = "", limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Load memory entries for the current context."""
        if user_id is None:
            return []
        entries = self._entries.get(user_id, [])
        if key is not None:
            entries = [entry for entry in entries if entry.key == key]
        terms = {term for term in query.lower().split() if len(term) > 2}
        ranked = sorted(
            entries,
            key=lambda entry: (
                -sum(term in f"{entry.key} {entry.value}".lower() for term in terms),
                -entry.created_at.timestamp(),
            ),
        )
        return [{"key": entry.key, "value": entry.value} for entry in ranked[: limit or self._limit]]

    async def store(self, *, user_id: str | None = None, key: str, value: Any) -> dict[str, Any]:
        """Store a new memory entry."""
        if user_id is None:
            return {"key": key, "value": value}
        entries = self._entries.setdefault(user_id, [])
        entries[:] = [entry for entry in entries if entry.key != key]
        entries.append(_MemoryEntry(key=key, value=value))
        return {"key": key, "value": value}

    async def update(self, *, user_id: str | None = None, key: str, value: Any) -> dict[str, Any]:
        """Update an existing memory entry."""
        return await self.store(user_id=user_id, key=key, value=value)

    async def forget(self, *, user_id: str | None = None, key: str) -> bool:
        """Remove a memory entry."""
        if user_id is None:
            return False
        entries = self._entries.get(user_id, [])
        before = len(entries)
        entries[:] = [entry for entry in entries if entry.key != key]
        return len(entries) != before

    def __init__(self, *, limit: int = 10) -> None:
        self._limit = limit
        self._entries: dict[str, list[_MemoryEntry]] = {}
