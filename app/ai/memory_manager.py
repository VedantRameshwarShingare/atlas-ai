"""Memory management interface for AI orchestration."""

from __future__ import annotations

from typing import Any


class MemoryManager:
    """Interface for loading, storing, updating, and forgetting memory entries."""

    async def load(self, *, user_id: str | None = None, key: str | None = None) -> list[dict[str, Any]]:
        """Load memory entries for the current context."""
        return []

    async def store(self, *, user_id: str | None = None, key: str, value: Any) -> dict[str, Any]:
        """Store a new memory entry."""
        return {"key": key, "value": value}

    async def update(self, *, user_id: str | None = None, key: str, value: Any) -> dict[str, Any]:
        """Update an existing memory entry."""
        return {"key": key, "value": value}

    async def forget(self, *, user_id: str | None = None, key: str) -> bool:
        """Remove a memory entry."""
        return True
