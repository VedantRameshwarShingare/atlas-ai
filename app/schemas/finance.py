"""Finance, watchlist, and alert API schemas."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SourceMetadataResponse(BaseModel):
    """Public source metadata for finance responses."""

    provider: str
    symbol: str
    retrieved_at: datetime


class QuoteResponse(BaseModel):
    """Public normalized quote response."""

    symbol: str
    price: float
    currency: str | None = None
    change: float | None = None
    change_percent: float | None = None
    timestamp: datetime | None = None
    source: SourceMetadataResponse


class CompanyProfileResponse(BaseModel):
    """Public normalized company profile response."""

    symbol: str
    name: str
    exchange: str | None = None
    industry: str | None = None
    country: str | None = None
    source: SourceMetadataResponse


class FinancialMetricResponse(BaseModel):
    """Public normalized company financial metric response."""

    symbol: str
    metric: str
    value: float
    period: str | None = None
    currency: str | None = None
    source: SourceMetadataResponse


class HistoricalPriceResponse(BaseModel):
    """Public normalized historical OHLCV response entry."""

    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    source: SourceMetadataResponse


class SymbolSearchResultResponse(BaseModel):
    """Public normalized symbol search result."""

    symbol: str
    name: str
    exchange: str | None = None
    type: str | None = None
    source: SourceMetadataResponse


class WatchlistCreateRequest(BaseModel):
    """Request payload to add a symbol to watchlist."""

    symbol: str = Field(min_length=1, max_length=12)


class WatchlistResponse(BaseModel):
    """Watchlist API response model."""

    id: UUID
    workspace_id: UUID
    user_id: UUID
    symbol: str
    company_name: str | None = None
    market: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AlertCreateRequest(BaseModel):
    """Request payload to create an alert foundation record."""

    symbol: str = Field(min_length=1, max_length=12)
    condition: str = Field(min_length=1, max_length=32)
    threshold: float = Field(gt=0)


class AlertResponse(BaseModel):
    """Alert API response model."""

    id: UUID
    workspace_id: UUID
    user_id: UUID
    symbol: str
    condition: str
    threshold: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
