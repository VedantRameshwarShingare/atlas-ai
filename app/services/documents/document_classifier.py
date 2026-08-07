"""Document classification service abstraction."""

from __future__ import annotations

from typing import Any

from app.services.base import BaseService


class DocumentClassifierService(BaseService):
    """Provide an interface for classifying document types."""

    name = "document_classifier"
    description = "Classifies uploaded documents into known categories"

    async def classify(self, file_path: str) -> dict[str, Any]:
        """Classify a document based on its file path or content."""
        return {"file_path": file_path, "source": "document_classifier"}

    async def ping(self) -> dict[str, Any]:
        """Return service readiness metadata."""
        return {"service": self.name, "available": True}
