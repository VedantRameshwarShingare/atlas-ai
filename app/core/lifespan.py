"""FastAPI lifespan management for application startup and shutdown."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.config import settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize logging and configuration during app startup."""
    configure_logging()
    settings

    app.state.settings = settings
    app.state.startup_complete = True

    try:
        yield
    finally:
        app.state.startup_complete = False
