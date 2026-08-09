"""Async SQLAlchemy engine, session factory, and lifecycle helpers."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

async_engine: AsyncEngine = create_async_engine(
    settings.database.url,
    echo=settings.database.echo,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Retain the established public name for existing callers during the migration.
AsyncSessionFactory = async_session_factory


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session for dependency injection."""
    async with async_session_factory() as session:
        yield session


async def dispose_database_engine() -> None:
    """Close all pooled database connections during application shutdown."""
    await async_engine.dispose()
