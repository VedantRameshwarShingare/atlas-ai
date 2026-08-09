"""Integration tests for the RAG vector retrieval pipeline."""

from __future__ import annotations

import pytest

from app.rag.vector_store import ChromaVectorStore


@pytest.mark.asyncio
async def test_vector_store_returns_most_similar_chunk() -> None:
    """The vector store should rank records by cosine similarity."""

    vector_store = ChromaVectorStore(
        persist_directory=None,
    )

    await vector_store.store(
        collection="documents",
        records=[
            {
                "id": "chunk-python",
                "document_id": "doc-1",
                "text": "Python is my favorite programming language.",
                "embedding": [1.0, 0.0, 0.0],
                "metadata": {},
            },
            {
                "id": "chunk-java",
                "document_id": "doc-1",
                "text": "Java is used for enterprise applications.",
                "embedding": [0.0, 1.0, 0.0],
                "metadata": {},
            },
            {
                "id": "chunk-django",
                "document_id": "doc-1",
                "text": "Django is a Python web framework.",
                "embedding": [0.8, 0.2, 0.0],
                "metadata": {},
            },
        ],
    )

    results = await vector_store.search(
        collection="documents",
        query_embedding=[1.0, 0.0, 0.0],
        limit=2,
    )

    assert len(results) == 2
    assert results[0]["id"] == "chunk-python"
    assert results[0]["similarity"] > results[1]["similarity"]


@pytest.mark.asyncio
async def test_embedding_engine_returns_768_dimensions() -> None:
    """Embedding engine should normalize a 768-dimensional embedding."""

    from app.rag.embeddings import EmbeddingEngine

    class FakeEmbeddingService:
        async def create_embedding(
            self,
            *,
            input_text: str,
            model: str | None = None,
        ) -> list[float]:
            return [0.1] * 768

    engine = EmbeddingEngine(service=FakeEmbeddingService())

    embedding = await engine.embed_text(
        text="Python is useful for backend development.",
    )

    assert isinstance(embedding, list)
    assert len(embedding) == 768
    assert all(isinstance(value, float) for value in embedding)


@pytest.mark.asyncio
async def test_ingestion_pipeline_stores_embedded_chunks(tmp_path) -> None:
    """Ingestion should parse, chunk, embed, and store document vectors."""

    from app.rag.embeddings import EmbeddingEngine
    from app.rag.ingestion import IngestionPipeline
    from app.rag.parser import TxtParser
    from app.rag.vector_store import ChromaVectorStore

    document = tmp_path / "python.txt"
    document.write_text(
        "Python is a programming language used for backend development.\n\nDjango is a Python web framework.",
        encoding="utf-8",
    )

    class FakeEmbeddingService:
        async def create_embedding(
            self,
            *,
            input_text: str,
            model: str | None = None,
        ) -> list[float]:
            if "Django" in input_text:
                return [0.9, 0.1, 0.0]
            return [1.0, 0.0, 0.0]

    embedding_engine = EmbeddingEngine(
        service=FakeEmbeddingService(),
    )
    vector_store = ChromaVectorStore(
        persist_directory=None,
    )

    pipeline = IngestionPipeline(
        parser=TxtParser(),
        embeddings=embedding_engine,
        vector_store=vector_store,
    )

    result = await pipeline.ingest(
        file_path=str(document),
        document_id="doc-python",
    )

    assert result["document_id"] == "doc-python"
    assert result["chunks"] == 2
    assert result["stored"] is True

    records = await vector_store.search(
        collection="documents",
        query_embedding=[1.0, 0.0, 0.0],
        limit=2,
    )

    assert len(records) == 2
    assert records[0]["document_id"] == "doc-python"
    assert records[0]["embedding"] == [1.0, 0.0, 0.0]
    assert records[0]["similarity"] == 1.0


@pytest.mark.asyncio
async def test_pdf_parser_extracts_text(tmp_path) -> None:
    """PDF parser should extract text and page metadata."""

    import pymupdf

    from app.rag.parser import PdfParser

    pdf_path = tmp_path / "atlas_test.pdf"

    document = pymupdf.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        "Atlas AI is a personal AI assistant.",
    )
    document.save(pdf_path)
    document.close()

    parser = PdfParser()

    result = await parser.parse(
        file_path=str(pdf_path),
    )

    assert result["format"] == "pdf"
    assert "Atlas AI" in result["text"]
    assert "personal AI assistant" in result["text"]
    assert result["metadata"]["pages"] == 1


@pytest.mark.asyncio
async def test_rag_engine_builds_citations() -> None:
    """RAG engine should retrieve chunks and build citations."""

    from app.rag.engine import RAGEngine
    from app.rag.vector_store import ChromaVectorStore

    vector_store = ChromaVectorStore(
        persist_directory=None,
    )

    await vector_store.store(
        collection="documents",
        records=[
            {
                "id": "chunk-python",
                "document_id": "doc-python",
                "text": "Python is a programming language.",
                "embedding": [1.0, 0.0, 0.0],
                "metadata": {
                    "document": "doc-python",
                    "page": 1,
                    "source": "python.pdf",
                },
            },
        ],
    )

    class FakeEmbeddingService:
        async def create_embedding(
            self,
            *,
            input_text: str,
            model: str | None = None,
        ) -> list[float]:
            return [1.0, 0.0, 0.0]

    from app.rag.embeddings import EmbeddingEngine

    engine = RAGEngine(
        embeddings=EmbeddingEngine(service=FakeEmbeddingService()),
        vector_store=vector_store,
    )

    context = await engine.build_context(
        query="What is Python?",
    )

    assert len(context.retrieved_chunks) == 1
    assert len(context.citations) == 1

    citation = context.citations[0]

    assert citation.document == "doc-python"
    assert citation.page == 1
    assert citation.chunk_id == "chunk-python"
    assert citation.source == "python.pdf"


@pytest.mark.asyncio
async def test_retriever_filters_by_similarity_threshold() -> None:
    """Retriever should remove chunks below the similarity threshold."""

    from app.rag.retriever import Retriever

    retriever = Retriever()

    chunks = [
        {
            "chunk_id": "chunk-high",
            "document_id": "doc-1",
            "text": "Python backend development.",
            "metadata": {},
            "similarity": 0.95,
        },
        {
            "chunk_id": "chunk-medium",
            "document_id": "doc-1",
            "text": "Django web framework.",
            "metadata": {},
            "similarity": 0.75,
        },
        {
            "chunk_id": "chunk-low",
            "document_id": "doc-1",
            "text": "Java enterprise applications.",
            "metadata": {},
            "similarity": 0.40,
        },
    ]

    results = await retriever.retrieve(
        query="Python",
        chunks=chunks,
        limit=5,
        similarity_threshold=0.70,
    )

    assert len(results) == 2
    assert results[0].chunk_id == "chunk-high"
    assert results[1].chunk_id == "chunk-medium"


@pytest.mark.asyncio
async def test_retriever_sorts_by_similarity() -> None:
    """Retriever should rank chunks from highest to lowest similarity."""

    from app.rag.retriever import Retriever

    retriever = Retriever()

    chunks = [
        {
            "chunk_id": "chunk-low",
            "document_id": "doc-1",
            "text": "Low relevance.",
            "metadata": {},
            "similarity": 0.30,
        },
        {
            "chunk_id": "chunk-high",
            "document_id": "doc-1",
            "text": "High relevance.",
            "metadata": {},
            "similarity": 0.95,
        },
        {
            "chunk_id": "chunk-medium",
            "document_id": "doc-1",
            "text": "Medium relevance.",
            "metadata": {},
            "similarity": 0.65,
        },
    ]

    results = await retriever.retrieve(
        query="relevance",
        chunks=chunks,
        limit=3,
    )

    assert [result.chunk_id for result in results] == [
        "chunk-high",
        "chunk-medium",
        "chunk-low",
    ]


@pytest.mark.asyncio
async def test_retriever_filters_by_document() -> None:
    """Retriever should optionally restrict results to one document."""

    from app.rag.retriever import Retriever

    retriever = Retriever()

    chunks = [
        {
            "chunk_id": "chunk-python",
            "document_id": "doc-python",
            "text": "Python programming.",
            "metadata": {},
            "similarity": 0.95,
        },
        {
            "chunk_id": "chunk-django",
            "document_id": "doc-django",
            "text": "Django framework.",
            "metadata": {},
            "similarity": 0.90,
        },
        {
            "chunk_id": "chunk-java",
            "document_id": "doc-java",
            "text": "Java programming.",
            "metadata": {},
            "similarity": 0.85,
        },
    ]

    results = await retriever.retrieve(
        query="programming",
        chunks=chunks,
        limit=5,
        document_id="doc-python",
    )

    assert len(results) == 1
    assert results[0].chunk_id == "chunk-python"
    assert results[0].document_id == "doc-python"


@pytest.mark.asyncio
async def test_retriever_respects_limit() -> None:
    """Retriever should return no more than the requested limit."""

    from app.rag.retriever import Retriever

    retriever = Retriever()

    chunks = [
        {
            "chunk_id": f"chunk-{index}",
            "document_id": "doc-1",
            "text": f"Chunk {index}",
            "metadata": {},
            "similarity": 1.0 - (index * 0.1),
        }
        for index in range(5)
    ]

    results = await retriever.retrieve(
        query="test",
        chunks=chunks,
        limit=2,
    )

    assert len(results) == 2
    assert results[0].chunk_id == "chunk-0"
    assert results[1].chunk_id == "chunk-1"


@pytest.mark.asyncio
async def test_retriever_returns_empty_for_non_positive_limit() -> None:
    """Retriever should return no results for a non-positive limit."""

    from app.rag.retriever import Retriever

    retriever = Retriever()

    results = await retriever.retrieve(
        query="test",
        chunks=[
            {
                "chunk_id": "chunk-1",
                "document_id": "doc-1",
                "text": "Test",
                "metadata": {},
                "similarity": 1.0,
            }
        ],
        limit=0,
    )

    assert results == []


@pytest.mark.asyncio
async def test_reranker_sorts_chunks_by_similarity() -> None:
    """Reranker should order chunks from highest to lowest similarity."""

    from app.rag.reranker import Reranker

    reranker = Reranker()

    chunks = [
        {
            "chunk_id": "low",
            "similarity": 0.30,
        },
        {
            "chunk_id": "high",
            "similarity": 0.95,
        },
        {
            "chunk_id": "medium",
            "similarity": 0.70,
        },
    ]

    results = await reranker.rerank(
        chunks=chunks,
    )

    assert [chunk["chunk_id"] for chunk in results] == [
        "high",
        "medium",
        "low",
    ]


@pytest.mark.asyncio
async def test_reranker_applies_similarity_threshold() -> None:
    """Reranker should remove chunks below the threshold."""

    from app.rag.reranker import Reranker

    reranker = Reranker()

    chunks = [
        {
            "chunk_id": "high",
            "similarity": 0.95,
        },
        {
            "chunk_id": "medium",
            "similarity": 0.70,
        },
        {
            "chunk_id": "low",
            "similarity": 0.40,
        },
    ]

    results = await reranker.rerank(
        chunks=chunks,
        similarity_threshold=0.70,
    )

    assert len(results) == 2
    assert results[0]["chunk_id"] == "high"
    assert results[1]["chunk_id"] == "medium"


@pytest.mark.asyncio
async def test_reranker_respects_limit() -> None:
    """Reranker should return no more than the requested limit."""

    from app.rag.reranker import Reranker

    reranker = Reranker()

    chunks = [
        {"chunk_id": "one", "similarity": 0.95},
        {"chunk_id": "two", "similarity": 0.90},
        {"chunk_id": "three", "similarity": 0.85},
    ]

    results = await reranker.rerank(
        chunks=chunks,
        limit=2,
    )

    assert len(results) == 2
    assert [chunk["chunk_id"] for chunk in results] == [
        "one",
        "two",
    ]


@pytest.mark.asyncio
async def test_reranker_returns_empty_for_non_positive_limit() -> None:
    """Reranker should return no results for a non-positive limit."""

    from app.rag.reranker import Reranker

    reranker = Reranker()

    results = await reranker.rerank(
        chunks=[
            {
                "chunk_id": "chunk-1",
                "similarity": 1.0,
            }
        ],
        limit=0,
    )

    assert results == []
