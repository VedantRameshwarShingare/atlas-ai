"""Loguru sink configuration for console and rotating application logs."""

from __future__ import annotations

import sys
from pathlib import Path
from threading import Lock
from typing import Any

from loguru import logger
from loguru._logger import Logger

from app.core.config import settings
from app.core.logging.formatters import CONSOLE_FORMAT, FILE_FORMAT
from app.core.logging.request_context import get_request_id

LOG_DIRECTORY = Path("logs")
LOG_FILE = LOG_DIRECTORY / "application.log"
_configuration_lock = Lock()
_configured = False


def _inject_context(record: dict[str, Any]) -> None:
    """Add request and module values required by each configured sink format."""
    if record["extra"].get("request_id") in (None, "-"):
        record["extra"]["request_id"] = get_request_id()
    record["extra"].setdefault("module", record["name"])


def configure_logging() -> Logger:
    """Configure Loguru once with console and compressed rotating-file sinks."""
    global _configured
    with _configuration_lock:
        if _configured:
            return logger

        LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
        level = settings.logging.level.upper()
        logger.remove()
        logger.configure(extra={"request_id": "-", "module": "atlas_ai"}, patcher=_inject_context)
        logger.add(sys.stderr, level=level, format=CONSOLE_FORMAT, colorize=True, backtrace=False, diagnose=False)
        logger.add(
            LOG_FILE,
            level=level,
            format=FILE_FORMAT,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            encoding="utf-8",
            backtrace=False,
            diagnose=False,
        )
        _configured = True
    return logger
