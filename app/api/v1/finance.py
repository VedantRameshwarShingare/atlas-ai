"""Workspace-scoped finance endpoints."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUserDependency
from app.api.responses import APIResponse
from app.database.session import get_async_session
from app.schemas.finance import (
    AlertCreateRequest,
    AlertResponse,
    CompanyProfileResponse,
    FinancialMetricResponse,
    HistoricalPriceResponse,
    QuoteResponse,
    SymbolSearchResultResponse,
    WatchlistCreateRequest,
    WatchlistResponse,
)
from app.services.finance.exceptions import (
    FinanceConfigurationError,
    FinanceNotFoundError,
    FinanceProviderUnavailableError,
    FinanceRateLimitError,
    FinanceValidationError,
)
from app.services.finance.service import FinanceService

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["finance"])


def get_finance_service(session: AsyncSession = Depends(get_async_session)) -> FinanceService:
    """Provide workspace-scoped finance service dependency."""
    return FinanceService(session)


def _handle_finance_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FinanceValidationError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, FinanceNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, FinanceRateLimitError):
        return HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))
    if isinstance(exc, (FinanceProviderUnavailableError, FinanceConfigurationError)):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Finance operation failed")


def _serialize(model_cls: type, value: object) -> dict:
    """Serialize finance objects from either model instances or attribute-based objects."""
    return model_cls.model_validate(value, from_attributes=True).model_dump(mode="json")


@router.get("/finance/quote/{symbol}", response_model=APIResponse)
async def get_quote(
    workspace_id: UUID,
    symbol: str,
    current_user: CurrentUserDependency,
    service: FinanceService = Depends(get_finance_service),
) -> APIResponse:
    """Get a normalized latest quote for a workspace member."""
    try:
        await service.ensure_workspace_access(workspace_id=workspace_id, user_id=current_user.id)
        quote = await service.get_quote(symbol)
    except Exception as exc:
        raise _handle_finance_error(exc) from exc
    return APIResponse(data={"quote": _serialize(QuoteResponse, quote)})


@router.get("/finance/company/{symbol}", response_model=APIResponse)
async def get_company_profile(
    workspace_id: UUID,
    symbol: str,
    current_user: CurrentUserDependency,
    service: FinanceService = Depends(get_finance_service),
) -> APIResponse:
    """Get normalized company profile and financial metrics for a workspace member."""
    try:
        await service.ensure_workspace_access(workspace_id=workspace_id, user_id=current_user.id)
        profile = await service.get_company_profile(symbol)
        metrics = await service.get_company_financials(symbol)
    except Exception as exc:
        raise _handle_finance_error(exc) from exc
    return APIResponse(
        data={
            "profile": _serialize(CompanyProfileResponse, profile),
            "metrics": [_serialize(FinancialMetricResponse, item) for item in metrics],
        }
    )


@router.get("/finance/history/{symbol}", response_model=APIResponse)
async def get_history(
    workspace_id: UUID,
    symbol: str,
    current_user: CurrentUserDependency,
    start_date: date = Query(...),
    end_date: date = Query(...),
    service: FinanceService = Depends(get_finance_service),
) -> APIResponse:
    """Get normalized historical OHLCV for a workspace member."""
    try:
        await service.ensure_workspace_access(workspace_id=workspace_id, user_id=current_user.id)
        records = await service.get_historical_prices(symbol, start_date, end_date)
    except Exception as exc:
        raise _handle_finance_error(exc) from exc
    return APIResponse(data={"prices": [_serialize(HistoricalPriceResponse, item) for item in records]})


@router.get("/finance/search", response_model=APIResponse)
async def search_symbol(
    workspace_id: UUID,
    current_user: CurrentUserDependency,
    q: str = Query(..., min_length=1, max_length=100),
    service: FinanceService = Depends(get_finance_service),
) -> APIResponse:
    """Search symbols by query for a workspace member."""
    try:
        await service.ensure_workspace_access(workspace_id=workspace_id, user_id=current_user.id)
        results = await service.search_symbol(q)
    except Exception as exc:
        raise _handle_finance_error(exc) from exc
    return APIResponse(data={"results": [_serialize(SymbolSearchResultResponse, item) for item in results]})


@router.get("/watchlist", response_model=APIResponse)
async def list_watchlist(
    workspace_id: UUID,
    current_user: CurrentUserDependency,
    service: FinanceService = Depends(get_finance_service),
) -> APIResponse:
    """List workspace watchlist entries."""
    try:
        items = await service.list_watchlist(workspace_id=workspace_id, user_id=current_user.id)
    except Exception as exc:
        raise _handle_finance_error(exc) from exc
    return APIResponse(data={"watchlist": [_serialize(WatchlistResponse, item) for item in items]})


@router.post("/watchlist", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def add_watchlist_symbol(
    workspace_id: UUID,
    payload: WatchlistCreateRequest,
    current_user: CurrentUserDependency,
    service: FinanceService = Depends(get_finance_service),
) -> APIResponse:
    """Add a symbol to workspace watchlist."""
    try:
        item = await service.add_watchlist_symbol(
            workspace_id=workspace_id,
            user_id=current_user.id,
            symbol=payload.symbol,
        )
    except Exception as exc:
        raise _handle_finance_error(exc) from exc
    return APIResponse(data={"watchlist": _serialize(WatchlistResponse, item)})


@router.delete("/watchlist/{symbol}", response_model=APIResponse)
async def remove_watchlist_symbol(
    workspace_id: UUID,
    symbol: str,
    current_user: CurrentUserDependency,
    service: FinanceService = Depends(get_finance_service),
) -> APIResponse:
    """Remove a symbol from workspace watchlist."""
    try:
        await service.remove_watchlist_symbol(workspace_id=workspace_id, user_id=current_user.id, symbol=symbol)
    except Exception as exc:
        raise _handle_finance_error(exc) from exc
    return APIResponse(data={"symbol": symbol.upper(), "status": "removed"})


@router.get("/alerts", response_model=APIResponse)
async def list_alerts(
    workspace_id: UUID,
    current_user: CurrentUserDependency,
    service: FinanceService = Depends(get_finance_service),
) -> APIResponse:
    """List workspace alerts."""
    try:
        items = await service.list_alerts(workspace_id=workspace_id, user_id=current_user.id)
    except Exception as exc:
        raise _handle_finance_error(exc) from exc
    return APIResponse(data={"alerts": [_serialize(AlertResponse, item) for item in items]})


@router.post("/alerts", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    workspace_id: UUID,
    payload: AlertCreateRequest,
    current_user: CurrentUserDependency,
    service: FinanceService = Depends(get_finance_service),
) -> APIResponse:
    """Create workspace alert foundation record."""
    try:
        item = await service.create_alert(
            workspace_id=workspace_id,
            user_id=current_user.id,
            symbol=payload.symbol,
            condition=payload.condition,
            threshold=payload.threshold,
        )
    except Exception as exc:
        raise _handle_finance_error(exc) from exc
    return APIResponse(data={"alert": _serialize(AlertResponse, item)})


@router.patch("/alerts/{alert_id}/deactivate", response_model=APIResponse)
async def deactivate_alert(
    workspace_id: UUID,
    alert_id: UUID,
    current_user: CurrentUserDependency,
    service: FinanceService = Depends(get_finance_service),
) -> APIResponse:
    """Deactivate a workspace alert."""
    try:
        item = await service.deactivate_alert(workspace_id=workspace_id, user_id=current_user.id, alert_id=alert_id)
    except Exception as exc:
        raise _handle_finance_error(exc) from exc
    return APIResponse(data={"alert": _serialize(AlertResponse, item)})


@router.delete("/alerts/{alert_id}", response_model=APIResponse)
async def delete_alert(
    workspace_id: UUID,
    alert_id: UUID,
    current_user: CurrentUserDependency,
    service: FinanceService = Depends(get_finance_service),
) -> APIResponse:
    """Delete a workspace alert."""
    try:
        await service.delete_alert(workspace_id=workspace_id, user_id=current_user.id, alert_id=alert_id)
    except Exception as exc:
        raise _handle_finance_error(exc) from exc
    return APIResponse(data={"alert_id": str(alert_id), "status": "deleted"})
