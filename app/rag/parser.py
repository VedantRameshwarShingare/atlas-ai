"""Document parser abstraction for text extraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseParser(ABC):
    """Base parser interface for different document formats."""

    @abstractmethod
    async def parse(self, *, file_path: str) -> dict[str, Any]:
        """Parse a document into a structured payload."""


class PdfParser(BaseParser):
    """PDF parser interface placeholder."""

    async def parse(self, *, file_path: str) -> dict[str, Any]:
        return {"file_path": file_path, "format": "pdf", "text": "", "metadata": {"pages": 0}}


class TxtParser(BaseParser):
    """Plain text parser interface placeholder."""

    async def parse(self, *, file_path: str) -> dict[str, Any]:
        return {"file_path": file_path, "format": "txt", "text": "", "metadata": {}}


class DocxParser(BaseParser):
    """DOCX parser interface placeholder."""

    async def parse(self, *, file_path: str) -> dict[str, Any]:
        return {"file_path": file_path, "format": "docx", "text": "", "metadata": {}}
