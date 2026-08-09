"""Repository for conversation entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.repositories.base_repository import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for managing conversation records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Conversation)

    async def get_latest_for_user(self, user_id: UUID, *, title: str | None = None) -> Conversation | None:
        """Return the newest conversation for a user, optionally filtered by title."""
        statement = select(Conversation).where(Conversation.user_id == user_id)
        if title is not None:
            statement = statement.where(Conversation.title == title)
        statement = statement.order_by(Conversation.updated_at.desc(), Conversation.created_at.desc()).limit(1)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
