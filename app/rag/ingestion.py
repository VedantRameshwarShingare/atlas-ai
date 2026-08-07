"""Document ingestion pipeline for the RAG engine."""

from __future__ import annotations

from typing import Any

from app.rag.chunker import SemanticChunker
from app.rag.document_store import DocumentRecord, DocumentStore
from app.rag.embeddings import EmbeddingEngine
from app.rag.parser import BaseParser, DocxParser, PdfParser, TxtParser
from app.rag.vector_store import VectorStore


class IngestionPipeline:
    """Coordinate parse, extract, chunk, embed, and store flow for document ingestion."""

    def __init__(
        self,
        *,
        parser: BaseParser | None = None,
        chunker: SemanticChunker | None = None,
        embeddings: EmbeddingEngine | None = None,
        vector_store: VectorStore | None = None,
        document_store: DocumentStore | None = None,
    ) -> None:
        self._parser = parser or PdfParser()
        self._chunker = chunker or SemanticChunker()
        self._embeddings = embeddings or EmbeddingEngine()
        self._vector_store = vector_store
        self._document_store = document_store or DocumentStore()

    async def ingest(self, *, file_path: str, document_id: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """Run the full ingestion pipeline for a document."""
        parsed = await self._parser.parse(file_path=file_path)
        document_id = document_id or f"doc:{file_path}"
        document_record = DocumentRecord(id=document_id, source_path=file_path, content_type=str(parsed.get("format", "unknown")), metadata=metadata or {})
        await self._document_store.save(document=document_record)
        chunks = await self._chunker.chunk(document_id=document_id, text=str(parsed.get("text", "")), metadata={"document": document_id, "source": file_path})
        records = []
        for chunk in chunks:
            embedding = await self._embeddings.embed_text(text=chunk.text)
            records.append({"id": chunk.id, "document_id": chunk.document_id, "text": chunk.text, "metadata": {**chunk.metadata, **{"embedding_model": embedding.get("model")}}})
        if self._vector_store is not None:
            await self._vector_store.store(collection="documents", records=records)
        return {"document_id": document_id, "chunks": len(chunks), "stored": self._vector_store is not None}
