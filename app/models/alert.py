"""Alert ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampedMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace


class Alert(Base, TimestampedMixin):
    """Represents a user-defined alert for market events."""

    __tablename__ = "alerts"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(50), default="price", nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    condition: Mapped[str] = mapped_column(String(32), nullable=False)
    threshold: Mapped[float] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column("is_enabled", Boolean, default=True, nullable=False)
    last_triggered: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workspace: Mapped[Workspace] = relationship(back_populates="alerts")
    user: Mapped[User] = relationship(back_populates="alerts")
