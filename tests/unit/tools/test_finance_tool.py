"""Unit tests for finance tool behavior in orchestration path."""

from __future__ import annotations

from datetime import date

import pytest

from app.ai.types import ChatRequest
from app.services.finance.types import (
    CompanyProfile,
    FinancialMetric,
    HistoricalPrice,
    Quote,
    SourceMetadata,
    SymbolSearchResult,
)
from app.tools.finance import FinanceTool


class _FinanceServiceStub:
    async def get_quote(self, symbol: str) -> Quote:
        return Quote(symbol=symbol, price=101.0, source=SourceMetadata(provider="stub", symbol=symbol))

    async def get_company_profile(self, symbol: str) -> CompanyProfile:
        return CompanyProfile(symbol=symbol, name="Atlas Corp", source=SourceMetadata(provider="stub", symbol=symbol))

    async def get_company_financials(self, symbol: str) -> list[FinancialMetric]:
        return [
            FinancialMetric(
                symbol=symbol, metric="eps", value=2.3, source=SourceMetadata(provider="stub", symbol=symbol)
            )
        ]

    async def get_historical_prices(self, symbol: str, start_date: date, end_date: date) -> list[HistoricalPrice]:
        return [
            HistoricalPrice(
                symbol=symbol,
                date=start_date,
                open=10,
                high=12,
                low=9,
                close=11,
                source=SourceMetadata(provider="stub", symbol=symbol),
            ),
            HistoricalPrice(
                symbol=symbol,
                date=end_date,
                open=11,
                high=13,
                low=10,
                close=12,
                source=SourceMetadata(provider="stub", symbol=symbol),
            ),
        ]

    async def search_symbol(self, query: str) -> list[SymbolSearchResult]:
        return [
            SymbolSearchResult(
                symbol="ATLS",
                name=f"{query} Holdings",
                source=SourceMetadata(provider="stub", symbol="ATLS"),
            )
        ]


@pytest.mark.asyncio
async def test_finance_tool_quote_path() -> None:
    tool = FinanceTool(service=_FinanceServiceStub())

    result = await tool.execute(request=ChatRequest(text="What is AAPL trading at?"))

    assert result.success is True
    assert result.data["operation"] == "quote"
    assert result.data["quote"]["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_finance_tool_search_path() -> None:
    tool = FinanceTool(service=_FinanceServiceStub())

    result = await tool.execute(request=ChatRequest(text="find the ticker for Atlas"))

    assert result.success is True
    assert result.data["operation"] == "search"
    assert result.data["results"][0]["symbol"] == "ATLS"
