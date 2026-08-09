"""Yahoo Finance financial data provider."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import httpx

from app.core.config import settings
from app.services.finance.exceptions import (
    FinanceNotFoundError,
    FinanceProviderUnavailableError,
    FinanceRateLimitError,
)
from app.services.finance.provider import FinancialDataProvider
from app.services.finance.types import (
    CompanyProfile,
    FinancialMetric,
    HistoricalPrice,
    Quote,
    SourceMetadata,
    SymbolSearchResult,
)


class YahooFinanceProvider(FinancialDataProvider):
    """Fetch normalized finance data from Yahoo Finance public endpoints."""

    name = "yahoo_finance"
    _search_path = "/v1/finance/search"
    _quote_path = "/v7/finance/quote"

    def __init__(
        self,
        *,
        timeout_seconds: float | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._timeout_seconds = timeout_seconds or settings.finance.request_timeout_seconds
        self._client = http_client or httpx.AsyncClient(base_url="https://query1.finance.yahoo.com")

    async def _request_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = await self._client.get(path, params=params, timeout=self._timeout_seconds)
        except httpx.TimeoutException as exc:
            raise FinanceProviderUnavailableError("Yahoo request timed out") from exc
        except httpx.HTTPError as exc:
            raise FinanceProviderUnavailableError("Yahoo request failed") from exc

        if response.status_code == 404:
            raise FinanceNotFoundError("Requested symbol was not found")
        if response.status_code == 429:
            raise FinanceRateLimitError("Yahoo rate limit exceeded")
        if response.status_code >= 500:
            raise FinanceProviderUnavailableError("Yahoo service is unavailable")
        if response.status_code >= 400:
            raise FinanceProviderUnavailableError("Yahoo request failed")

        try:
            payload = response.json()
        except ValueError as exc:
            raise FinanceProviderUnavailableError("Yahoo returned invalid JSON") from exc

        if not isinstance(payload, dict):
            raise FinanceProviderUnavailableError("Yahoo response format is invalid")

        return payload

    async def _get_quote_row(self, symbol: str) -> dict[str, Any]:
        payload = await self._request_json(self._quote_path, {"symbols": symbol})
        quote_response = payload.get("quoteResponse", {})
        rows = quote_response.get("result", []) if isinstance(quote_response, dict) else []
        for row in rows:
            if isinstance(row, dict) and str(row.get("symbol", "")).upper() == symbol:
                return row
        raise FinanceNotFoundError("Requested symbol was not found")

    async def get_quote(self, symbol: str) -> Quote:
        row = await self._get_quote_row(symbol)
        price = row.get("regularMarketPrice")
        if price is None:
            raise FinanceNotFoundError("Quote data is unavailable for symbol")

        timestamp = None
        market_time = row.get("regularMarketTime")
        if isinstance(market_time, (int, float)):
            timestamp = datetime.fromtimestamp(int(market_time), tz=UTC)

        return Quote(
            symbol=symbol,
            price=float(price),
            currency=row.get("currency"),
            change=float(row.get("regularMarketChange") or 0),
            change_percent=float(row.get("regularMarketChangePercent") or 0),
            timestamp=timestamp,
            source=SourceMetadata(provider=self.name, symbol=symbol),
        )

    async def get_company_profile(self, symbol: str) -> CompanyProfile:
        row = await self._get_quote_row(symbol)
        return CompanyProfile(
            symbol=symbol,
            name=str(row.get("longName") or row.get("shortName") or symbol),
            exchange=row.get("fullExchangeName") or row.get("exchange"),
            industry=row.get("industryDisp") or row.get("sectorDisp"),
            country=row.get("region"),
            source=SourceMetadata(provider=self.name, symbol=symbol),
        )

    async def get_company_financials(self, symbol: str) -> list[FinancialMetric]:
        row = await self._get_quote_row(symbol)
        normalized: list[FinancialMetric] = []
        metric_map = {
            "marketCap": "marketCap",
            "trailingPE": "trailingPE",
            "epsTrailingTwelveMonths": "epsTrailingTwelveMonths",
        }

        for source_key, metric_name in metric_map.items():
            value = row.get(source_key)
            if value is None:
                continue
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            normalized.append(
                FinancialMetric(
                    symbol=symbol,
                    metric=metric_name,
                    value=number,
                    period="ttm",
                    currency=row.get("currency"),
                    source=SourceMetadata(provider=self.name, symbol=symbol),
                )
            )

        if not normalized:
            raise FinanceNotFoundError("Company financial metrics are unavailable for symbol")

        return normalized

    async def get_historical_prices(self, symbol: str, start_date: date, end_date: date) -> list[HistoricalPrice]:
        start_ts = int(datetime.combine(start_date, datetime.min.time(), tzinfo=UTC).timestamp())
        end_ts = int(datetime.combine(end_date, datetime.max.time(), tzinfo=UTC).timestamp())
        payload = await self._request_json(
            f"/v8/finance/chart/{symbol}",
            {"period1": start_ts, "period2": end_ts, "interval": "1d", "events": "history"},
        )

        chart = payload.get("chart", {})
        rows = chart.get("result", []) if isinstance(chart, dict) else []
        if not rows:
            raise FinanceNotFoundError("Historical price data is unavailable for symbol")

        result = rows[0]
        timestamps = result.get("timestamp") or []
        quote_rows = (result.get("indicators") or {}).get("quote") or []
        if not timestamps or not quote_rows:
            raise FinanceNotFoundError("Historical price data is unavailable for symbol")

        quote_row = quote_rows[0]
        opens = quote_row.get("open") or []
        highs = quote_row.get("high") or []
        lows = quote_row.get("low") or []
        closes = quote_row.get("close") or []
        volumes = quote_row.get("volume") or []

        records: list[HistoricalPrice] = []
        for ts, open_value, high_value, low_value, close_value, volume_value in zip(
            timestamps,
            opens,
            highs,
            lows,
            closes,
            volumes,
            strict=True,
        ):
            if None in (open_value, high_value, low_value, close_value):
                continue
            records.append(
                HistoricalPrice(
                    symbol=symbol,
                    date=datetime.fromtimestamp(int(ts), tz=UTC).date(),
                    open=float(open_value),
                    high=float(high_value),
                    low=float(low_value),
                    close=float(close_value),
                    volume=float(volume_value) if volume_value is not None else None,
                    source=SourceMetadata(provider=self.name, symbol=symbol),
                )
            )

        if not records:
            raise FinanceNotFoundError("Historical price data is unavailable for symbol")

        return records

    async def search_symbol(self, query: str) -> list[SymbolSearchResult]:
        payload = await self._request_json(self._search_path, {"q": query, "quotesCount": 10, "newsCount": 0})
        rows = payload.get("quotes")
        if not isinstance(rows, list) or not rows:
            raise FinanceNotFoundError("No symbols matched the query")

        results: list[SymbolSearchResult] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            symbol = str(row.get("symbol") or "").upper()
            if not symbol:
                continue
            results.append(
                SymbolSearchResult(
                    symbol=symbol,
                    name=str(row.get("longname") or row.get("shortname") or symbol),
                    exchange=row.get("exchange") or row.get("exchDisp"),
                    type=row.get("quoteType"),
                    source=SourceMetadata(provider=self.name, symbol=symbol),
                )
            )

        if not results:
            raise FinanceNotFoundError("No symbols matched the query")

        return results


class YahooFinanceService(YahooFinanceProvider):
    """Backward-compatible alias for earlier Yahoo service references."""
