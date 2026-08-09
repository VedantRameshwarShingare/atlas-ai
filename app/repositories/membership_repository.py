"""Repository for workspace membership entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership, MembershipRole
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class MembershipRepository(BaseRepository[Membership]):
    """Repository for managing membership records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Membership)

    async def get_by_workspace_and_user(self, workspace_id: UUID, user_id: UUID) -> Membership | None:
        """Return membership for a given workspace and user."""
        result = await self.session.execute(
            select(Membership).where(
                Membership.workspace_id == workspace_id,
                Membership.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_with_users(self, workspace_id: UUID) -> list[tuple[Membership, User]]:
        """Return memberships for a workspace including user details."""
        result = await self.session.execute(
            select(Membership, User)
            .join(User, User.id == Membership.user_id)
            .where(Membership.workspace_id == workspace_id)
            .order_by(Membership.created_at.asc())
        )
        return list(result.all())

    async def count_role(self, workspace_id: UUID, role: MembershipRole) -> int:
        """Return number of members with a given role in the workspace."""
        result = await self.session.execute(
            select(Membership).where(
                Membership.workspace_id == workspace_id,
                Membership.role == role,
            )
        )
        return len(result.scalars().all())
