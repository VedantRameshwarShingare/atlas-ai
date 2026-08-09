"""Formatter for converting Atlas responses to Telegram-safe plain text."""

from __future__ import annotations

from app.ai.types import ChatResponse


class TelegramFormatter:
    """Render Atlas responses as Telegram-safe plain text with splitting support."""

    max_message_length = 4000

    async def render(self, response: ChatResponse) -> str:
        """Render the response into Telegram-safe text."""
        return "\n\n".join(await self.render_messages(response))

    async def render_messages(self, response: ChatResponse) -> list[str]:
        """Split a response into Telegram-sized message chunks."""
        content = (response.content or "").strip() or "Sorry, I couldn't generate a response."
        return self._split_message(content)

    def _split_message(self, content: str) -> list[str]:
        if len(content) <= self.max_message_length:
            return [content]

        paragraphs = content.split("\n\n")
        chunks: list[str] = []
        current = ""

        for paragraph in paragraphs:
            paragraph = paragraph.strip()

            if not paragraph:
                continue

            candidate = paragraph if not current else f"{current}\n\n{paragraph}"

            if len(candidate) <= self.max_message_length:
                current = candidate
                continue

            if current:
                chunks.append(current)
                current = ""

            if len(paragraph) <= self.max_message_length:
                current = paragraph
                continue

            chunks.extend(self._split_hard(paragraph))

        if current:
            chunks.append(current)

        return chunks or [content[: self.max_message_length]]

    def _split_hard(self, content: str) -> list[str]:
        pieces: list[str] = []
        remaining = content

        while remaining:
            if len(remaining) <= self.max_message_length:
                pieces.append(remaining)
                break

            split_at = remaining.rfind(
                "\n",
                0,
                self.max_message_length,
            )

            if split_at <= 0:
                split_at = remaining.rfind(
                    " ",
                    0,
                    self.max_message_length,
                )

            if split_at <= 0:
                split_at = self.max_message_length

            pieces.append(remaining[:split_at].rstrip())
            remaining = remaining[split_at:].lstrip()

        return pieces
