"""Database initialization helpers."""

from __future__ import annotations

from app.database.base import Base
from app.database.session import async_engine


async def initialize_database() -> None:
    """Create all database tables."""
    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
