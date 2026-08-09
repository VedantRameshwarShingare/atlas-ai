"""FastAPI lifespan registration for bootstrap concerns."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import configure_logging
from app.database.session import dispose_database_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize typed settings and logging for the application lifetime."""
    configure_logging()
    app.state.settings = settings
    try:
        yield
    finally:
        await dispose_database_engine()
