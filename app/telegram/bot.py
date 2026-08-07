"""Telegram bot initialization for Atlas AI."""

from __future__ import annotations

import os
from typing import Any

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.telegram.handlers.errors import error_handler
from app.telegram.handlers.message import message_handler
from app.telegram.handlers.start import start_handler
from app.telegram.router import TelegramRouter
from app.telegram.middleware.authentication import AuthenticationMiddleware
from app.telegram.middleware.logging import LoggingMiddleware
from app.telegram.middleware.rate_limit import RateLimitMiddleware


class AtlasTelegramBot:
    """Initialize and configure the Telegram bot application."""

    def __init__(self, *, token: str | None = None, orchestrator: Any | None = None) -> None:
        self._token = token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self._application = Application.builder().token(self._token).build()
        self._router = TelegramRouter(orchestrator=orchestrator)
        self._register_handlers()
        self._register_middleware()

    def _register_handlers(self) -> None:
        self._application.add_handler(CommandHandler("start", start_handler))
        self._application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        self._application.add_error_handler(error_handler)

    def _register_middleware(self) -> None:
        self._application.add_middleware(LoggingMiddleware())
        self._application.add_middleware(AuthenticationMiddleware())
        self._application.add_middleware(RateLimitMiddleware())

    @property
    def application(self) -> Application:
        """Return the underlying telegram application."""
        return self._application

    @property
    def router(self) -> TelegramRouter:
        """Return the router used by the bot."""
        return self._router

    async def initialize(self) -> None:
        """Initialize bot state and setup."""
        await self._application.initialize()

    async def shutdown(self) -> None:
        """Shutdown and clear bot resources."""
        await self._application.shutdown()
