"""Loguru output formats used by Atlas AI logging sinks."""

from __future__ import annotations

CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level:<8}</level> | "
    "<cyan>{extra[request_id]}</cyan> | "
    "<magenta>{extra[module]}</magenta> | "
    "<level>{message}</level>\n{exception}"
)

FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {extra[request_id]} | {extra[module]} | {message}\n{exception}"
)
