"""Unified memory engine coordinating short-term, long-term, workspace, and conversation memory."""

from __future__ import annotations

from typing import Any

from app.memory.conversation_memory import ConversationMemory
from app.memory.long_term import LongTermMemory
from app.memory.memory_store import MemoryStore
from app.memory.memory_types import MemoryContext, MemoryRecord
from app.memory.preferences import PreferencesMemory
from app.memory.profile import ProfileMemory
from app.memory.short_term import ShortTermMemory
from app.memory.workspace_memory import WorkspaceMemory


class MemoryEngine:
    """Coordinate memory subsystems without touching external services or routes."""

    def __init__(
        self,
        *,
        short_term_memory: ShortTermMemory | None = None,
        long_term_memory: LongTermMemory | None = None,
        profile_memory: ProfileMemory | None = None,
        preferences_memory: PreferencesMemory | None = None,
        workspace_memory: WorkspaceMemory | None = None,
        conversation_memory: ConversationMemory | None = None,
        memory_store: MemoryStore | None = None,
    ) -> None:
        self._short_term_memory = short_term_memory or ShortTermMemory()
        self._long_term_memory = long_term_memory or LongTermMemory()
        self._profile_memory = profile_memory or ProfileMemory()
        self._preferences_memory = preferences_memory or PreferencesMemory()
        self._workspace_memory = workspace_memory or WorkspaceMemory()
        self._conversation_memory = conversation_memory or ConversationMemory()
        self._memory_store = memory_store

    async def load_memory(self, *, user_id: str, session_id: str | None = None, limit: int = 50) -> MemoryContext:
        """Load memory context from the memory subsystems."""
        short_term = await self._short_term_memory.load(user_id=user_id, session_id=session_id, limit=limit)
        long_term = await self._long_term_memory.load(user_id=user_id, limit=limit)
        workspace = await self._workspace_memory.list_records(user_id=user_id)
        conversation = await self._conversation_memory.load_conversation(user_id=user_id, limit=limit)
        merged_context = " | ".join(str(record.value) for record in [*short_term, *long_term, *workspace, *conversation] if str(record.value))
        return MemoryContext(
            user_id=user_id,
            short_term=short_term,
            long_term=long_term,
            workspace=workspace,
            conversation=conversation,
            merged_context=merged_context,
            metadata={"session_id": session_id},
        )

    async def save_memory(self, *, user_id: str, category: str, key: str, value: Any, session_id: str | None = None, metadata: dict[str, Any] | None = None) -> MemoryRecord:
        """Save a memory entry into the appropriate store."""
        if category == "short_term":
            return await self._short_term_memory.save(user_id=user_id, key=key, value=str(value), session_id=session_id, metadata=metadata)
        if category == "long_term":
            return await self._long_term_memory.save(user_id=user_id, key=key, value=value, metadata=metadata)
        if category == "workspace":
            return await self._workspace_memory.add_record(user_id=user_id, key=key, value=str(value))
        if category == "conversation":
            return await self._conversation_memory.add_record(user_id=user_id, key=key, value=str(value))
        raise ValueError(f"Unsupported category: {category}")

    async def update_memory(self, *, category: str, record_id: str, value: Any) -> MemoryRecord:
        """Update a memory entry in the appropriate subsystem."""
        if category == "short_term":
            return await self._short_term_memory.update(record_id, value=str(value))
        if category == "long_term":
            return await self._long_term_memory.update(record_id, value=value)
        raise ValueError(f"Unsupported category: {category}")

    async def delete_memory(self, *, category: str, record_id: str) -> None:
        """Delete a memory entry from the appropriate subsystem."""
        if category == "short_term":
            await self._short_term_memory.delete(record_id)
            return
        if category == "long_term":
            await self._long_term_memory.delete(record_id)
            return
        raise ValueError(f"Unsupported category: {category}")

    async def search_memory(self, *, user_id: str, query: str, limit: int = 10) -> list[MemoryRecord]:
        """Search memory across supported subsystems."""
        results: list[MemoryRecord] = []
        results.extend(await self._short_term_memory.search(user_id=user_id, query=query, limit=limit))
        results.extend(await self._long_term_memory.search(user_id=user_id, query=query, limit=limit))
        return results[-limit:]

    async def merge_context(self, *, user_id: str, session_id: str | None = None, limit: int = 50) -> MemoryContext:
        """Merge memory context into a single context object."""
        return await self.load_memory(user_id=user_id, session_id=session_id, limit=limit)
