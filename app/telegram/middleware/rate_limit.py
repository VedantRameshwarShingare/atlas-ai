"""Rate limiting middleware for Telegram updates."""

from __future__ import annotations

from typing import Any


class RateLimitMiddleware:
    """Simple in-memory rate limiting scaffold."""

    def __init__(self) -> None:
        self._requests: dict[str, int] = {}

    async def __call__(self, update: Any, context: Any, next_handler: Any) -> Any:
        chat_id = str(getattr(getattr(update, "effective_chat", None), "id", "unknown"))
        self._requests[chat_id] = self._requests.get(chat_id, 0) + 1
        if self._requests[chat_id] > 50:
            return None
        return await next_handler(update, context)
