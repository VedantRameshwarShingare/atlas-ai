"""Yahoo Finance service abstraction."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseService


class YahooFinanceService(BaseService):
    """Provide historical prices, market data, company statistics, and sector data."""

    name = "yahoo_finance"
    description = "Wraps Yahoo Finance data access"

    async def get_historical_prices(self, symbol: str) -> list[dict[str, Any]]:
        """Return historical price series."""
        return [{"symbol": symbol, "source": "yahoo_finance"}]

    async def get_market_data(self) -> dict[str, Any]:
        """Return market data summary."""
        return {"source": "yahoo_finance"}

    async def get_company_statistics(self, symbol: str) -> dict[str, Any]:
        """Return company statistics."""
        return {"symbol": symbol, "source": "yahoo_finance"}

    async def get_sector_data(self, sector: str) -> dict[str, Any]:
        """Return sector performance data."""
        return {"sector": sector, "source": "yahoo_finance"}

    async def ping(self) -> dict[str, Any]:
        """Return service readiness metadata."""
        return {"service": self.name, "available": True}
