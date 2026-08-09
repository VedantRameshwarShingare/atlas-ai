"""Repository for message entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.repositories.base_repository import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Repository for managing message records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Message)

    async def list_by_conversation(
        self,
        conversation_id: UUID,
        *,
        limit: int = 50,
    ) -> list[Message]:
        """Return recent messages for a conversation in chronological order."""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit)
        )

        messages = list(result.scalars().all())
        messages.reverse()
        return messages
