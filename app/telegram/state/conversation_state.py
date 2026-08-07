"""Conversation state for Telegram sessions."""

from __future__ import annotations

from typing import Any

from app.ai.types import ChatRequest, ChatResponse
from app.ai.enums import ResponseType


class ConversationState:
    """Maintain temporary Telegram conversation state without database logic."""

    def __init__(self) -> None:
        self._messages: list[str] = []
        self._uploads: list[dict[str, Any]] = []

    async def handle_message(self, *, request: ChatRequest, bot: Any, update: Any) -> ChatResponse:
        """Store a user message and return a placeholder response."""
        self._messages.append(request.text)
        return ChatResponse(
            content=f"Received: {request.text}",
            response_type=ResponseType.MARKDOWN,
            metadata={"telegram_chat_id": request.metadata.get("telegram_chat_id")},
        )

    async def store_upload(self, *, update: Any) -> None:
        """Store temporary upload metadata."""
        self._uploads.append({"chat_id": getattr(getattr(update, "effective_chat", None), "id", None)})
