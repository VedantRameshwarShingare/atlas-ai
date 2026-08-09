"""Repository for watchlist entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.watchlist import Watchlist
from app.repositories.base_repository import BaseRepository


class WatchlistRepository(BaseRepository[Watchlist]):
    """Repository for managing watchlist records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Watchlist)

    async def list_for_workspace(self, workspace_id: UUID) -> list[Watchlist]:
        """List watchlist entries for a workspace sorted by symbol."""
        result = await self.session.execute(
            select(Watchlist).where(Watchlist.workspace_id == workspace_id).order_by(Watchlist.symbol.asc())
        )
        return list(result.scalars().all())

    async def get_by_workspace_and_symbol(self, *, workspace_id: UUID, symbol: str) -> Watchlist | None:
        """Return watchlist entry for a symbol within a workspace."""
        result = await self.session.execute(
            select(Watchlist).where(Watchlist.workspace_id == workspace_id, Watchlist.symbol == symbol)
        )
        return result.scalar_one_or_none()
