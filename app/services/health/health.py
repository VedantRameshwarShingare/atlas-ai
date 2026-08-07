"""Health monitoring service abstraction."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseService


class HealthService(BaseService):
    """Provide readiness and health reporting hooks."""

    name = "health"
    description = "Reports service health and readiness"

    async def check(self) -> dict[str, Any]:
        """Return a minimal health payload."""
        return {"service": self.name, "status": "ok"}

    async def ping(self) -> dict[str, Any]:
        """Return service readiness metadata."""
        return {"service": self.name, "available": True}
