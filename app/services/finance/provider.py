"""Provider protocol for normalized finance data access."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from app.services.finance.types import CompanyProfile, FinancialMetric, HistoricalPrice, Quote, SymbolSearchResult


class FinancialDataProvider(ABC):
    """Abstract provider interface used by the finance service."""

    name: str

    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote:
        """Return a normalized quote for a symbol."""

    @abstractmethod
    async def get_company_profile(self, symbol: str) -> CompanyProfile:
        """Return normalized company profile details."""

    @abstractmethod
    async def get_company_financials(self, symbol: str) -> list[FinancialMetric]:
        """Return normalized financial metrics for a company."""

    @abstractmethod
    async def get_historical_prices(self, symbol: str, start_date: date, end_date: date) -> list[HistoricalPrice]:
        """Return normalized historical prices."""

    @abstractmethod
    async def search_symbol(self, query: str) -> list[SymbolSearchResult]:
        """Search symbols by query."""
