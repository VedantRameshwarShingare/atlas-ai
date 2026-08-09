"""Document persistence abstraction for the RAG pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DocumentRecord:
    """A stored document record."""

    id: str
    source_path: str
    content_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentStore:
    """Keep document metadata without introducing database logic."""

    def __init__(self) -> None:
        self._documents: dict[str, DocumentRecord] = {}

    async def save(self, *, document: DocumentRecord) -> DocumentRecord:
        """Persist a document record."""
        self._documents[document.id] = document
        return document

    async def get(self, *, document_id: str) -> DocumentRecord | None:
        """Return a document record by id."""
        return self._documents.get(document_id)

    async def list(self) -> list[DocumentRecord]:
        """List all stored documents."""
        return list(self._documents.values())

    async def delete(self, *, document_id: str) -> bool:
        """Remove a document record and report whether it existed."""
        return self._documents.pop(document_id, None) is not None
