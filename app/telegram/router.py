"""Router for Telegram updates."""

from __future__ import annotations

from typing import Any

from telegram import Update


class TelegramRouter:
    """Route updates to the correct handler without embedding business logic."""

    def __init__(self, *, orchestrator: Any | None = None) -> None:
        self._orchestrator = orchestrator

    async def route(self, update: Update) -> Any:
        """Route an update to a specialized handler by update type."""
        if update.message is None:
            return {"type": "unknown", "text": "Unsupported update"}
        if update.message.document:
            return {"type": "document", "text": update.message.caption or ""}
        if update.message.photo:
            return {"type": "photo", "text": update.message.caption or ""}
        if update.message.voice:
            return {"type": "voice", "text": ""}
        if update.message.text:
            return {"type": "message", "text": update.message.text}
        return {"type": "unknown", "text": "Unsupported update"}
