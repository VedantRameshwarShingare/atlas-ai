"""PDF parsing service abstraction."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseService


class PdfParserService(BaseService):
    """Provide an interface for parsing PDF documents."""

    name = "pdf_parser"
    description = "Parses PDF content into text or metadata"

    async def parse(self, file_path: str) -> dict[str, Any]:
        """Parse a PDF file and return metadata."""
        return {"file_path": file_path, "source": "pdf_parser"}

    async def ping(self) -> dict[str, Any]:
        """Return service readiness metadata."""
        return {"service": self.name, "available": True}
