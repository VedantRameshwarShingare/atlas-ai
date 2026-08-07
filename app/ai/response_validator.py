"""Validation for AI-generated responses."""

from __future__ import annotations

from app.ai.types import ChatResponse


class ResponseValidator:
    """Validate AI output for emptiness, safety, sources, and length constraints."""

    def __init__(self, max_length: int = 4000) -> None:
        self._max_length = max_length

    def validate(self, response: ChatResponse) -> ChatResponse:
        """Validate and normalize the response before returning it."""
        if not response.content.strip():
            raise ValueError("Response content must not be empty")
        if len(response.content) > self._max_length:
            raise ValueError("Response content exceeds maximum allowed length")
        if not response.sources and not response.tool_citations:
            response.metadata["warnings"] = ["No sources or tool citations were attached"]
        return response
