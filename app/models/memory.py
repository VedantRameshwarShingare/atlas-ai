"""Memory ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampedMixin

if TYPE_CHECKING:
    from app.models.user import User


class Memory(Base, TimestampedMixin):
    """Represents a user's stored memory entry."""

    __tablename__ = "memories"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    memory_type: Mapped[str] = mapped_column(String(50), default="fact", nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False, default=0.0)

    user: Mapped[User] = relationship(back_populates="memories")
