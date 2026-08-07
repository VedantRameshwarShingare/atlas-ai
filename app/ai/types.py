"""Typed request and response models for the AI orchestration layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.ai.enums import IntentType, ResponseType, ToolType


@dataclass(slots=True)
class ChatRequest:
    """Represents an incoming chat request."""

    user_id: UUID | None = None
    text: str = ""
    conversation_id: UUID | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ChatResponse:
    """Represents a normalized AI response."""

    content: str
    response_type: ResponseType = ResponseType.MARKDOWN
    sources: list[str] = field(default_factory=list)
    tool_citations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ToolCall:
    """Represents a tool invocation request."""

    name: str
    tool_type: ToolType
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ToolResult:
    """Represents the outcome of a tool execution."""

    tool_name: str
    tool_type: ToolType
    success: bool
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class IntentResult:
    """Represents the detected intent for a user request."""

    intent: IntentType
    confidence: float
    required_tools: list[ToolType] = field(default_factory=list)


@dataclass(slots=True)
class ConversationContext:
    """Represents a unified context object passed into the AI pipeline."""

    request: ChatRequest
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    memories: list[dict[str, Any]] = field(default_factory=list)
    workspace_context: dict[str, Any] = field(default_factory=dict)
    documents: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
