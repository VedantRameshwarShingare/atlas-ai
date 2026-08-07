"""Application-wide configuration defaults with no secret values."""

from __future__ import annotations

DEFAULT_APPLICATION_NAME = "Atlas AI"
DEFAULT_APPLICATION_VERSION = "0.1.0"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
DEFAULT_DATABASE_URL = "sqlite:///./atlas_ai.db"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_TIMEZONE = "UTC"
DEFAULT_SCHEDULER_TIMEZONE = "UTC"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
