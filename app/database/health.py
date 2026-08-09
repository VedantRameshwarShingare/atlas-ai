"""Database connectivity checks used by application health reporting."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.session import async_engine


async def is_database_connected() -> bool:
    """Return whether PostgreSQL accepts a simple connection and query."""
    try:
        async with async_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return False
    return True
