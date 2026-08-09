"""Repository for alert entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.repositories.base_repository import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    """Repository for managing alert records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Alert)

    async def list_for_workspace(self, workspace_id: UUID) -> list[Alert]:
        """List alerts for a workspace sorted by newest first."""
        result = await self.session.execute(
            select(Alert).where(Alert.workspace_id == workspace_id).order_by(Alert.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_workspace_and_id(self, *, workspace_id: UUID, alert_id: UUID) -> Alert | None:
        """Get an alert only when it belongs to the workspace."""
        result = await self.session.execute(
            select(Alert).where(Alert.workspace_id == workspace_id, Alert.id == alert_id)
        )
        return result.scalar_one_or_none()

    async def get_active_duplicate(
        self,
        *,
        workspace_id: UUID,
        symbol: str,
        condition: str,
        threshold: float,
    ) -> Alert | None:
        """Return matching active alert if one already exists."""
        result = await self.session.execute(
            select(Alert).where(
                Alert.workspace_id == workspace_id,
                Alert.symbol == symbol,
                Alert.condition == condition,
                Alert.threshold == threshold,
                Alert.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()
