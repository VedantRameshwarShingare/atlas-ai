"""Modular RAG engine coordinating ingestion, retrieval, reranking, and context building."""

from __future__ import annotations

from typing import Any

from app.rag.chunker import SemanticChunker
from app.rag.citation import CitationBuilder
from app.rag.context_builder import ContextBuilder
from app.rag.document_store import DocumentStore
from app.rag.embeddings import EmbeddingEngine
from app.rag.ingestion import IngestionPipeline
from app.rag.parser import BaseParser
from app.rag.reranker import Reranker
from app.rag.retriever import Retriever
from app.rag.vector_store import ChromaVectorStore, VectorStore


class RAGEngine:
    """Coordinate the RAG pipeline without calling OpenAI directly."""

    def __init__(
        self,
        *,
        parser: BaseParser | None = None,
        chunker: SemanticChunker | None = None,
        embeddings: EmbeddingEngine | None = None,
        vector_store: VectorStore | None = None,
        document_store: DocumentStore | None = None,
        retriever: Retriever | None = None,
        reranker: Reranker | None = None,
        citation_builder: CitationBuilder | None = None,
        context_builder: ContextBuilder | None = None,
    ) -> None:
        self._parser = parser
        self._chunker = chunker or SemanticChunker()
        self._embeddings = embeddings or EmbeddingEngine()
        self._vector_store = vector_store or ChromaVectorStore()
        self._document_store = document_store or DocumentStore()
        self._retriever = retriever or Retriever()
        self._reranker = reranker or Reranker()
        self._citation_builder = citation_builder or CitationBuilder()
        self._context_builder = context_builder or ContextBuilder()

        self._ingestion_pipeline = IngestionPipeline(
            parser=self._parser,
            chunker=self._chunker,
            embeddings=self._embeddings,
            vector_store=self._vector_store,
            document_store=self._document_store,
        )

    async def ingest(
        self,
        *,
        file_path: str,
        document_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Ingest a document into the RAG pipeline."""

        return await self._ingestion_pipeline.ingest(
            file_path=file_path,
            document_id=document_id,
            metadata=metadata,
        )

    async def retrieve(
        self,
        *,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.0,
        document_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve, filter, and rerank document chunks."""

        if self._vector_store is None or limit <= 0 or not query.strip():
            return []

        query_embedding = await self._embeddings.embed_text(text=query)

        records = await self._vector_store.search(
            collection="documents",
            query_embedding=query_embedding,
            limit=limit,
        )
        retrieved = await self._retriever.retrieve(
            query=query,
            chunks=records,
            limit=limit,
            similarity_threshold=similarity_threshold,
            document_id=document_id,
        )
        ranked = await self._reranker.rerank(chunks=retrieved, limit=limit)
        return [
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
                "similarity": chunk.similarity,
            }
            for chunk in ranked
        ]

    async def delete(self, *, document_id: str) -> bool:
        """Delete a document and all vectors created during its ingestion."""
        return await self._ingestion_pipeline.delete(document_id=document_id)

    async def build_context(
        self,
        *,
        memory_context: str = "",
        conversation: list[Any] | None = None,
        workspace: list[Any] | None = None,
        capability_results: list[Any] | None = None,
        query: str | None = None,
    ) -> Any:
        """Build a single context object from retrieved and auxiliary context."""

        retrieved_chunks = await self.retrieve(query=query or "", limit=5) if query is not None else []

        citations = [await self._citation_builder.build(chunk=chunk) for chunk in retrieved_chunks]

        return await self._context_builder.build(
            memory_context=memory_context,
            retrieved_chunks=retrieved_chunks,
            conversation=conversation,
            workspace=workspace,
            capability_results=capability_results,
            citations=citations,
        )
