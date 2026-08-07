"""RAG subsystem package for Atlas AI."""

from app.rag.chunker import Chunk, SemanticChunker
from app.rag.citation import Citation, CitationBuilder
from app.rag.context_builder import ContextBuilder, RAGContext
from app.rag.document_store import DocumentRecord, DocumentStore
from app.rag.embeddings import EmbeddingEngine
from app.rag.engine import RAGEngine
from app.rag.ingestion import IngestionPipeline
from app.rag.parser import BaseParser, DocxParser, PdfParser, TxtParser
from app.rag.reranker import Reranker
from app.rag.retriever import RetrievedChunk, Retriever
from app.rag.vector_store import ChromaVectorStore, VectorStore

__all__ = [
    "Chunk",
    "SemanticChunker",
    "Citation",
    "CitationBuilder",
    "ContextBuilder",
    "RAGContext",
    "DocumentRecord",
    "DocumentStore",
    "EmbeddingEngine",
    "RAGEngine",
    "IngestionPipeline",
    "BaseParser",
    "DocxParser",
    "PdfParser",
    "TxtParser",
    "Reranker",
    "RetrievedChunk",
    "Retriever",
    "ChromaVectorStore",
    "VectorStore",
]
