"""Centralized Telegram exception handling."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unexpected Telegram errors without crashing the entire bot."""
    exception = context.error
    if isinstance(update, Update):
        chat_id = update.effective_chat.id if update.effective_chat else None
        if chat_id is not None:
            await context.bot.send_message(chat_id=chat_id, text="An unexpected error occurred. Please try again later.")
    print(f"Telegram error: {exception}")
