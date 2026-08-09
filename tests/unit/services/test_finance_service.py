"""Unit tests for finance service orchestration and validation."""

from __future__ import annotations

from datetime import date

import pytest

from app.services.finance.exceptions import FinanceProviderUnavailableError, FinanceValidationError
from app.services.finance.service import FinanceService
from app.services.finance.types import (
    CompanyProfile,
    FinancialMetric,
    HistoricalPrice,
    Quote,
    SourceMetadata,
    SymbolSearchResult,
)


class _ProviderStub:
    def __init__(self, *, fail: Exception | None = None, provider_name: str = "stub") -> None:
        self._fail = fail
        self._provider_name = provider_name

    async def get_quote(self, symbol: str) -> Quote:
        if self._fail is not None:
            raise self._fail
        return Quote(symbol=symbol, price=100.0, source=SourceMetadata(provider=self._provider_name, symbol=symbol))

    async def get_company_profile(self, symbol: str) -> CompanyProfile:
        if self._fail is not None:
            raise self._fail
        return CompanyProfile(
            symbol=symbol, name=f"{symbol} Corp", source=SourceMetadata(provider=self._provider_name, symbol=symbol)
        )

    async def get_company_financials(self, symbol: str) -> list[FinancialMetric]:
        if self._fail is not None:
            raise self._fail
        return [
            FinancialMetric(
                symbol=symbol,
                metric="pe_ratio",
                value=15.0,
                source=SourceMetadata(provider=self._provider_name, symbol=symbol),
            )
        ]

    async def get_historical_prices(self, symbol: str, start_date: date, end_date: date) -> list[HistoricalPrice]:
        if self._fail is not None:
            raise self._fail
        return [
            HistoricalPrice(
                symbol=symbol,
                date=start_date,
                open=100,
                high=110,
                low=99,
                close=108,
                volume=1000,
                source=SourceMetadata(provider=self._provider_name, symbol=symbol),
            ),
            HistoricalPrice(
                symbol=symbol,
                date=end_date,
                open=108,
                high=112,
                low=105,
                close=111,
                volume=1200,
                source=SourceMetadata(provider=self._provider_name, symbol=symbol),
            ),
        ]

    async def search_symbol(self, query: str) -> list[SymbolSearchResult]:
        if self._fail is not None:
            raise self._fail
        return [
            SymbolSearchResult(
                symbol="ATLS",
                name=f"{query} Holdings",
                exchange="NYSE",
                source=SourceMetadata(provider=self._provider_name, symbol="ATLS"),
            )
        ]


@pytest.mark.asyncio
async def test_finance_service_falls_back_to_secondary_provider_for_quote() -> None:
    primary = _ProviderStub(fail=FinanceProviderUnavailableError("primary down"), provider_name="primary")
    secondary = _ProviderStub(provider_name="secondary")
    service = FinanceService(finnhub_provider=primary, yahoo_provider=secondary, sec_provider=secondary)

    quote = await service.get_quote("aapl")

    assert quote.symbol == "AAPL"
    assert quote.source.provider == "secondary"


@pytest.mark.asyncio
async def test_finance_service_validates_symbol_and_date_range() -> None:
    provider = _ProviderStub(provider_name="test")
    service = FinanceService(finnhub_provider=provider, yahoo_provider=provider, sec_provider=provider)

    with pytest.raises(FinanceValidationError):
        await service.get_quote("$$")

    with pytest.raises(FinanceValidationError):
        await service.get_historical_prices("AAPL", date(2025, 1, 2), date(2025, 1, 1))


@pytest.mark.asyncio
async def test_finance_service_validates_search_query_length() -> None:
    provider = _ProviderStub(provider_name="test")
    service = FinanceService(finnhub_provider=provider, yahoo_provider=provider, sec_provider=provider)

    with pytest.raises(FinanceValidationError):
        await service.search_symbol(" " * 5)

    with pytest.raises(FinanceValidationError):
        await service.search_symbol("x" * 101)
