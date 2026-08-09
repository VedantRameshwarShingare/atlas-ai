"""Workspace-scoped document upload and lifecycle service."""

from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document, DocumentStatus
from app.models.membership import MembershipRole
from app.rag.engine import RAGEngine
from app.repositories.document_repository import DocumentRepository
from app.repositories.membership_repository import MembershipRepository


class DocumentError(Exception):
    """Base document-domain exception."""


class DocumentNotFoundError(DocumentError):
    """Raised when a workspace or document is unavailable to the caller."""


class DocumentForbiddenError(DocumentError):
    """Raised when caller lacks permissions for the requested operation."""


class DocumentValidationError(DocumentError):
    """Raised when upload data violates document constraints."""


class DocumentProcessingError(DocumentError):
    """Raised when ingestion or cleanup fails."""


class DocumentService:
    """Coordinates workspace authorization, storage, and RAG lifecycle."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        rag_engine: RAGEngine | None = None,
    ) -> None:
        self.session = session
        self.documents = DocumentRepository(session)
        self.memberships = MembershipRepository(session)
        self.rag_engine = rag_engine or RAGEngine()

    async def list_documents(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Document]:
        """List workspace documents visible to a workspace member."""
        await self._require_membership(workspace_id=workspace_id, user_id=user_id)
        return await self.documents.list_for_workspace(workspace_id, offset=offset, limit=limit)

    async def get_document(self, *, workspace_id: UUID, user_id: UUID, document_id: UUID) -> Document:
        """Return workspace document metadata for workspace members."""
        await self._require_membership(workspace_id=workspace_id, user_id=user_id)
        document = await self.documents.get_by_workspace_and_id(workspace_id, document_id)
        if document is None:
            raise DocumentNotFoundError("Document not found")
        return document

    async def upload_document(self, *, workspace_id: UUID, user_id: UUID, file: UploadFile) -> Document:
        """Store and ingest an uploaded file inside a workspace boundary."""
        await self._require_membership(workspace_id=workspace_id, user_id=user_id)

        filename = (file.filename or "").strip()
        if not filename:
            raise DocumentValidationError("Filename is required")

        extension = Path(filename).suffix.lower()
        allowed_extensions = {item.lower() for item in settings.documents.allowed_extensions}
        if extension not in allowed_extensions:
            raise DocumentValidationError("Unsupported file extension")

        if file.content_type:
            allowed_content_types = {item.lower() for item in settings.documents.allowed_content_types}
            if file.content_type.lower() not in allowed_content_types:
                raise DocumentValidationError("Unsupported content type")

        content = await file.read()
        if not content:
            raise DocumentValidationError("Uploaded file is empty")

        if len(content) > settings.documents.max_upload_size_bytes:
            raise DocumentValidationError("Uploaded file exceeds size limit")

        safe_filename = Path(filename).name
        content_type = file.content_type or "application/octet-stream"

        document = Document(
            workspace_id=workspace_id,
            uploaded_by=user_id,
            filename=safe_filename,
            storage_path="",
            content_type=content_type,
            file_size=len(content),
            status=DocumentStatus.PENDING.value,
            error_message=None,
        )
        self.session.add(document)
        await self.session.flush()

        storage_root = Path(settings.documents.storage_directory)
        target_directory = storage_root / str(workspace_id)
        target_directory.mkdir(parents=True, exist_ok=True)

        storage_path = target_directory / f"{document.id}{extension}"
        document.storage_path = str(storage_path)

        await asyncio.to_thread(storage_path.write_bytes, content)

        try:
            document.status = DocumentStatus.PROCESSING.value
            await self.session.commit()
            await self.session.refresh(document)

            await self.rag_engine.ingest(
                file_path=str(storage_path),
                document_id=str(document.id),
                metadata={
                    "workspace_id": str(workspace_id),
                    "uploaded_by": str(user_id),
                    "filename": safe_filename,
                    "content_type": content_type,
                },
            )

            document.status = DocumentStatus.READY.value
            document.error_message = None
            await self.session.commit()
            await self.session.refresh(document)
            return document
        except Exception as exc:
            document.status = DocumentStatus.FAILED.value
            document.error_message = "Document ingestion failed"
            await self.session.commit()
            await self.session.refresh(document)
            raise DocumentProcessingError("Document ingestion failed") from exc
        finally:
            await file.close()

    async def delete_document(self, *, workspace_id: UUID, user_id: UUID, document_id: UUID) -> None:
        """Delete a document, including vector entries and persisted file."""
        membership = await self._require_membership(workspace_id=workspace_id, user_id=user_id)
        document = await self.documents.get_by_workspace_and_id(workspace_id, document_id)

        if document is None:
            raise DocumentNotFoundError("Document not found")

        can_delete = membership.role in {MembershipRole.OWNER, MembershipRole.ADMIN} or str(
            document.uploaded_by
        ) == str(user_id)
        if not can_delete:
            raise DocumentForbiddenError("Insufficient permissions to delete document")

        try:
            await self.rag_engine.delete(document_id=str(document.id))
        except Exception as exc:
            raise DocumentProcessingError("Document deletion failed") from exc

        file_path = Path(document.storage_path)
        if await asyncio.to_thread(file_path.exists):
            await asyncio.to_thread(file_path.unlink)

        await self.documents.delete(document)

    async def _require_membership(self, *, workspace_id: UUID, user_id: UUID):
        membership = await self.memberships.get_by_workspace_and_user(workspace_id, user_id)
        if membership is None:
            raise DocumentNotFoundError("Workspace not found")
        return membership
