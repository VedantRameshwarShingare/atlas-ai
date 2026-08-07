"""Standardized response models for the FastAPI layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    """Standard success envelope for API responses."""

    success: bool = True
    data: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: str | None = None


class APIErrorResponse(BaseModel):
    """Standard error envelope for API responses."""

    success: bool = False
    error: str
    message: str
    details: list[Any] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: str | None = None
