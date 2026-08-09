"""Normalize AI responses for different output formats."""

from __future__ import annotations

from app.ai.enums import ResponseType
from app.ai.types import ChatResponse


class ResponseFormatter:
    """Format AI output for Markdown, Telegram, or source-oriented contexts."""

    def format(
        self,
        content: str,
        *,
        response_type: ResponseType = ResponseType.MARKDOWN,
        sources: list[str] | None = None,
        tool_citations: list[str] | None = None,
    ) -> ChatResponse:
        """Normalize a raw response string into a typed ChatResponse."""

        return ChatResponse(
            content=content,
            response_type=response_type,
            sources=sources or [],
            tool_citations=tool_citations or [],
        )
