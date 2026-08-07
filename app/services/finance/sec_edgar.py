"""SEC EDGAR service abstraction."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseService


class SecEdgarService(BaseService):
    """Provide SEC filing metadata for 10-K, 10-Q, and 8-K documents."""

    name = "sec_edgar"
    description = "Wraps SEC EDGAR filing access"

    async def get_filings(self, symbol: str) -> list[dict[str, Any]]:
        """Return filing metadata for a symbol."""
        return [{"symbol": symbol, "source": "sec_edgar"}]

    async def get_filing(self, accession_number: str) -> dict[str, Any]:
        """Return filing details for a specific accession number."""
        return {"accession_number": accession_number, "source": "sec_edgar"}

    async def ping(self) -> dict[str, Any]:
        """Return service readiness metadata."""
        return {"service": self.name, "available": True}
