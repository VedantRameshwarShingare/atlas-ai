"""Repository for alert entities."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.repositories.base_repository import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    """Repository for managing alert records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Alert)
