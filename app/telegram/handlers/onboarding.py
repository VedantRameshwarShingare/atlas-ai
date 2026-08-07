"""Conversational onboarding handler for Telegram."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from app.telegram.state.onboarding_state import OnboardingState


async def onboarding_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Advance onboarding via natural conversation rather than inline menus."""
    state = context.bot_data.setdefault("onboarding_state", OnboardingState())
    message = update.message.text or ""
    response = await state.handle_message(message)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)
