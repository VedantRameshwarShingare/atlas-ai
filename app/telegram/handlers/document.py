"""Document message handler."""

from __future__ import annotations

from telegram.ext import ContextTypes

from app.telegram.state.conversation_state import ConversationState
from telegram import Update


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming documents and prepare them for later processing."""
    state = context.bot_data.setdefault("conversation_state", ConversationState())
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Document received. It will be queued for processing in a future step.",
    )
    await state.store_upload(update=update)
