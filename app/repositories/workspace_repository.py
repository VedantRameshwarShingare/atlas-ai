"""Repository for workspace entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership
from app.models.workspace import Workspace
from app.repositories.base_repository import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    """Repository for managing workspace records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Workspace)

    async def list_for_user(self, user_id: UUID, *, offset: int = 0, limit: int = 100) -> list[Workspace]:
        """Return workspaces where the user has membership."""
        result = await self.session.execute(
            select(Workspace)
            .join(Membership, Membership.workspace_id == Workspace.id)
            .where(Membership.user_id == user_id)
            .order_by(Workspace.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_for_user(self, workspace_id: UUID, user_id: UUID) -> Workspace | None:
        """Return a workspace only if the user has membership."""
        result = await self.session.execute(
            select(Workspace)
            .join(Membership, Membership.workspace_id == Workspace.id)
            .where(Workspace.id == workspace_id, Membership.user_id == user_id)
        )
        return result.scalar_one_or_none()
