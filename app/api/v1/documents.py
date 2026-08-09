"""Document endpoints for the API layer."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUserDependency
from app.api.responses import APIResponse
from app.database.session import get_async_session
from app.rag.engine import RAGEngine
from app.schemas.document import DocumentResponse
from app.services.document_service import (
    DocumentForbiddenError,
    DocumentNotFoundError,
    DocumentProcessingError,
    DocumentService,
    DocumentValidationError,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/documents", tags=["documents"])


def get_rag_engine() -> RAGEngine:
    """Provide the default RAG engine dependency."""
    return RAGEngine()


def get_document_service(
    session: AsyncSession = Depends(get_async_session),
    rag_engine: RAGEngine = Depends(get_rag_engine),
) -> DocumentService:
    """Provide workspace-scoped document service."""
    return DocumentService(session, rag_engine=rag_engine)


def _handle_document_error(exc: Exception) -> HTTPException:
    if isinstance(exc, DocumentNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, DocumentForbiddenError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, DocumentValidationError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, DocumentProcessingError):
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Document operation failed")


def _to_document_response(document: object) -> DocumentResponse:
    return DocumentResponse.model_validate(document)


@router.post("", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    workspace_id: UUID,
    current_user: CurrentUserDependency,
    service: DocumentService = Depends(get_document_service),
    file: UploadFile = File(...),
) -> APIResponse:
    """Upload and ingest a workspace document under access control."""
    try:
        document = await service.upload_document(
            workspace_id=workspace_id,
            user_id=current_user.id,
            file=file,
        )
    except Exception as exc:
        raise _handle_document_error(exc) from exc
    return APIResponse(data={"document": _to_document_response(document).model_dump(mode="json")})


@router.get("", response_model=APIResponse)
async def list_documents(
    workspace_id: UUID,
    current_user: CurrentUserDependency,
    service: DocumentService = Depends(get_document_service),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
) -> APIResponse:
    """List workspace documents for workspace members."""
    try:
        documents = await service.list_documents(
            workspace_id=workspace_id,
            user_id=current_user.id,
            offset=offset,
            limit=limit,
        )
    except Exception as exc:
        raise _handle_document_error(exc) from exc
    return APIResponse(data={"documents": [_to_document_response(item).model_dump(mode="json") for item in documents]})


@router.get("/{document_id}", response_model=APIResponse)
async def get_document(
    workspace_id: UUID,
    document_id: UUID,
    current_user: CurrentUserDependency,
    service: DocumentService = Depends(get_document_service),
) -> APIResponse:
    """Return workspace-scoped document metadata."""
    try:
        document = await service.get_document(
            workspace_id=workspace_id,
            user_id=current_user.id,
            document_id=document_id,
        )
    except Exception as exc:
        raise _handle_document_error(exc) from exc
    return APIResponse(data={"document": _to_document_response(document).model_dump(mode="json")})


@router.delete("/{document_id}", response_model=APIResponse)
async def delete_document(
    workspace_id: UUID,
    document_id: UUID,
    current_user: CurrentUserDependency,
    service: DocumentService = Depends(get_document_service),
) -> APIResponse:
    """Delete a workspace document and its associated RAG vectors."""
    try:
        await service.delete_document(
            workspace_id=workspace_id,
            user_id=current_user.id,
            document_id=document_id,
        )
    except Exception as exc:
        raise _handle_document_error(exc) from exc
    return APIResponse(data={"document_id": str(document_id), "status": "deleted"})
