"""Structured logging configuration for the application."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from app.config import settings


def configure_logging() -> logging.Logger:
    """Configure console and rotating file handlers for the application."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger = logging.getLogger("atlas_ai")
    logger.setLevel(log_level)
    logger.propagate = False

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "atlas_ai.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


logger: Optional[logging.Logger] = None
