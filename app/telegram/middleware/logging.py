"""Logging middleware for Telegram updates."""

from __future__ import annotations

from typing import Any


class LoggingMiddleware:
    """Record basic update metadata for future tracing."""

    async def __call__(self, update: Any, context: Any, next_handler: Any) -> Any:
        print(f"Telegram update received: {getattr(update, 'effective_chat', None)}")
        return await next_handler(update, context)
