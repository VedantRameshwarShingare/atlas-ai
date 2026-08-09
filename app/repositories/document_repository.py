"""Repository for document entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for managing document records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Document)

    async def list_for_workspace(self, workspace_id: UUID, *, offset: int = 0, limit: int = 100) -> list[Document]:
        """Return documents scoped to a workspace ordered by newest first."""
        result = await self.session.execute(
            select(Document)
            .where(Document.workspace_id == workspace_id)
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_workspace_and_id(self, workspace_id: UUID, document_id: UUID) -> Document | None:
        """Return a document when it belongs to the specified workspace."""
        result = await self.session.execute(
            select(Document).where(Document.workspace_id == workspace_id, Document.id == document_id)
        )
        return result.scalar_one_or_none()
