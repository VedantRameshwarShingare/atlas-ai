"""Scheduled-job ORM model for persistent Atlas AI scheduling."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampedMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace


class ScheduledJobType(StrEnum):
    """Supported scheduled background job types."""

    DOCUMENT_PROCESSOR = "document_processor"
    MARKET_MONITOR = "market_monitor"
    WATCHLIST_MONITOR = "watchlist_monitor"
    EARNINGS_MONITOR = "earnings_monitor"
    ALERT_DISPATCHER = "alert_dispatcher"
    MORNING_BRIEF = "morning_brief"
    WORKSPACE_CLEANUP = "workspace_cleanup"
    HEALTH_CHECK = "health_check"


class ScheduledJob(Base, TimestampedMixin):
    """Persistent user- or workspace-scoped scheduled job."""

    __tablename__ = "scheduled_jobs"

    __table_args__ = (
        Index(
            "ix_scheduled_jobs_user_enabled",
            "user_id",
            "enabled",
        ),
        Index(
            "ix_scheduled_jobs_workspace_enabled",
            "workspace_id",
            "enabled",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    workspace_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    schedule: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    timezone: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="UTC",
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    user: Mapped[User] = relationship(
        back_populates="scheduled_jobs",
    )

    workspace: Mapped[Workspace | None] = relationship(
        back_populates="scheduled_jobs",
    )
