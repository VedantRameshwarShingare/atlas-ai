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
        metadata = getattr(chunk, "metadata", {}) or {}
        return Citation(
            document=str(metadata.get("document", "unknown")),
            page=metadata.get("page"),
            chunk_id=getattr(chunk, "chunk_id", None),
            source=metadata.get("source"),
            metadata=metadata,
        )
