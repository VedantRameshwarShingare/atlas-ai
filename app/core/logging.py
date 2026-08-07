"""Minimal standard-library logging configuration for application bootstrap."""

from __future__ import annotations

import logging

from app.core.config import settings

LOGGER_NAME = "atlas_ai"


def configure_logging() -> logging.Logger:
    """Configure and return the Atlas AI application logger once."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(logging, settings.logging.level.upper(), logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        logger.addHandler(handler)
    logger.propagate = False
    return logger


def get_logger() -> logging.Logger:
    """Return the configured Atlas AI logger."""
    return configure_logging()
