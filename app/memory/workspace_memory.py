"""Workspace-scoped memory abstractions."""

from __future__ import annotations

from app.memory.memory_types import MemoryCategory, MemoryRecord, WorkspaceMemoryState


class WorkspaceMemory:
    """Keep per-workspace context such as documents, summaries, and insights."""

    def __init__(self, state: WorkspaceMemoryState | None = None) -> None:
        self._state = state or WorkspaceMemoryState(workspace_id="default")
        self._records: list[MemoryRecord] = []

    async def load(self) -> WorkspaceMemoryState:
        """Return the current workspace state."""
        return self._state

    async def save(self, *, state: WorkspaceMemoryState) -> WorkspaceMemoryState:
        """Persist the workspace state."""
        self._state = state
        return self._state

    async def add_record(self, *, user_id: str, key: str, value: str) -> MemoryRecord:
        """Add a workspace memory record."""
        record = MemoryRecord(user_id=user_id, category=MemoryCategory.WORKSPACE, key=key, value=value)
        self._records.append(record)
        return record

    async def list_records(self, *, user_id: str) -> list[MemoryRecord]:
        """List workspace memory records for the given user."""
        return [record for record in self._records if record.user_id == user_id]
