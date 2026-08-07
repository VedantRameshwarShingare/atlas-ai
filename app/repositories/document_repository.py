"""Repository for document entities."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for managing document records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Document)
