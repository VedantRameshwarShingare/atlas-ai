"""SEC EDGAR financial data provider."""

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


class SecEdgarProvider(FinancialDataProvider):
    """Fetch normalized company data from SEC EDGAR endpoints."""

    name = "sec_edgar"
    _ticker_map_path = "/files/company_tickers.json"

    def __init__(
        self,
        *,
        user_agent: str | None = None,
        timeout_seconds: float | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._user_agent = user_agent or settings.finance.sec_user_agent
        self._timeout_seconds = timeout_seconds or settings.finance.request_timeout_seconds
        self._client = http_client or httpx.AsyncClient(base_url="https://data.sec.gov")
        self._ticker_cache: dict[str, dict[str, Any]] | None = None

    def _headers(self) -> dict[str, str]:
        if not self._user_agent:
            raise FinanceConfigurationError("SEC User-Agent is not configured")
        return {
            "User-Agent": self._user_agent,
            "Accept": "application/json",
        }

    async def _request_json(self, path: str) -> dict[str, Any]:
        try:
            response = await self._client.get(path, headers=self._headers(), timeout=self._timeout_seconds)
        except httpx.TimeoutException as exc:
            raise FinanceProviderUnavailableError("SEC request timed out") from exc
        except httpx.HTTPError as exc:
            raise FinanceProviderUnavailableError("SEC request failed") from exc

        if response.status_code == 404:
            raise FinanceNotFoundError("Requested SEC data was not found")
        if response.status_code == 429:
            raise FinanceRateLimitError("SEC rate limit exceeded")
        if response.status_code >= 500:
            raise FinanceProviderUnavailableError("SEC service is unavailable")
        if response.status_code >= 400:
            raise FinanceProviderUnavailableError("SEC request failed")

        try:
            payload = response.json()
        except ValueError as exc:
            raise FinanceProviderUnavailableError("SEC returned invalid JSON") from exc

        if not isinstance(payload, dict):
            raise FinanceProviderUnavailableError("SEC response format is invalid")

        return payload

    async def _ticker_map(self) -> dict[str, dict[str, Any]]:
        if self._ticker_cache is not None:
            return self._ticker_cache

        payload = await self._request_json(self._ticker_map_path)
        mapping: dict[str, dict[str, Any]] = {}
        for row in payload.values():
            if not isinstance(row, dict):
                continue
            symbol = str(row.get("ticker") or "").upper()
            if not symbol:
                continue
            mapping[symbol] = row

        self._ticker_cache = mapping
        return mapping

    async def _resolve_cik(self, symbol: str) -> tuple[str, dict[str, Any]]:
        mapping = await self._ticker_map()
        row = mapping.get(symbol)
        if row is None:
            raise FinanceNotFoundError("Requested symbol was not found")
        cik = str(row.get("cik_str") or "").strip()
        if not cik:
            raise FinanceNotFoundError("Requested symbol was not found")
        return cik.zfill(10), row

    async def _submissions(self, symbol: str) -> tuple[dict[str, Any], dict[str, Any]]:
        cik, row = await self._resolve_cik(symbol)
        payload = await self._request_json(f"/submissions/CIK{cik}.json")
        return payload, row

    async def get_quote(self, symbol: str) -> Quote:
        raise FinanceNotFoundError("SEC does not provide real-time quote data")

    async def get_company_profile(self, symbol: str) -> CompanyProfile:
        payload, row = await self._submissions(symbol)
        return CompanyProfile(
            symbol=symbol,
            name=str(payload.get("name") or row.get("title") or symbol),
            exchange=None,
            industry=payload.get("sicDescription"),
            country=payload.get("stateOfIncorporationDescription"),
            source=SourceMetadata(provider=self.name, symbol=symbol),
        )

    async def get_company_financials(self, symbol: str) -> list[FinancialMetric]:
        payload, _ = await self._submissions(symbol)
        filings = (payload.get("filings") or {}).get("recent") or {}

        forms = filings.get("form") or []
        filing_dates = filings.get("filingDate") or []
        accession_numbers = filings.get("accessionNumber") or []

        metrics: list[FinancialMetric] = []
        for form, filing_date, accession in zip(forms, filing_dates, accession_numbers, strict=True):
            if form not in {"10-K", "10-Q"}:
                continue
            metrics.append(
                FinancialMetric(
                    symbol=symbol,
                    metric="sec_filing",
                    value=1.0,
                    period=str(filing_date),
                    currency=None,
                    source=SourceMetadata(provider=self.name, symbol=f"{symbol}:{accession}"),
                )
            )

        if not metrics:
            raise FinanceNotFoundError("SEC financial filings are unavailable for symbol")

        return metrics

    async def get_historical_prices(self, symbol: str, start_date: date, end_date: date) -> list[HistoricalPrice]:
        del symbol, start_date, end_date
        raise FinanceNotFoundError("SEC does not provide historical market prices")

    async def search_symbol(self, query: str) -> list[SymbolSearchResult]:
        mapping = await self._ticker_map()
        query_l = query.lower().strip()
        results: list[SymbolSearchResult] = []
        for symbol, row in mapping.items():
            title = str(row.get("title") or "")
            if query_l in symbol.lower() or query_l in title.lower():
                results.append(
                    SymbolSearchResult(
                        symbol=symbol,
                        name=title or symbol,
                        exchange=None,
                        type="equity",
                        source=SourceMetadata(provider=self.name, symbol=symbol, retrieved_at=datetime.now(UTC)),
                    )
                )
            if len(results) >= 10:
                break

        if not results:
            raise FinanceNotFoundError("No symbols matched the query")

        return results


class SecEdgarService(SecEdgarProvider):
    """Backward-compatible alias for earlier SEC service references."""

    async def get_filings(self, symbol: str) -> list[dict[str, Any]]:
        """Return filing-like metadata in legacy shape."""
        metrics = await self.get_company_financials(symbol)
        return [metric.model_dump(mode="json") for metric in metrics]

    async def get_filing(self, accession_number: str) -> dict[str, Any]:
        """Preserve the old method with controlled not-found behavior."""
        raise FinanceNotFoundError(f"SEC filing {accession_number} is not directly supported")
