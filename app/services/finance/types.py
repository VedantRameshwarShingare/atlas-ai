"""Normalized finance data models."""

from __future__ import annotations

from datetime import UTC, date, datetime

from pydantic import BaseModel, Field


class SourceMetadata(BaseModel):
    """Provider source metadata attached to normalized finance records."""

    provider: str
    symbol: str
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Quote(BaseModel):
    """Normalized latest quote data."""

    symbol: str
    price: float
    currency: str | None = None
    change: float | None = None
    change_percent: float | None = None
    timestamp: datetime | None = None
    source: SourceMetadata


class CompanyProfile(BaseModel):
    """Normalized company profile data."""

    symbol: str
    name: str
    exchange: str | None = None
    industry: str | None = None
    country: str | None = None
    source: SourceMetadata


class HistoricalPrice(BaseModel):
    """Normalized historical OHLCV entry."""

    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    source: SourceMetadata


class FinancialMetric(BaseModel):
    """Normalized company financial metric value."""

    symbol: str
    metric: str
    value: float
    period: str | None = None
    currency: str | None = None
    source: SourceMetadata


class SymbolSearchResult(BaseModel):
    """Normalized symbol lookup result."""

    symbol: str
    name: str
    exchange: str | None = None
    type: str | None = None
    source: SourceMetadata
