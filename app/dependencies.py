"""Dependency injection placeholders for configuration and runtime services."""

from __future__ import annotations

from typing import Any

from fastapi import Request

from app.config import settings
from app.core.logging import configure_logging


def get_settings() -> Any:
    """Return the application settings singleton."""
    return settings


def get_logger() -> Any:
    """Return a configured application logger."""
    return configure_logging()


def get_database_dependency() -> Any:
    """Placeholder for future database dependency wiring."""
    return None


def get_openai_dependency() -> Any:
    """Placeholder for future OpenAI client dependency wiring."""
    return None


def get_request_settings(request: Request) -> Any:
    """Expose settings through the current request state."""
    return getattr(request.app.state, "settings", settings)
