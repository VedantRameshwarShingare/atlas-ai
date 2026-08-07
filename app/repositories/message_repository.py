"""Repository for message entities."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.repositories.base_repository import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Repository for managing message records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Message)
