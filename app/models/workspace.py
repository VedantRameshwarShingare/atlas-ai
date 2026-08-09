"""Workspace ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampedMixin

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.conversation import Conversation
    from app.models.document import Document
    from app.models.membership import Membership
    from app.models.scheduled_job import ScheduledJob
    from app.models.watchlist import Watchlist


class Workspace(Base, TimestampedMixin):
    """Represents a collaborative workspace boundary."""

    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    memberships: Mapped[list[Membership]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    conversations: Mapped[list[Conversation]] = relationship(back_populates="workspace")
    documents: Mapped[list[Document]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    watchlists: Mapped[list[Watchlist]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    alerts: Mapped[list[Alert]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    scheduled_jobs: Mapped[list[ScheduledJob]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
