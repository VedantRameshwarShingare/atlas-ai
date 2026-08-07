"""Conversation memory utilities for selection and compression."""

from __future__ import annotations

from app.memory.memory_types import MemoryCategory, MemoryRecord


class ConversationMemory:
    """Support loading, summarizing, compressing, and selecting conversation history."""

    def __init__(self) -> None:
        self._records: list[MemoryRecord] = []

    async def load_conversation(self, *, user_id: str, limit: int = 20) -> list[MemoryRecord]:
        """Load recent conversation entries."""
        records = [record for record in self._records if record.user_id == user_id and record.category == MemoryCategory.CONVERSATION]
        return records[-limit:]

    async def summarize_conversation(self, *, user_id: str) -> str:
        """Summarize the selected conversation memory."""
        records = await self.load_conversation(user_id=user_id)
        if not records:
            return "No recent conversation context."
        return " | ".join(str(record.value) for record in records)

    async def compress_context(self, *, user_id: str, limit: int = 10) -> list[MemoryRecord]:
        """Compress stored conversation context to a smaller list."""
        return (await self.load_conversation(user_id=user_id, limit=limit))

    async def select_relevant_history(self, *, user_id: str, query: str, limit: int = 5) -> list[MemoryRecord]:
        """Select conversation records relevant to the query."""
        records = await self.load_conversation(user_id=user_id)
        return [record for record in records if query.lower() in str(record.value).lower()][-limit:]

    async def add_record(self, *, user_id: str, key: str, value: str) -> MemoryRecord:
        """Add a new conversation memory record."""
        record = MemoryRecord(user_id=user_id, category=MemoryCategory.CONVERSATION, key=key, value=value)
        self._records.append(record)
        return record
