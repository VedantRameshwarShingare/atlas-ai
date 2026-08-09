"""Document parser abstraction for text extraction."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from xml.etree import ElementTree
from zipfile import ZipFile

import pymupdf


class BaseParser(ABC):
    """Base parser interface for different document formats."""

    @abstractmethod
    async def parse(self, *, file_path: str) -> dict[str, Any]:
        """Parse a document into a structured payload."""


class UnsupportedDocumentError(ValueError):
    """Raised when a document has no supported parser."""


def parser_for_file(file_path: str) -> BaseParser:
    """Return the parser appropriate for a supported document path."""
    parsers: dict[str, type[BaseParser]] = {
        ".pdf": PdfParser,
        ".txt": TxtParser,
        ".docx": DocxParser,
    }
    parser_type = parsers.get(Path(file_path).suffix.lower())
    if parser_type is None:
        raise UnsupportedDocumentError(f"Unsupported document format: {Path(file_path).suffix or 'unknown'}")
    return parser_type()


class PdfParser(BaseParser):
    """Parse PDF documents using PyMuPDF."""

    async def parse(self, *, file_path: str) -> dict[str, Any]:
        """Extract text and page metadata from a PDF document."""

        document = await asyncio.to_thread(
            pymupdf.open,
            file_path,
        )

        try:
            pages: list[str] = []
            page_texts: list[dict[str, Any]] = []

            for page_number, page in enumerate(document, start=1):
                page_text = page.get_text().strip()

                if page_text:
                    pages.append(page_text)
                    page_texts.append(
                        {
                            "page": page_number,
                            "text": page_text,
                        }
                    )

            text = "\n\n".join(pages)

            return {
                "file_path": file_path,
                "format": "pdf",
                "text": text,
                "metadata": {
                    "pages": len(document),
                    "page_texts": page_texts,
                },
            }
        finally:
            document.close()


class TxtParser(BaseParser):
    """Parse plain-text documents."""

    async def parse(self, *, file_path: str) -> dict[str, Any]:
        """Read a UTF-8 text document into a structured payload."""

        path = Path(file_path)

        text = await asyncio.to_thread(
            path.read_text,
            encoding="utf-8",
        )

        return {
            "file_path": str(path),
            "format": "txt",
            "text": text,
            "metadata": {},
        }


class DocxParser(BaseParser):
    """Extract paragraph text from DOCX files without provider dependencies."""

    async def parse(self, *, file_path: str) -> dict[str, Any]:
        """Parse a DOCX document's word-processing paragraphs."""
        path = Path(file_path)

        def _extract() -> str:
            namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            with ZipFile(path) as archive:
                root = ElementTree.fromstring(archive.read("word/document.xml"))
            paragraphs = [
                "".join(text.text or "" for text in paragraph.findall(".//w:t", namespace)).strip()
                for paragraph in root.findall(".//w:p", namespace)
            ]
            return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)

        return {
            "file_path": str(path),
            "format": "docx",
            "text": await asyncio.to_thread(_extract),
            "metadata": {},
        }
