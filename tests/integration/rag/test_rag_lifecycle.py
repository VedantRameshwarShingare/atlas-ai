"""End-to-end RAG lifecycle coverage using isolated local fakes."""

from __future__ import annotations

from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from app.rag.document_store import DocumentStore
from app.rag.embeddings import EmbeddingEngine
from app.rag.engine import RAGEngine
from app.rag.ingestion import IngestionPipeline
from app.rag.parser import DocxParser, TxtParser
from app.rag.vector_store import ChromaVectorStore


class FakeEmbeddingService:
    """Deterministic embedding service that never performs network I/O."""

    async def create_embedding(self, *, input_text: str, model: str | None = None) -> list[float]:
        """Return a small vector chosen from the text content."""
        del model
        return [1.0, 0.0, 0.0] if "Python" in input_text else [0.0, 1.0, 0.0]


@pytest.mark.asyncio
async def test_docx_parser_extracts_paragraphs(tmp_path) -> None:
    """DOCX extraction returns textual paragraphs without external services."""
    document = tmp_path / "atlas.docx"
    document_xml = (
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>Atlas AI</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>retrieves documents.</w:t></w:r></w:p></w:body></w:document>"
    )
    with ZipFile(document, "w", ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", document_xml)

    result = await DocxParser().parse(file_path=str(document))

    assert result["format"] == "docx"
    assert result["text"] == "Atlas AI\n\nretrieves documents."


@pytest.mark.asyncio
async def test_reingestion_and_deletion_leave_no_orphaned_vectors(tmp_path) -> None:
    """Re-ingestion replaces chunks and deletion removes vectors plus metadata."""
    document = tmp_path / "atlas.txt"
    document.write_text("Python retrieval", encoding="utf-8")
    vector_store = ChromaVectorStore(persist_directory=None)
    document_store = DocumentStore()
    pipeline = IngestionPipeline(
        parser=TxtParser(),
        embeddings=EmbeddingEngine(service=FakeEmbeddingService()),
        vector_store=vector_store,
        document_store=document_store,
    )

    await pipeline.ingest(file_path=str(document), document_id="atlas")
    document.write_text("Other topic", encoding="utf-8")
    await pipeline.ingest(file_path=str(document), document_id="atlas")
    records = await vector_store.search(collection="documents", query_embedding=[1.0, 0.0, 0.0])

    assert len(records) == 1
    assert records[0]["text"] == "Other topic"
    assert await pipeline.delete(document_id="atlas") is True
    assert await document_store.get(document_id="atlas") is None
    assert await vector_store.search(collection="documents", query_embedding=[1.0, 0.0, 0.0]) == []


@pytest.mark.asyncio
async def test_engine_uses_full_retrieval_flow_and_metadata(tmp_path) -> None:
    """The engine filters, reranks, and builds citations from stored chunk metadata."""
    document = tmp_path / "atlas.txt"
    document.write_text("Python retrieval\n\nOther topic", encoding="utf-8")
    vector_store = ChromaVectorStore(persist_directory=None)
    engine = RAGEngine(
        embeddings=EmbeddingEngine(service=FakeEmbeddingService()),
        vector_store=vector_store,
    )

    await engine.ingest(file_path=str(document), document_id="atlas", metadata={"source": "upload"})
    context = await engine.build_context(query="Python")

    assert len(context.retrieved_chunks) == 2
    assert context.retrieved_chunks[0]["chunk_id"] == "atlas:chunk:0"
    assert context.citations[0].document == "atlas"
    assert context.citations[0].source == str(document)
