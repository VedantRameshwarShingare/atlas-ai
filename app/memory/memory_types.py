"""Typed models for the Atlas AI memory subsystem."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class MemoryCategory(StrEnum):
    """Supported memory categories."""

    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    WORKSPACE = "workspace"
    CONVERSATION = "conversation"


class MemoryRecord(BaseModel):
    """A single memory entry."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    user_id: str
    category: MemoryCategory
    key: str
    value: Any
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MemoryContext(BaseModel):
    """Merged memory context for orchestrator consumption."""

    user_id: str
    short_term: list[MemoryRecord] = Field(default_factory=list)
    long_term: list[MemoryRecord] = Field(default_factory=list)
    workspace: list[MemoryRecord] = Field(default_factory=list)
    conversation: list[MemoryRecord] = Field(default_factory=list)
    merged_context: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class UserProfileState(BaseModel):
    """User profile fields stored in memory-only form."""

    timezone: str = "UTC"
    language: str = "en"
    writing_style: str = "concise"
    briefing_preferences: dict[str, Any] = Field(default_factory=dict)


class UserPreferencesState(BaseModel):
    """User notification and briefing preferences."""

    notification_preferences: dict[str, Any] = Field(default_factory=dict)
    briefing_time: str | None = None
    preferred_sources: list[str] = Field(default_factory=list)
    market_focus: list[str] = Field(default_factory=list)


class WorkspaceMemoryState(BaseModel):
    """Workspace-scoped memory state."""

    workspace_id: str
    uploaded_documents: list[str] = Field(default_factory=list)
    research_notes: list[str] = Field(default_factory=list)
    company: str | None = None
    generated_summaries: list[str] = Field(default_factory=list)
    conversation_history: list[str] = Field(default_factory=list)
    ai_insights: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
