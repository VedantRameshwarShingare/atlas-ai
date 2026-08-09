"""Finance service for provider orchestration and workspace-scoped operations."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.membership import MembershipRole
from app.models.watchlist import Watchlist
from app.repositories.alert_repository import AlertRepository
from app.repositories.membership_repository import MembershipRepository
from app.repositories.watchlist_repository import WatchlistRepository
from app.services.finance.exceptions import (
    FinanceConfigurationError,
    FinanceError,
    FinanceNotFoundError,
    FinanceProviderUnavailableError,
    FinanceRateLimitError,
    FinanceValidationError,
)
from app.services.finance.finnhub import FinnhubProvider
from app.services.finance.provider import FinancialDataProvider
from app.services.finance.sec_edgar import SecEdgarProvider
from app.services.finance.types import CompanyProfile, FinancialMetric, HistoricalPrice, Quote, SymbolSearchResult
from app.services.finance.yahoo_finance import YahooFinanceProvider

_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.\-]{1,12}$")


class FinanceService:
    """Coordinate finance providers and workspace-scoped watchlist/alert data."""

    def __init__(
        self,
        session: AsyncSession | None = None,
        *,
        finnhub_provider: FinancialDataProvider | None = None,
        yahoo_provider: FinancialDataProvider | None = None,
        sec_provider: FinancialDataProvider | None = None,
    ) -> None:
        self.session = session
        self.memberships = MembershipRepository(session) if session is not None else None
        self.watchlists = WatchlistRepository(session) if session is not None else None
        self.alerts = AlertRepository(session) if session is not None else None
        self.finnhub_provider = finnhub_provider or FinnhubProvider()
        self.yahoo_provider = yahoo_provider or YahooFinanceProvider()
        self.sec_provider = sec_provider or SecEdgarProvider()

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not normalized:
            raise FinanceValidationError("Symbol is required")
        if not _SYMBOL_PATTERN.match(normalized):
            raise FinanceValidationError("Symbol format is invalid")
        return normalized

    @staticmethod
    def _validate_search_query(query: str) -> str:
        normalized = query.strip()
        if not normalized:
            raise FinanceValidationError("Search query is required")
        if len(normalized) > 100:
            raise FinanceValidationError("Search query exceeds maximum length")
        return normalized

    @staticmethod
    def _validate_date_range(start_date: date, end_date: date, *, max_days: int = 3650) -> None:
        if end_date < start_date:
            raise FinanceValidationError("End date must be on or after start date")
        if (end_date - start_date).days > max_days:
            raise FinanceValidationError("Requested date range exceeds allowed maximum")

    async def _first_success(self, providers: list[FinancialDataProvider], operation: str, *args: object) -> object:
        last_error: FinanceError | None = None
        for provider in providers:
            try:
                method = getattr(provider, operation)
                return await method(*args)
            except (
                FinanceNotFoundError,
                FinanceRateLimitError,
                FinanceProviderUnavailableError,
                FinanceConfigurationError,
            ) as exc:
                last_error = exc
                continue

        if last_error is not None:
            raise last_error

        raise FinanceProviderUnavailableError("No finance providers are available")

    async def get_quote(self, symbol: str) -> Quote:
        normalized = self._normalize_symbol(symbol)
        return await self._first_success([self.finnhub_provider, self.yahoo_provider], "get_quote", normalized)

    async def get_company_profile(self, symbol: str) -> CompanyProfile:
        normalized = self._normalize_symbol(symbol)
        return await self._first_success(
            [self.finnhub_provider, self.yahoo_provider, self.sec_provider],
            "get_company_profile",
            normalized,
        )

    async def get_company_financials(self, symbol: str) -> list[FinancialMetric]:
        normalized = self._normalize_symbol(symbol)
        return await self._first_success(
            [self.finnhub_provider, self.sec_provider, self.yahoo_provider],
            "get_company_financials",
            normalized,
        )

    async def get_historical_prices(self, symbol: str, start_date: date, end_date: date) -> list[HistoricalPrice]:
        normalized = self._normalize_symbol(symbol)
        self._validate_date_range(start_date, end_date)
        return await self._first_success(
            [self.finnhub_provider, self.yahoo_provider],
            "get_historical_prices",
            normalized,
            start_date,
            end_date,
        )

    async def search_symbol(self, query: str) -> list[SymbolSearchResult]:
        normalized = self._validate_search_query(query)
        return await self._first_success(
            [self.finnhub_provider, self.yahoo_provider, self.sec_provider],
            "search_symbol",
            normalized,
        )

    async def list_watchlist(self, *, workspace_id: UUID, user_id: UUID) -> list[Watchlist]:
        membership = await self.ensure_workspace_access(workspace_id=workspace_id, user_id=user_id)
        del membership
        if self.watchlists is None:
            raise FinanceProviderUnavailableError("Database session is unavailable")
        return await self.watchlists.list_for_workspace(workspace_id)

    async def add_watchlist_symbol(self, *, workspace_id: UUID, user_id: UUID, symbol: str) -> Watchlist:
        membership = await self.ensure_workspace_access(workspace_id=workspace_id, user_id=user_id)
        del membership
        normalized = self._normalize_symbol(symbol)

        if self.watchlists is None:
            raise FinanceProviderUnavailableError("Database session is unavailable")

        existing = await self.watchlists.get_by_workspace_and_symbol(workspace_id=workspace_id, symbol=normalized)
        if existing is not None:
            raise FinanceValidationError("Symbol already exists in watchlist")

        profile = await self.get_company_profile(normalized)

        watchlist_item = Watchlist(
            workspace_id=workspace_id,
            user_id=user_id,
            symbol=normalized,
            company_name=profile.name,
            market=profile.exchange,
            is_active=True,
        )
        return await self.watchlists.create(watchlist_item)

    async def remove_watchlist_symbol(self, *, workspace_id: UUID, user_id: UUID, symbol: str) -> None:
        membership = await self.ensure_workspace_access(workspace_id=workspace_id, user_id=user_id)
        del membership
        normalized = self._normalize_symbol(symbol)

        if self.watchlists is None:
            raise FinanceProviderUnavailableError("Database session is unavailable")

        item = await self.watchlists.get_by_workspace_and_symbol(workspace_id=workspace_id, symbol=normalized)
        if item is None:
            raise FinanceNotFoundError("Watchlist symbol not found")

        await self.watchlists.delete(item)

    async def list_alerts(self, *, workspace_id: UUID, user_id: UUID) -> list[Alert]:
        membership = await self.ensure_workspace_access(workspace_id=workspace_id, user_id=user_id)
        del membership

        if self.alerts is None:
            raise FinanceProviderUnavailableError("Database session is unavailable")

        return await self.alerts.list_for_workspace(workspace_id)

    async def create_alert(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
        symbol: str,
        condition: str,
        threshold: float,
    ) -> Alert:
        membership = await self.ensure_workspace_access(workspace_id=workspace_id, user_id=user_id)
        del membership

        if self.alerts is None:
            raise FinanceProviderUnavailableError("Database session is unavailable")

        normalized_symbol = self._normalize_symbol(symbol)
        normalized_condition = condition.strip().lower()
        if normalized_condition not in {"price_above", "price_below"}:
            raise FinanceValidationError("Invalid alert condition")
        if threshold <= 0:
            raise FinanceValidationError("Alert threshold must be positive")

        existing = await self.alerts.get_active_duplicate(
            workspace_id=workspace_id,
            symbol=normalized_symbol,
            condition=normalized_condition,
            threshold=threshold,
        )
        if existing is not None:
            raise FinanceValidationError("Duplicate active alert already exists")

        alert = Alert(
            workspace_id=workspace_id,
            user_id=user_id,
            alert_type="price",
            symbol=normalized_symbol,
            condition=normalized_condition,
            threshold=threshold,
            is_active=True,
            last_triggered=None,
        )
        return await self.alerts.create(alert)

    async def deactivate_alert(self, *, workspace_id: UUID, user_id: UUID, alert_id: UUID) -> Alert:
        membership = await self.ensure_workspace_access(workspace_id=workspace_id, user_id=user_id)
        del membership

        if self.alerts is None:
            raise FinanceProviderUnavailableError("Database session is unavailable")

        alert = await self.alerts.get_by_workspace_and_id(workspace_id=workspace_id, alert_id=alert_id)
        if alert is None:
            raise FinanceNotFoundError("Alert not found")

        if alert.user_id != user_id and not await self._can_manage_alert(workspace_id=workspace_id, user_id=user_id):
            raise FinanceNotFoundError("Alert not found")

        alert.is_active = False
        return await self.alerts.update(alert)

    async def delete_alert(self, *, workspace_id: UUID, user_id: UUID, alert_id: UUID) -> None:
        membership = await self.ensure_workspace_access(workspace_id=workspace_id, user_id=user_id)
        del membership

        if self.alerts is None:
            raise FinanceProviderUnavailableError("Database session is unavailable")

        alert = await self.alerts.get_by_workspace_and_id(workspace_id=workspace_id, alert_id=alert_id)
        if alert is None:
            raise FinanceNotFoundError("Alert not found")

        if alert.user_id != user_id and not await self._can_manage_alert(workspace_id=workspace_id, user_id=user_id):
            raise FinanceNotFoundError("Alert not found")

        await self.alerts.delete(alert)

    async def _can_manage_alert(self, *, workspace_id: UUID, user_id: UUID) -> bool:
        if self.memberships is None:
            return False
        membership = await self.memberships.get_by_workspace_and_user(workspace_id=workspace_id, user_id=user_id)
        if membership is None:
            return False
        return membership.role in {MembershipRole.OWNER, MembershipRole.ADMIN}

    async def _require_membership(self, *, workspace_id: UUID, user_id: UUID):
        if self.memberships is None:
            raise FinanceProviderUnavailableError("Database session is unavailable")
        membership = await self.memberships.get_by_workspace_and_user(workspace_id=workspace_id, user_id=user_id)
        if membership is None:
            raise FinanceNotFoundError("Workspace not found")
        return membership

    async def ensure_workspace_access(self, *, workspace_id: UUID, user_id: UUID):
        """Public workspace access check for API callers that only need authorization."""
        return await self._require_membership(workspace_id=workspace_id, user_id=user_id)

    @staticmethod
    def source_metadata(provider: str, symbol: str) -> dict[str, str]:
        """Generate deterministic source metadata for callers that need plain dict output."""

        return {
            "provider": provider,
            "symbol": symbol,
            "retrieved_at": datetime.now(UTC).isoformat(),
        }
