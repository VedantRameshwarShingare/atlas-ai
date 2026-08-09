"""Start command handler."""

from __future__ import annotations

from telegram.ext import ContextTypes

from telegram import Update


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start by greeting the user and preparing onboarding."""
    user_id = update.effective_user.id if update.effective_user else 0
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "Welcome to Atlas AI.\n"
            "I’m ready to help you with research, memory, and workspace context.\n"
            f"Session initialized for user {user_id}."
        ),
    )
