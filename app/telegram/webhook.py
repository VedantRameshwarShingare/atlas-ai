"""Webhook support for Telegram integration."""

from __future__ import annotations

from typing import Any


class TelegramWebhook:
    """Provide webhook lifecycle hooks for the Telegram bot."""

    def __init__(self, *, bot: Any) -> None:
        self._bot = bot

    async def start(self) -> None:
        """Start the webhook lifecycle."""
        return None

    async def stop(self) -> None:
        """Stop the webhook lifecycle."""
        return None

    async def health(self) -> dict[str, Any]:
        """Return webhook health metadata."""
        return {"status": "ok", "service": "telegram_webhook"}
