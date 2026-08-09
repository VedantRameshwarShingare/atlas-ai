"""Citation generation for retrieved chunks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Citation:
    """Structured citation payload for a retrieved chunk."""

    document: str
    page: int | None = None
    chunk_id: str | None = None
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class CitationBuilder:
    """Create structured citations from retrieved chunks."""

    async def build(self, *, chunk: Any) -> Citation:
        """Construct a citation containing document, page, chunk id, and source."""

        if isinstance(chunk, dict):
            metadata = chunk.get("metadata", {}) or {}
            chunk_id = chunk.get("chunk_id", chunk.get("id"))
            document_id = chunk.get("document_id")
        else:
            metadata = getattr(chunk, "metadata", {}) or {}
            chunk_id = getattr(chunk, "chunk_id", None)
            document_id = getattr(chunk, "document_id", None)

        return Citation(
            document=str(metadata.get("document") or document_id or "unknown"),
            page=metadata.get("page"),
            chunk_id=chunk_id,
            source=metadata.get("source"),
            metadata=metadata,
        )
