"""User ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampedMixin

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.conversation import Conversation
    from app.models.document import Document
    from app.models.membership import Membership
    from app.models.memory import Memory
    from app.models.research_session import ResearchSession
    from app.models.scheduled_job import ScheduledJob
    from app.models.watchlist import Watchlist


class User(Base, TimestampedMixin):
    """Represents a registered application user."""

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("telegram_user_id", name="uq_users_telegram_user_id"),)

    # Email/password are nullable to preserve legacy Telegram-only records.
    email: Mapped[str | None] = mapped_column(String(320), nullable=True, unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(20), default="en", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    conversations: Mapped[list[Conversation]] = relationship(back_populates="user", cascade="all, delete-orphan")
    documents: Mapped[list[Document]] = relationship(back_populates="user", cascade="all, delete-orphan")
    watchlists: Mapped[list[Watchlist]] = relationship(back_populates="user", cascade="all, delete-orphan")
    alerts: Mapped[list[Alert]] = relationship(back_populates="user", cascade="all, delete-orphan")
    memories: Mapped[list[Memory]] = relationship(back_populates="user", cascade="all, delete-orphan")
    research_sessions: Mapped[list[ResearchSession]] = relationship(back_populates="user", cascade="all, delete-orphan")
    memberships: Mapped[list[Membership]] = relationship(back_populates="user", cascade="all, delete-orphan")
    scheduled_jobs: Mapped[list[ScheduledJob]] = relationship(back_populates="user", cascade="all, delete-orphan")
