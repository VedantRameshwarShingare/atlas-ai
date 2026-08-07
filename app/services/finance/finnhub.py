"""Finnhub finance service abstraction."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseService


class FinnhubService(BaseService):
    """Provide finance-related data access for company profile, news, financials, earnings, and quotes."""

    name = "finnhub"
    description = "Wraps Finnhub data access for financial information"

    def __init__(self, api_key: str) -> None:
        super().__init__()
        self._api_key = api_key

    async def get_company_profile(self, symbol: str) -> dict[str, Any]:
        """Return company profile metadata."""
        return {"symbol": symbol, "source": "finnhub"}

    async def get_company_news(self, symbol: str) -> list[dict[str, Any]]:
        """Return company-related news entries."""
        return [{"symbol": symbol, "source": "finnhub"}]

    async def get_financials(self, symbol: str) -> dict[str, Any]:
        """Return financial statement-related data."""
        return {"symbol": symbol, "source": "finnhub"}

    async def get_earnings(self, symbol: str) -> dict[str, Any]:
        """Return earnings-related data."""
        return {"symbol": symbol, "source": "finnhub"}

    async def get_calendar(self, symbol: str) -> list[dict[str, Any]]:
        """Return earnings calendar data."""
        return [{"symbol": symbol, "source": "finnhub"}]

    async def get_quote(self, symbol: str) -> dict[str, Any]:
        """Return current quote data."""
        return {"symbol": symbol, "source": "finnhub"}

    async def ping(self) -> dict[str, Any]:
        """Return service readiness metadata."""
        return {"service": self.name, "available": bool(self._api_key)}
