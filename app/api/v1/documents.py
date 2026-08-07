"""Document endpoints for the API layer."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, Form, UploadFile

from app.api.responses import APIResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=APIResponse)
async def upload_document(
    file: UploadFile = File(...),
    workspace_id: str | None = Form(default=None),
) -> APIResponse:
    """Validate a document upload and return metadata."""
    return APIResponse(
        data={
            "filename": file.filename,
            "content_type": file.content_type,
            "workspace_id": workspace_id,
            "status": "received",
        }
    )


@router.get("/{document_id}", response_model=APIResponse)
async def get_document(document_id: str) -> APIResponse:
    """Return metadata for a stored document reference."""
    return APIResponse(data={"document_id": document_id, "status": "metadata_only"})


@router.delete("/{document_id}", response_model=APIResponse)
async def delete_document(document_id: str) -> APIResponse:
    """Accept a deletion request for a document reference."""
    return APIResponse(data={"document_id": document_id, "status": "deleted"})
