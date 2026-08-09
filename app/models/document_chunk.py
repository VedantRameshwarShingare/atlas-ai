"""Document chunk ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampedMixin

if TYPE_CHECKING:
    from app.models.document import Document


class DocumentChunk(Base, TimestampedMixin):
    """Represents a chunk of a document for retrieval and embeddings."""

    __tablename__ = "document_chunks"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    document: Mapped[Document] = relationship(back_populates="chunks")
