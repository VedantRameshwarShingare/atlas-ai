"""Watchlist ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampedMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace


class Watchlist(Base, TimestampedMixin):
    """Represents a user's watched symbol."""

    __tablename__ = "watchlists"
    __table_args__ = (UniqueConstraint("workspace_id", "symbol", name="uq_watchlists_workspace_symbol"),)

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    market: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    workspace: Mapped[Workspace] = relationship(back_populates="watchlists")
    user: Mapped[User] = relationship(back_populates="watchlists")
