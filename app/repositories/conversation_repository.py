"""Repository for conversation entities."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.repositories.base_repository import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for managing conversation records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Conversation)
