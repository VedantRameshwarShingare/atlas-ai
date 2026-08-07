"""Cache service abstraction."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseService


class CacheService(BaseService):
    """Provide a simple cache interface for key/value storage."""

    name = "cache"
    description = "Wraps application cache operations"

    async def get(self, key: str) -> Any:
        """Retrieve a cached value."""
        return None

    async def set(self, key: str, value: Any, *, ttl_seconds: int | None = None) -> bool:
        """Store a cached value."""
        return True

    async def delete(self, key: str) -> bool:
        """Delete a cached value."""
        return True

    async def clear(self) -> bool:
        """Clear all cached values."""
        return True

    async def ping(self) -> dict[str, Any]:
        """Return service readiness metadata."""
        return {"service": self.name, "available": True}
