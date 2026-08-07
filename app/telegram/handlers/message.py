"""Text message handler."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.ai.types import ChatRequest
from app.telegram.formatter.telegram_formatter import TelegramFormatter
from app.telegram.state.conversation_state import ConversationState


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text and forward it to the orchestrator."""
    user_id = update.effective_user.id if update.effective_user else 0
    text = update.message.text or ""
    state = context.bot_data.setdefault("conversation_state", ConversationState())
    request = ChatRequest(user_id=None, text=text, metadata={"telegram_chat_id": str(update.effective_chat.id)})
    response = await state.handle_message(request=request, bot=context.bot, update=update)
    formatter = TelegramFormatter()
    rendered = await formatter.render(response)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=rendered, parse_mode="Markdown")
