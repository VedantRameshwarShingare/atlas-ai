"""Text extraction service abstraction."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseService


class TextExtractorService(BaseService):
    """Provide an interface for extracting text from documents."""

    name = "text_extractor"
    description = "Extracts text from supported document formats"

    async def extract(self, file_path: str) -> dict[str, Any]:
        """Extract text from a file path."""
        return {"file_path": file_path, "source": "text_extractor"}

    async def ping(self) -> dict[str, Any]:
        """Return service readiness metadata."""
        return {"service": self.name, "available": True}
