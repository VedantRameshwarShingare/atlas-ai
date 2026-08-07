"""Authentication middleware for Telegram updates."""

from __future__ import annotations

from typing import Any


class AuthenticationMiddleware:
    """Stub authentication middleware; no secrets or sessions are handled here."""

    async def __call__(self, update: Any, context: Any, next_handler: Any) -> Any:
        context.bot_data.setdefault("authenticated", True)
        return await next_handler(update, context)
