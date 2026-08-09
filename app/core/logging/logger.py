"""Named Loguru logger helper."""

from __future__ import annotations

from loguru import logger
from loguru._logger import Logger

from app.core.logging.config import configure_logging


def get_logger(name: str) -> Logger:
    """Return a configured Loguru logger bound to the supplied module name."""
    configure_logging()
    return logger.bind(module=name)
