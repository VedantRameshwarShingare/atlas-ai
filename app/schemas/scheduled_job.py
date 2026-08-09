"""API schemas for persistent scheduled jobs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.scheduled_job import ScheduledJobType


class ScheduledJobCreateRequest(BaseModel):
    """Create a persistent scheduled job."""

    name: str = Field(min_length=1, max_length=255)
    job_type: ScheduledJobType
    schedule: str = Field(min_length=1, max_length=255)
    timezone: str = Field(default="UTC", min_length=1, max_length=100)
    enabled: bool = True
    payload: dict = Field(default_factory=dict)


class ScheduledJobUpdateRequest(BaseModel):
    """Update a persistent scheduled job."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    schedule: str | None = Field(default=None, min_length=1, max_length=255)
    timezone: str | None = Field(default=None, min_length=1, max_length=100)
    enabled: bool | None = None
    payload: dict | None = None


class ScheduledJobResponse(BaseModel):
    """Scheduled job API response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    workspace_id: UUID | None
    name: str
    job_type: ScheduledJobType
    schedule: str
    timezone: str
    enabled: bool
    payload: dict
    last_run_at: datetime | None
    next_run_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime
