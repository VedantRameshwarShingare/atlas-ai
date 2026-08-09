"""Finance tool integration for the existing AI tool pipeline."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta
from typing import Any

from app.ai.enums import ToolType
from app.ai.types import ChatRequest
from app.services.finance.service import FinanceService
from app.tools.base import BaseTool, ToolResult

_SYMBOL_PATTERN = re.compile(r"\b[A-Z]{1,6}(?:\.[A-Z])?\b")

_COMPANY_SYMBOLS = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "tesla": "TSLA",
    "nvidia": "NVDA",
    "meta": "META",
}


class FinanceTool(BaseTool):
    """Execute finance operations using the shared finance service."""

    name = "finance"
    description = "Provides quote, company, historical, and symbol-search finance results"
    tool_type = ToolType.FINANCE

    def __init__(self, service: FinanceService | None = None) -> None:
        self._service = service or FinanceService()

    def validate(self, **kwargs: Any) -> None:
        request = kwargs.get("request")

        if not isinstance(request, ChatRequest):
            raise ValueError("request must be a ChatRequest")

        if not request.text.strip():
            raise ValueError("request text is required")

    async def execute(self, **kwargs: Any) -> ToolResult:
        request: ChatRequest = kwargs["request"]
        lowered = request.text.lower()
        symbol = self._extract_symbol(request.text)

        if "historical" in lowered or "ohlc" in lowered or "candlestick" in lowered:
            if symbol is None:
                raise ValueError("No symbol found for historical query")

            end_date = date.today()
            start_date = end_date - timedelta(days=30)

            prices = await self._service.get_historical_prices(
                symbol,
                start_date,
                end_date,
            )

            return ToolResult(
                success=True,
                tool_name=self.name,
                data={
                    "operation": "history",
                    "symbol": symbol,
                    "prices": [item.model_dump(mode="json") for item in prices],
                },
                sources=[f"finance:{symbol}"],
            )

        if "company profile" in lowered or "tell me about" in lowered:
            if symbol is None:
                raise ValueError("No symbol found for company query")

            profile = await self._service.get_company_profile(symbol)
            financials = await self._service.get_company_financials(symbol)

            return ToolResult(
                success=True,
                tool_name=self.name,
                data={
                    "operation": "company",
                    "profile": profile.model_dump(mode="json"),
                    "financials": [item.model_dump(mode="json") for item in financials],
                },
                sources=[f"finance:{symbol}"],
            )

        if "find the ticker" in lowered or ("find" in lowered and "ticker" in lowered):
            query = self._extract_search_query(request.text)
            results = await self._service.search_symbol(query)

            return ToolResult(
                success=True,
                tool_name=self.name,
                data={
                    "operation": "search",
                    "query": query,
                    "results": [item.model_dump(mode="json") for item in results],
                },
                sources=["finance:search"],
            )

        if symbol is None:
            raise ValueError("No symbol found for quote query")

        quote = await self._service.get_quote(symbol)

        return ToolResult(
            success=True,
            tool_name=self.name,
            data={
                "operation": "quote",
                "symbol": symbol,
                "quote": quote.model_dump(mode="json"),
            },
            sources=[f"finance:{symbol}"],
            metadata={"retrieved_at": datetime.now(UTC).isoformat()},
        )

    @staticmethod
    def _extract_symbol(text: str) -> str | None:
        """Resolve company names or explicit ticker symbols."""

        lowered = text.lower()

        # Resolve common company names to their ticker symbols first.
        for company, symbol in _COMPANY_SYMBOLS.items():
            if re.search(rf"\b{re.escape(company)}\b", lowered):
                return symbol

        # Ignore common English words that can match the ticker pattern.
        symbol_stopwords = {
            "WHAT",
            "WHEN",
            "WHERE",
            "WHO",
            "WHY",
            "HOW",
            "IS",
            "ARE",
            "THE",
            "THIS",
            "THAT",
            "STOCK",
            "PRICE",
            "TRADING",
            "TODAY",
            "AT",
            "FOR",
            "USD",
            "OHLC",
        }

        for token in _SYMBOL_PATTERN.findall(text.upper()):
            if token in symbol_stopwords:
                continue
            return token

        return None

    @staticmethod
    def _extract_search_query(text: str) -> str:
        cleaned = text.strip()

        parts = re.split(
            r"find the ticker for|find ticker for|ticker for",
            cleaned,
            flags=re.IGNORECASE,
        )

        candidate = parts[-1].strip() if len(parts) > 1 else cleaned
        return candidate or cleaned
