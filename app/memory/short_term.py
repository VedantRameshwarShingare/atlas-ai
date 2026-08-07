"""Short-term memory support for active conversation state."""

from __future__ import annotations

from app.memory.memory_types import MemoryCategory, MemoryRecord


class ShortTermMemory:
    """Store transient conversation and session context."""

    def __init__(self) -> None:
        self._records: list[MemoryRecord] = []

    async def load(self, *, user_id: str, session_id: str | None = None, limit: int = 20) -> list[MemoryRecord]:
        """Load recent short-term memory entries."""
        records = [record for record in self._records if record.user_id == user_id and record.category == MemoryCategory.SHORT_TERM]
        if session_id is not None:
            records = [record for record in records if record.metadata.get("session_id") == session_id]
        return records[-limit:]

    async def save(self, *, user_id: str, key: str, value: str, session_id: str | None = None, metadata: dict | None = None) -> MemoryRecord:
        """Persist a short-term memory entry."""
        record = MemoryRecord(user_id=user_id, category=MemoryCategory.SHORT_TERM, key=key, value=value, metadata={**(metadata or {}), **({"session_id": session_id} if session_id else {})})
        self._records.append(record)
        return record

    async def update(self, record_id: str, *, value: str) -> MemoryRecord:
        """Update an existing short-term memory entry."""
        for record in self._records:
            if record.id == record_id:
                record.value = value
                record.updated_at = record.updated_at
                return record
        raise KeyError(record_id)

    async def delete(self, record_id: str) -> None:
        """Delete a short-term memory entry."""
        self._records = [record for record in self._records if record.id != record_id]

    async def search(self, *, user_id: str, query: str, limit: int = 10) -> list[MemoryRecord]:
        """Search short-term memory entries by query text."""
        matches = [record for record in self._records if record.user_id == user_id and query.lower() in str(record.value).lower()]
        return matches[-limit:]
