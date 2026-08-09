"""Persistent ChromaDB vector store for the RAG pipeline."""

from __future__ import annotations

import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import chromadb


class VectorStore(ABC):
    """Interface for storing and retrieving vector embeddings."""

    @abstractmethod
    async def store(
        self,
        *,
        collection: str,
        records: list[dict[str, Any]],
    ) -> None:
        """Store vector records."""

    @abstractmethod
    async def update(
        self,
        *,
        collection: str,
        record_id: str,
        values: dict[str, Any],
    ) -> None:
        """Update a vector record."""

    @abstractmethod
    async def delete(
        self,
        *,
        collection: str,
        record_id: str,
    ) -> None:
        """Delete a vector record."""

    @abstractmethod
    async def delete_document(self, *, collection: str, document_id: str) -> None:
        """Delete every vector belonging to a document."""

    @abstractmethod
    async def search(
        self,
        *,
        collection: str,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search vector records by similarity."""


class ChromaVectorStore(VectorStore):
    """Persistent vector store backed by ChromaDB."""

    def __init__(
        self,
        *,
        persist_directory: str | None = ".chroma",
    ) -> None:
        if persist_directory is None:
            self._client = chromadb.EphemeralClient()
            self._collection_prefix = f"test_{uuid.uuid4().hex}"
        else:
            self._client = chromadb.PersistentClient(
                path=str(Path(persist_directory)),
            )
            self._collection_prefix = ""

    def _get_collection(self, name: str) -> Any:
        """Return or create a ChromaDB collection."""

        collection_name = f"{self._collection_prefix}_{name}" if self._collection_prefix else name

        return self._client.get_or_create_collection(
            name=collection_name,
            configuration={"hnsw": {"space": "cosine"}},
        )

    async def store(
        self,
        *,
        collection: str,
        records: list[dict[str, Any]],
    ) -> None:
        """Store vector records in ChromaDB."""

        if not records:
            return

        def _store() -> None:
            chroma_collection = self._get_collection(collection)

            chroma_collection.upsert(
                ids=[str(record["id"]) for record in records],
                embeddings=[[float(value) for value in record["embedding"]] for record in records],
                documents=[str(record.get("text", "")) for record in records],
                metadatas=[
                    {
                        "document_id": str(record.get("document_id", "")),
                        "metadata": json.dumps(record.get("metadata", {})),
                    }
                    for record in records
                ],
            )

        await asyncio.to_thread(_store)

    async def update(
        self,
        *,
        collection: str,
        record_id: str,
        values: dict[str, Any],
    ) -> None:
        """Update an existing vector record."""

        def _update() -> None:
            chroma_collection = self._get_collection(collection)

            existing = chroma_collection.get(
                ids=[record_id],
                include=["embeddings", "documents", "metadatas"],
            )

            if not existing["ids"]:
                return

            embedding = existing["embeddings"][0]
            document = existing["documents"][0] or ""
            metadata = existing["metadatas"][0] or {}

            if "embedding" in values:
                embedding = values["embedding"]

            if "text" in values:
                document = str(values["text"])

            record_metadata = dict(metadata)

            if "document_id" in values:
                record_metadata["document_id"] = str(values["document_id"])

            if "metadata" in values:
                record_metadata["metadata"] = json.dumps(values["metadata"])

            chroma_collection.upsert(
                ids=[record_id],
                embeddings=[embedding],
                documents=[document],
                metadatas=[record_metadata],
            )

        await asyncio.to_thread(_update)

    async def delete(
        self,
        *,
        collection: str,
        record_id: str,
    ) -> None:
        """Delete a vector record from ChromaDB."""

        def _delete() -> None:
            chroma_collection = self._get_collection(collection)
            chroma_collection.delete(ids=[record_id])

        await asyncio.to_thread(_delete)

    async def delete_document(self, *, collection: str, document_id: str) -> None:
        """Delete all chunks associated with a document identifier."""

        def _delete_document() -> None:
            chroma_collection = self._get_collection(collection)
            records = chroma_collection.get(where={"document_id": document_id}, include=[])
            if records["ids"]:
                chroma_collection.delete(ids=records["ids"])

        await asyncio.to_thread(_delete_document)

    async def search(
        self,
        *,
        collection: str,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Return records ranked by cosine similarity."""

        if limit <= 0:
            return []

        def _search() -> list[dict[str, Any]]:
            chroma_collection = self._get_collection(collection)

            if chroma_collection.count() == 0:
                return []

            results = chroma_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=[
                    "embeddings",
                    "documents",
                    "metadatas",
                    "distances",
                ],
            )

            records: list[dict[str, Any]] = []

            ids = results["ids"][0]
            embeddings = results["embeddings"][0]
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]

            for (
                record_id,
                embedding,
                document,
                metadata,
                distance,
            ) in zip(
                ids,
                embeddings,
                documents,
                metadatas,
                distances,
                strict=True,
            ):
                raw_metadata = metadata.get("metadata", "{}")

                try:
                    parsed_metadata = json.loads(raw_metadata)
                except (TypeError, json.JSONDecodeError):
                    parsed_metadata = {}

                similarity = 1.0 - float(distance)

                records.append(
                    {
                        "id": record_id,
                        "document_id": metadata.get("document_id", ""),
                        "text": document or "",
                        "embedding": [float(value) for value in embedding],
                        "metadata": parsed_metadata,
                        "similarity": similarity,
                    }
                )

            return records

        return await asyncio.to_thread(_search)
