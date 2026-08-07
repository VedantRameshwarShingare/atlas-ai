"""Context aggregation for AI orchestration."""

from __future__ import annotations

from app.ai.types import ConversationContext, ToolResult


class ContextManager:
    """Collect conversational, memory, document, and tool context into one object."""

    def build_context(
        self,
        *,
        request: object,
        conversation_history: list[dict[str, object]] | None = None,
        memories: list[dict[str, object]] | None = None,
        workspace_context: dict[str, object] | None = None,
        documents: list[dict[str, object]] | None = None,
        tool_results: list[ToolResult] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ConversationContext:
        """Build a unified context object for the orchestration pipeline."""
        return ConversationContext(
            request=request,
            conversation_history=conversation_history or [],
            memories=memories or [],
            workspace_context=workspace_context or {},
            documents=documents or [],
            tool_results=tool_results or [],
            metadata=metadata or {},
        )
