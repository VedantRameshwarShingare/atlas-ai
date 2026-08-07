"""Formatter for converting Atlas responses to Telegram-friendly Markdown."""

from __future__ import annotations

from app.ai.types import ChatResponse


class TelegramFormatter:
    """Render Atlas responses as Telegram-safe Markdown with splitting support."""

    async def render(self, response: ChatResponse) -> str:
        """Render the response into Telegram Markdown and split oversized messages."""
        content = response.content or ""
        if len(content) > 3500:
            parts = [content[i : i + 3500] for i in range(0, len(content), 3500)]
            return "\n\n---\n\n".join(parts)
        return content
