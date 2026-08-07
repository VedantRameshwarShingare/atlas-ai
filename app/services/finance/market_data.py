"""Market data service abstraction."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseService


class MarketDataService(BaseService):
    """Provide market-level data access for indexes, movers, and status."""

    name = "market_data"
    description = "Wraps market data access"

    async def get_indexes(self) -> list[dict[str, Any]]:
        """Return major market index snapshots."""
        return [{"source": "market_data"}]

    async def get_top_gainers(self) -> list[dict[str, Any]]:
        """Return top gainers."""
        return [{"source": "market_data"}]

    async def get_top_losers(self) -> list[dict[str, Any]]:
        """Return top losers."""
        return [{"source": "market_data"}]

    async def get_economic_calendar(self) -> list[dict[str, Any]]:
        """Return upcoming economic events."""
        return [{"source": "market_data"}]

    async def ping(self) -> dict[str, Any]:
        """Return service readiness metadata."""
        return {"service": self.name, "available": True}
