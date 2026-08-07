"""Repository for user entities."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for managing user records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)
