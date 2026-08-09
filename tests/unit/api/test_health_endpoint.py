"""Unit tests for the public health endpoint."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.health import health


@pytest.mark.asyncio
async def test_health_reports_connected_database() -> None:
    """The endpoint reports healthy when the database responds."""
    with patch("app.api.v1.health.is_database_connected", new=AsyncMock(return_value=True)):
        response = await health()

    assert response.model_dump() == {"status": "healthy", "database": "connected"}


@pytest.mark.asyncio
async def test_health_reports_unavailable_database() -> None:
    """The endpoint does not expose database errors when it is unavailable."""
    with patch("app.api.v1.health.is_database_connected", new=AsyncMock(return_value=False)):
        response = await health()

    assert response.model_dump() == {"status": "unhealthy", "database": "unavailable"}
