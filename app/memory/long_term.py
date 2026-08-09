"""Long-term memory support for durable user preferences and facts."""

from __future__ import annotations

from app.memory.memory_types import MemoryCategory, MemoryRecord


class LongTermMemory:
    """Store durable facts, preferences, and user-specific context."""

    def __init__(self) -> None:
        self._records: list[MemoryRecord] = []

    async def load(self, *, user_id: str, key: str | None = None, limit: int = 50) -> list[MemoryRecord]:
        """Load long-term memory entries."""
        records = [
            record
            for record in self._records
            if record.user_id == user_id and record.category == MemoryCategory.LONG_TERM
        ]
        if key is not None:
            records = [record for record in records if record.key == key]
        return records[-limit:]

    async def save(self, *, user_id: str, key: str, value: object, metadata: dict | None = None) -> MemoryRecord:
        """Persist a long-term memory entry."""
        record = MemoryRecord(
            user_id=user_id, category=MemoryCategory.LONG_TERM, key=key, value=value, metadata=metadata or {}
        )
        self._records.append(record)
        return record

    async def update(self, record_id: str, *, value: object) -> MemoryRecord:
        """Update an existing long-term memory entry."""
        for record in self._records:
            if record.id == record_id:
                record.value = value
                return record
        raise KeyError(record_id)

    async def delete(self, record_id: str) -> None:
        """Delete a long-term memory entry."""
        self._records = [record for record in self._records if record.id != record_id]

    async def search(self, *, user_id: str, query: str, limit: int = 10) -> list[MemoryRecord]:
        """Search long-term memory entries by query text."""
        matches = [
            record
            for record in self._records
            if record.user_id == user_id and query.lower() in str(record.value).lower()
        ]
        return matches[-limit:]
