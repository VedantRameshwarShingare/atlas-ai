# RAG module

Atlas AI's RAG module ingests PDF, TXT, and DOCX documents, stores chunk embeddings in ChromaDB, and returns ranked chunks with structured citations.

## Configuration

The active settings source is `app.core.config`. Use nested environment values such as:

```env
HUGGINGFACE__API_KEY=your-token
HUGGINGFACE__EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
DATABASE__URL=postgresql+asyncpg://user:password@localhost:5432/atlas_ai
```

Embeddings use Hugging Face Inference Providers. The default `BAAI/bge-small-en-v1.5` model produces 768-dimensional vectors. Normal application tests inject deterministic fake embedding services and do not contact Hugging Face.

## Storage and ingestion

`ChromaVectorStore()` stores persistent collections below `.chroma`. Pass `persist_directory=None` only for isolated tests; this creates an ephemeral Chroma client.

The ingestion flow is:

```text
document -> parser -> semantic chunker -> embedding engine -> ChromaDB -> document store
```

Each stored record contains a chunk ID, document ID, text, embedding vector, and metadata. PDF pages are parsed independently so `page`, `source`, and `chunk_index` survive through citations. Re-ingesting a document ID replaces its prior vectors; deleting a document removes both its metadata and all associated vectors.

## Retrieval

`RAGEngine` coordinates embedding, Chroma candidate search, `Retriever` filtering, lightweight `Reranker` ordering, `CitationBuilder`, and `ContextBuilder`. It exposes `ingest`, `retrieve`, `build_context`, and `delete`.

The retriever applies optional document filtering, a similarity threshold, deterministic score ordering, and limits. The reranker performs the final lightweight score ordering and is intentionally replaceable by a future cross-encoder.

## Testing

Run RAG coverage with:

```bash
uv run pytest tests/integration/rag -v
```

The tests use ephemeral ChromaDB and fake embeddings. PDF test fixtures require PyMuPDF, while DOCX extraction reads the standard Office XML document payload and does not require a separate document-provider dependency.
