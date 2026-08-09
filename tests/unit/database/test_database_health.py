"""Unit tests for database connectivity reporting."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.database.health import is_database_connected


@pytest.mark.asyncio
async def test_is_database_connected_returns_true_after_select_one() -> None:
    """A successful SELECT 1 reports a connected database."""
    connection = AsyncMock()
    connection.execute = AsyncMock()

    context_manager = MagicMock()
    context_manager.__aenter__ = AsyncMock(return_value=connection)
    context_manager.__aexit__ = AsyncMock(return_value=None)

    mock_engine = MagicMock()
    mock_engine.connect.return_value = context_manager

    with patch(
        "app.database.health.async_engine",
        mock_engine,
    ):
        result = await is_database_connected()

    assert result is True
    connection.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_is_database_connected_returns_false_when_connection_fails() -> None:
    """A SQLAlchemy connection error reports an unavailable database."""
    mock_engine = MagicMock()
    mock_engine.connect.side_effect = SQLAlchemyError("connection refused")

    with patch(
        "app.database.health.async_engine",
        mock_engine,
    ):
        result = await is_database_connected()

    assert result is False
