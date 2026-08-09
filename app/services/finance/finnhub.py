"""Finnhub financial data provider."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import httpx

from app.core.config import settings
from app.services.finance.exceptions import (
    FinanceConfigurationError,
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


class FinnhubProvider(FinancialDataProvider):
    """Fetch normalized finance data from Finnhub."""

    name = "finnhub"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key or (
            settings.finance.finnhub_api_key.get_secret_value() if settings.finance.finnhub_api_key else None
        )
        self._timeout_seconds = timeout_seconds or settings.finance.request_timeout_seconds
        self._client = http_client or httpx.AsyncClient(base_url="https://finnhub.io/api/v1")

    async def _request_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self._api_key:
            raise FinanceConfigurationError("Finnhub API key is not configured")

        query = {**params, "token": self._api_key}

        try:
            response = await self._client.get(path, params=query, timeout=self._timeout_seconds)
        except httpx.TimeoutException as exc:
            raise FinanceProviderUnavailableError("Finnhub request timed out") from exc
        except httpx.HTTPError as exc:
            raise FinanceProviderUnavailableError("Finnhub request failed") from exc

        if response.status_code in {401, 403}:
            raise FinanceProviderUnavailableError("Finnhub authentication failed")
        if response.status_code == 404:
            raise FinanceNotFoundError("Requested symbol was not found")
        if response.status_code == 429:
            raise FinanceRateLimitError("Finnhub rate limit exceeded")
        if response.status_code >= 500:
            raise FinanceProviderUnavailableError("Finnhub service is unavailable")
        if response.status_code >= 400:
            raise FinanceProviderUnavailableError("Finnhub request failed")

        try:
            payload = response.json()
        except ValueError as exc:
            raise FinanceProviderUnavailableError("Finnhub returned invalid JSON") from exc

        if not isinstance(payload, dict):
            raise FinanceProviderUnavailableError("Finnhub response format is invalid")

        return payload

    async def get_quote(self, symbol: str) -> Quote:
        payload = await self._request_json("/quote", {"symbol": symbol})

        price = float(payload.get("c") or 0)
        if price <= 0:
            raise FinanceNotFoundError("Quote data is unavailable for symbol")

        timestamp = None
        if payload.get("t"):
            timestamp = datetime.fromtimestamp(int(payload["t"]), tz=UTC)

        return Quote(
            symbol=symbol,
            price=price,
            currency="USD",
            change=float(payload.get("d") or 0),
            change_percent=float(payload.get("dp") or 0),
            timestamp=timestamp,
            source=SourceMetadata(provider=self.name, symbol=symbol),
        )

    async def get_company_profile(self, symbol: str) -> CompanyProfile:
        payload = await self._request_json("/stock/profile2", {"symbol": symbol})

        if not payload.get("name"):
            raise FinanceNotFoundError("Company profile is unavailable for symbol")

        return CompanyProfile(
            symbol=symbol,
            name=str(payload.get("name")),
            exchange=payload.get("exchange"),
            industry=payload.get("finnhubIndustry"),
            country=payload.get("country"),
            source=SourceMetadata(provider=self.name, symbol=symbol),
        )

    async def get_company_financials(self, symbol: str) -> list[FinancialMetric]:
        payload = await self._request_json("/stock/metric", {"symbol": symbol, "metric": "all"})
        metrics = payload.get("metric")

        if not isinstance(metrics, dict) or not metrics:
            raise FinanceNotFoundError("Company financial metrics are unavailable for symbol")

        normalized: list[FinancialMetric] = []
        for metric_name in ("marketCapitalization", "52WeekHigh", "52WeekLow", "epsTTM", "peTTM"):
            value = metrics.get(metric_name)
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
                    currency="USD",
                    source=SourceMetadata(provider=self.name, symbol=symbol),
                )
            )

        if not normalized:
            raise FinanceNotFoundError("Company financial metrics are unavailable for symbol")

        return normalized

    async def get_historical_prices(self, symbol: str, start_date: date, end_date: date) -> list[HistoricalPrice]:
        payload = await self._request_json(
            "/stock/candle",
            {
                "symbol": symbol,
                "resolution": "D",
                "from": int(datetime.combine(start_date, datetime.min.time(), tzinfo=UTC).timestamp()),
                "to": int(datetime.combine(end_date, datetime.max.time(), tzinfo=UTC).timestamp()),
            },
        )

        if payload.get("s") != "ok":
            raise FinanceNotFoundError("Historical price data is unavailable for symbol")

        timestamps = payload.get("t") or []
        opens = payload.get("o") or []
        highs = payload.get("h") or []
        lows = payload.get("l") or []
        closes = payload.get("c") or []
        volumes = payload.get("v") or []

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
            records.append(
                HistoricalPrice(
                    symbol=symbol,
                    date=datetime.fromtimestamp(int(ts), tz=UTC).date(),
                    open=float(open_value),
                    high=float(high_value),
                    low=float(low_value),
                    close=float(close_value),
                    volume=float(volume_value),
                    source=SourceMetadata(provider=self.name, symbol=symbol),
                )
            )

        if not records:
            raise FinanceNotFoundError("Historical price data is unavailable for symbol")

        return records

    async def search_symbol(self, query: str) -> list[SymbolSearchResult]:
        payload = await self._request_json("/search", {"q": query})
        rows = payload.get("result")
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
                    name=str(row.get("description") or symbol),
                    exchange=row.get("mic"),
                    type=row.get("type"),
                    source=SourceMetadata(provider=self.name, symbol=symbol),
                )
            )

        if not results:
            raise FinanceNotFoundError("No symbols matched the query")

        return results


class FinnhubService(FinnhubProvider):
    """Backward-compatible alias for earlier Finnhub service references."""
