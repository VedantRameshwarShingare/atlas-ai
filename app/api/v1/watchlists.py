"""Watchlist endpoints for the API layer."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.responses import APIResponse

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


@router.get("", response_model=APIResponse)
async def list_watchlists() -> APIResponse:
    """List watchlists without business logic."""
    return APIResponse(data={"watchlists": []})


@router.post("", response_model=APIResponse)
async def create_watchlist() -> APIResponse:
    """Create a watchlist placeholder response."""
    return APIResponse(data={"status": "created"})


@router.delete("/{symbol}", response_model=APIResponse)
async def delete_watchlist(symbol: str) -> APIResponse:
    """Delete a watchlist entry placeholder response."""
    return APIResponse(data={"symbol": symbol, "status": "deleted"})
