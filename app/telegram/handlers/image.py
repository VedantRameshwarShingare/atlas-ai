"""Image message handler placeholder."""

from __future__ import annotations

from telegram.ext import ContextTypes

from telegram import Update


async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle image uploads with a placeholder message."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Image understanding is not available yet.",
    )
