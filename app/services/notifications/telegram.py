"""Telegram notification service abstraction."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseService


class TelegramNotificationService(BaseService):
    """Provide a typed interface for sending Telegram notifications."""

    name = "telegram_notifications"
    description = "Wraps outbound Telegram message delivery"

    async def send_message(self, *, chat_id: str, message: str) -> dict[str, Any]:
        """Send a message to a Telegram chat."""
        return {"chat_id": chat_id, "message": message, "source": "telegram"}

    async def ping(self) -> dict[str, Any]:
        """Return service readiness metadata."""
        return {"service": self.name, "available": True}
