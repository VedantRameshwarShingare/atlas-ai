"""Workspace and membership API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.membership import MembershipRole


class WorkspaceCreateRequest(BaseModel):
    """Request payload for creating a workspace."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class WorkspaceUpdateRequest(BaseModel):
    """Request payload for updating workspace metadata."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def ensure_any_field_set(self) -> WorkspaceUpdateRequest:
        """Require at least one changed field."""
        if self.name is None and self.description is None:
            raise ValueError("At least one field must be provided")
        return self


class AddMemberRequest(BaseModel):
    """Request payload for adding a member to a workspace."""

    email: EmailStr
    role: MembershipRole = MembershipRole.MEMBER


class UpdateMemberRoleRequest(BaseModel):
    """Request payload for changing a member's role."""

    role: MembershipRole


class WorkspaceResponse(BaseModel):
    """Workspace response model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class MembershipResponse(BaseModel):
    """Membership response model with user identity details."""

    model_config = ConfigDict(from_attributes=True)

    workspace_id: UUID
    user_id: UUID
    email: str | None
    role: MembershipRole
    created_at: datetime
    updated_at: datetime
