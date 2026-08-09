"""Repository for user entities."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for managing user records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        """Return a user by normalized account email."""
        normalized = email.strip().lower()
        result = await self.session.execute(select(User).where(User.email == normalized))
        return result.scalar_one_or_none()

    async def get_by_telegram_user_id(self, telegram_user_id: str) -> User | None:
        """Return a user by linked Telegram identity."""
        normalized = telegram_user_id.strip()
        result = await self.session.execute(select(User).where(User.telegram_user_id == normalized))
        return result.scalar_one_or_none()
