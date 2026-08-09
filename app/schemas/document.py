"""Workspace document API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    """Public document metadata excluding internal storage paths."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    uploaded_by: UUID
    filename: str
    content_type: str
    file_size: int
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime
