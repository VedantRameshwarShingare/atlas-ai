"""Vector store interface around ChromaDB-style storage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class VectorStore(ABC):
    """Interface for storing and retrieving vector embeddings."""

    @abstractmethod
    async def store(self, *, collection: str, records: list[dict[str, Any]]) -> None:
        """Store vector records."""

    @abstractmethod
    async def update(self, *, collection: str, record_id: str, values: dict[str, Any]) -> None:
        """Update an existing vector record."""

    @abstractmethod
    async def delete(self, *, collection: str, record_id: str) -> None:
        """Delete a vector record."""

    @abstractmethod
    async def search(self, *, collection: str, query_embedding: list[float], limit: int = 5) -> list[dict[str, Any]]:
        """Search vector records by similarity."""


class ChromaVectorStore(VectorStore):
    """Simple in-memory implementation used for scaffolding the interface."""

    def __init__(self) -> None:
        self._records: dict[str, list[dict[str, Any]]] = {}

    async def store(self, *, collection: str, records: list[dict[str, Any]]) -> None:
        self._records[collection] = list(self._records.get(collection, [])) + records

    async def update(self, *, collection: str, record_id: str, values: dict[str, Any]) -> None:
        for record in self._records.get(collection, []):
            if record.get("id") == record_id:
                record.update(values)
                return

    async def delete(self, *, collection: str, record_id: str) -> None:
        self._records[collection] = [record for record in self._records.get(collection, []) if record.get("id") != record_id]

    async def search(self, *, collection: str, query_embedding: list[float], limit: int = 5) -> list[dict[str, Any]]:
        return list(self._records.get(collection, []))[:limit]
