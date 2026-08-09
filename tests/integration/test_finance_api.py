"""Finance API integration tests with fake providers and no network I/O."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.main import app
from app.services.finance.exceptions import FinanceNotFoundError, FinanceValidationError
from app.services.finance.types import (
    CompanyProfile,
    FinancialMetric,
    HistoricalPrice,
    Quote,
    SourceMetadata,
    SymbolSearchResult,
)


@dataclass
class _WatchlistItem:
    id: UUID
    workspace_id: UUID
    user_id: UUID
    symbol: str
    company_name: str | None
    market: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class _AlertItem:
    id: UUID
    workspace_id: UUID
    user_id: UUID
    symbol: str
    condition: str
    threshold: float
    is_active: bool
    created_at: datetime
    updated_at: datetime


class _FakeFinanceService:
    def __init__(self) -> None:
        self.members: dict[UUID, set[UUID]] = {}
        self.watchlist_by_workspace: dict[UUID, list[_WatchlistItem]] = {}
        self.alerts_by_workspace: dict[UUID, list[_AlertItem]] = {}

    async def ensure_workspace_access(self, *, workspace_id: UUID, user_id: UUID) -> dict[str, str]:
        if user_id not in self.members.get(workspace_id, set()):
            raise FinanceNotFoundError("Workspace not found")
        return {"workspace_id": str(workspace_id), "user_id": str(user_id)}

    async def get_quote(self, symbol: str) -> Quote:
        symbol = symbol.strip().upper()
        if not symbol:
            raise FinanceValidationError("Symbol is required")
        source = SourceMetadata(provider="test", symbol=symbol)
        return Quote(symbol=symbol, price=123.45, currency="USD", change=1.0, change_percent=0.8, source=source)

    async def get_company_profile(self, symbol: str) -> CompanyProfile:
        symbol = symbol.strip().upper()
        source = SourceMetadata(provider="test", symbol=symbol)
        return CompanyProfile(symbol=symbol, name=f"{symbol} Corp", exchange="NASDAQ", source=source)

    async def get_company_financials(self, symbol: str) -> list[FinancialMetric]:
        symbol = symbol.strip().upper()
        source = SourceMetadata(provider="test", symbol=symbol)
        return [FinancialMetric(symbol=symbol, metric="market_cap", value=1_000_000.0, source=source)]

    async def get_historical_prices(self, symbol: str, start_date: date, end_date: date) -> list[HistoricalPrice]:
        symbol = symbol.strip().upper()
        source = SourceMetadata(provider="test", symbol=symbol)
        return [
            HistoricalPrice(
                symbol=symbol,
                date=start_date,
                open=100.0,
                high=110.0,
                low=95.0,
                close=108.0,
                volume=1000,
                source=source,
            ),
            HistoricalPrice(
                symbol=symbol,
                date=end_date,
                open=108.0,
                high=115.0,
                low=105.0,
                close=112.0,
                volume=1200,
                source=source,
            ),
        ]

    async def search_symbol(self, query: str) -> list[SymbolSearchResult]:
        source = SourceMetadata(provider="test", symbol="ATLS")
        return [SymbolSearchResult(symbol="ATLS", name=f"{query} Holdings", exchange="NYSE", source=source)]

    async def list_watchlist(self, *, workspace_id: UUID, user_id: UUID) -> list[_WatchlistItem]:
        await self.ensure_workspace_access(workspace_id=workspace_id, user_id=user_id)
        return list(self.watchlist_by_workspace.get(workspace_id, []))

    async def add_watchlist_symbol(self, *, workspace_id: UUID, user_id: UUID, symbol: str) -> _WatchlistItem:
        await self.ensure_workspace_access(workspace_id=workspace_id, user_id=user_id)
        normalized = symbol.strip().upper()
        now = datetime.now(UTC)
        item = _WatchlistItem(
            id=uuid4(),
            workspace_id=workspace_id,
            user_id=user_id,
            symbol=normalized,
            company_name=f"{normalized} Corp",
            market="NASDAQ",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        items = self.watchlist_by_workspace.setdefault(workspace_id, [])
        if any(existing.symbol == normalized for existing in items):
            raise FinanceValidationError("Symbol already exists in watchlist")
        items.append(item)
        return item

    async def remove_watchlist_symbol(self, *, workspace_id: UUID, user_id: UUID, symbol: str) -> None:
        await self.ensure_workspace_access(workspace_id=workspace_id, user_id=user_id)
        normalized = symbol.strip().upper()
        items = self.watchlist_by_workspace.setdefault(workspace_id, [])
        remaining = [item for item in items if item.symbol != normalized]
        if len(remaining) == len(items):
            raise FinanceNotFoundError("Watchlist symbol not found")
        self.watchlist_by_workspace[workspace_id] = remaining

    async def list_alerts(self, *, workspace_id: UUID, user_id: UUID) -> list[_AlertItem]:
        await self.ensure_workspace_access(workspace_id=workspace_id, user_id=user_id)
        return list(self.alerts_by_workspace.get(workspace_id, []))

    async def create_alert(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
        symbol: str,
        condition: str,
        threshold: float,
    ) -> _AlertItem:
        await self.ensure_workspace_access(workspace_id=workspace_id, user_id=user_id)
        now = datetime.now(UTC)
        item = _AlertItem(
            id=uuid4(),
            workspace_id=workspace_id,
            user_id=user_id,
            symbol=symbol.strip().upper(),
            condition=condition,
            threshold=threshold,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self.alerts_by_workspace.setdefault(workspace_id, []).append(item)
        return item

    async def deactivate_alert(self, *, workspace_id: UUID, user_id: UUID, alert_id: UUID) -> _AlertItem:
        await self.ensure_workspace_access(workspace_id=workspace_id, user_id=user_id)
        for alert in self.alerts_by_workspace.get(workspace_id, []):
            if alert.id == alert_id:
                alert.is_active = False
                alert.updated_at = datetime.now(UTC)
                return alert
        raise FinanceNotFoundError("Alert not found")

    async def delete_alert(self, *, workspace_id: UUID, user_id: UUID, alert_id: UUID) -> None:
        await self.ensure_workspace_access(workspace_id=workspace_id, user_id=user_id)
        alerts = self.alerts_by_workspace.get(workspace_id, [])
        self.alerts_by_workspace[workspace_id] = [alert for alert in alerts if alert.id != alert_id]


@pytest.fixture(autouse=True)
def configure_auth_settings() -> None:
    """Use deterministic JWT settings for finance API tests."""
    original_secret = settings.auth.jwt_secret_key
    original_algorithm = settings.auth.jwt_algorithm
    original_expire_minutes = settings.auth.access_token_expire_minutes

    settings.auth.jwt_secret_key = SecretStr("finance-test-jwt-secret-key-32-bytes")
    settings.auth.jwt_algorithm = "HS256"
    settings.auth.access_token_expire_minutes = 60
    try:
        yield
    finally:
        settings.auth.jwt_secret_key = original_secret
        settings.auth.jwt_algorithm = original_algorithm
        settings.auth.access_token_expire_minutes = original_expire_minutes


@pytest.fixture(autouse=True)
async def ensure_workspace_schema_compatibility(db_session: AsyncSession) -> None:
    """Support local test DBs that have not applied the latest migration head."""
    await db_session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(320)"))
    await db_session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)"))
    await db_session.execute(text("ALTER TABLE users ALTER COLUMN telegram_user_id DROP NOT NULL"))
    await db_session.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))

    await db_session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS workspaces (
                id UUID PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                name VARCHAR(255) NOT NULL,
                description VARCHAR(1000)
            )
            """
        )
    )
    await db_session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS memberships (
                id UUID PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id),
                role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'admin', 'member')),
                CONSTRAINT uq_memberships_workspace_user UNIQUE (workspace_id, user_id)
            )
            """
        )
    )
    await db_session.commit()


async def _register_and_login(client: AsyncClient, email: str, password: str = "SecurePass123") -> dict[str, str]:
    register = await client.post("/auth/register", json={"email": email, "password": password})
    assert register.status_code == 201
    token = register.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_finance_endpoints_require_workspace_membership(api_client: AsyncClient) -> None:
    """Finance endpoints are available to members and hidden for non-members."""
    owner_headers = await _register_and_login(api_client, f"owner-{uuid4().hex}@example.com")
    outsider_headers = await _register_and_login(api_client, f"outsider-{uuid4().hex}@example.com")

    workspace_response = await api_client.post("/workspaces", headers=owner_headers, json={"name": "Finance WS"})
    assert workspace_response.status_code == 201
    workspace_id = UUID(workspace_response.json()["data"]["workspace"]["id"])

    owner_me = await api_client.get("/auth/me", headers=owner_headers)
    outsider_me = await api_client.get("/auth/me", headers=outsider_headers)
    owner_id = UUID(owner_me.json()["id"])
    outsider_id = UUID(outsider_me.json()["id"])

    fake_service = _FakeFinanceService()
    fake_service.members[workspace_id] = {owner_id}

    from app.api.v1.finance import get_finance_service

    app.dependency_overrides[get_finance_service] = lambda: fake_service
    try:
        owner_quote = await api_client.get(f"/workspaces/{workspace_id}/finance/quote/AAPL", headers=owner_headers)
        outsider_quote = await api_client.get(
            f"/workspaces/{workspace_id}/finance/quote/AAPL", headers=outsider_headers
        )

        assert owner_quote.status_code == 200
        assert owner_quote.json()["data"]["quote"]["symbol"] == "AAPL"
        assert outsider_quote.status_code == 404
        assert outsider_id not in fake_service.members[workspace_id]
    finally:
        app.dependency_overrides.pop(get_finance_service, None)


@pytest.mark.asyncio
async def test_finance_watchlist_and_alert_crud(api_client: AsyncClient) -> None:
    """Watchlist and alert CRUD use workspace-scoped routes and normalized payloads."""
    owner_headers = await _register_and_login(api_client, f"owner2-{uuid4().hex}@example.com")

    workspace_response = await api_client.post("/workspaces", headers=owner_headers, json={"name": "Finance CRUD WS"})
    workspace_id = UUID(workspace_response.json()["data"]["workspace"]["id"])

    owner_me = await api_client.get("/auth/me", headers=owner_headers)
    owner_id = UUID(owner_me.json()["id"])

    fake_service = _FakeFinanceService()
    fake_service.members[workspace_id] = {owner_id}

    from app.api.v1.finance import get_finance_service

    app.dependency_overrides[get_finance_service] = lambda: fake_service
    try:
        add_watchlist = await api_client.post(
            f"/workspaces/{workspace_id}/watchlist",
            headers=owner_headers,
            json={"symbol": "msft"},
        )
        assert add_watchlist.status_code == 201
        assert add_watchlist.json()["data"]["watchlist"]["symbol"] == "MSFT"

        list_watchlist = await api_client.get(f"/workspaces/{workspace_id}/watchlist", headers=owner_headers)
        assert list_watchlist.status_code == 200
        assert len(list_watchlist.json()["data"]["watchlist"]) == 1

        create_alert = await api_client.post(
            f"/workspaces/{workspace_id}/alerts",
            headers=owner_headers,
            json={"symbol": "MSFT", "condition": "price_above", "threshold": 100},
        )
        assert create_alert.status_code == 201
        alert_id = create_alert.json()["data"]["alert"]["id"]

        deactivate_alert = await api_client.patch(
            f"/workspaces/{workspace_id}/alerts/{alert_id}/deactivate",
            headers=owner_headers,
        )
        assert deactivate_alert.status_code == 200
        assert deactivate_alert.json()["data"]["alert"]["is_active"] is False

        delete_alert = await api_client.delete(f"/workspaces/{workspace_id}/alerts/{alert_id}", headers=owner_headers)
        assert delete_alert.status_code == 200

        remove_watchlist = await api_client.delete(f"/workspaces/{workspace_id}/watchlist/MSFT", headers=owner_headers)
        assert remove_watchlist.status_code == 200
    finally:
        app.dependency_overrides.pop(get_finance_service, None)
