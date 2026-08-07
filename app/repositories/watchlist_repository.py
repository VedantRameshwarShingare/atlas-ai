"""Repository for watchlist entities."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.watchlist import Watchlist
from app.repositories.base_repository import BaseRepository


class WatchlistRepository(BaseRepository[Watchlist]):
    """Repository for managing watchlist records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Watchlist)
