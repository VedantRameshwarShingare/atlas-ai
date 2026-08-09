"""Workspace and membership domain service."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership, MembershipRole
from app.models.workspace import Workspace
from app.repositories.membership_repository import MembershipRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository


class WorkspaceError(Exception):
    """Base workspace domain error."""


class WorkspaceNotFoundError(WorkspaceError):
    """Raised when the workspace is missing or inaccessible."""


class WorkspaceForbiddenError(WorkspaceError):
    """Raised when caller lacks required permissions."""


class WorkspaceValidationError(WorkspaceError):
    """Raised when a workspace operation violates business rules."""


class WorkspaceService:
    """Encapsulates workspace and membership CRUD and authorization rules."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.workspaces = WorkspaceRepository(session)
        self.memberships = MembershipRepository(session)
        self.users = UserRepository(session)

    async def list_workspaces(self, user_id: UUID, *, offset: int = 0, limit: int = 100) -> list[Workspace]:
        """Return workspaces where caller is a member."""
        return await self.workspaces.list_for_user(user_id, offset=offset, limit=limit)

    async def create_workspace(self, *, owner_id: UUID, name: str, description: str | None = None) -> Workspace:
        """Create a workspace and its initial owner membership."""
        workspace = Workspace(name=name.strip(), description=description)
        self.session.add(workspace)
        await self.session.flush()

        owner_membership = Membership(
            workspace_id=workspace.id,
            user_id=owner_id,
            role=MembershipRole.OWNER,
        )
        self.session.add(owner_membership)
        await self.session.commit()
        await self.session.refresh(workspace)
        return workspace

    async def get_workspace(self, *, workspace_id: UUID, user_id: UUID) -> Workspace:
        """Return a workspace only if caller is a member."""
        workspace = await self.workspaces.get_for_user(workspace_id, user_id)
        if workspace is None:
            raise WorkspaceNotFoundError("Workspace not found")
        return workspace

    async def update_workspace(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
        name: str | None,
        description: str | None,
    ) -> Workspace:
        """Update workspace metadata when caller has admin-level privileges."""
        membership = await self._get_membership_or_not_found(workspace_id=workspace_id, user_id=user_id)
        if membership.role not in {MembershipRole.OWNER, MembershipRole.ADMIN}:
            raise WorkspaceForbiddenError("Insufficient permissions to update workspace")

        workspace = await self.workspaces.get(workspace_id)
        if workspace is None:
            raise WorkspaceNotFoundError("Workspace not found")

        if name is not None:
            workspace.name = name.strip()
        if description is not None:
            workspace.description = description

        await self.session.commit()
        await self.session.refresh(workspace)
        return workspace

    async def delete_workspace(self, *, workspace_id: UUID, user_id: UUID) -> None:
        """Delete a workspace when caller is an owner."""
        membership = await self._get_membership_or_not_found(workspace_id=workspace_id, user_id=user_id)
        if membership.role != MembershipRole.OWNER:
            raise WorkspaceForbiddenError("Only owners can delete workspaces")

        workspace = await self.workspaces.get(workspace_id)
        if workspace is None:
            raise WorkspaceNotFoundError("Workspace not found")

        await self.workspaces.delete(workspace)

    async def list_members(self, *, workspace_id: UUID, user_id: UUID) -> list[tuple[Membership, object]]:
        """List members when caller belongs to the workspace."""
        await self._get_membership_or_not_found(workspace_id=workspace_id, user_id=user_id)
        return await self.memberships.list_with_users(workspace_id)

    async def add_member(
        self,
        *,
        workspace_id: UUID,
        acting_user_id: UUID,
        email: str,
        role: MembershipRole,
    ) -> Membership:
        """Add a workspace member with role constraints by acting member role."""
        acting_membership = await self._get_membership_or_not_found(workspace_id=workspace_id, user_id=acting_user_id)
        self._ensure_manage_permission(acting_membership.role)
        self._ensure_role_assignment_allowed(acting_membership.role, role)

        user = await self.users.get_by_email(email.strip().lower())
        if user is None:
            raise WorkspaceValidationError("Target user does not exist")

        existing = await self.memberships.get_by_workspace_and_user(workspace_id, user.id)
        if existing is not None:
            raise WorkspaceValidationError("User is already a member")

        membership = Membership(workspace_id=workspace_id, user_id=user.id, role=role)
        await self.memberships.create(membership)
        return membership

    async def update_member_role(
        self,
        *,
        workspace_id: UUID,
        acting_user_id: UUID,
        target_user_id: UUID,
        role: MembershipRole,
    ) -> Membership:
        """Update membership role while protecting owner invariants."""
        acting_membership = await self._get_membership_or_not_found(workspace_id=workspace_id, user_id=acting_user_id)
        self._ensure_manage_permission(acting_membership.role)
        self._ensure_role_assignment_allowed(acting_membership.role, role)

        target_membership = await self.memberships.get_by_workspace_and_user(workspace_id, target_user_id)
        if target_membership is None:
            raise WorkspaceNotFoundError("Membership not found")

        if target_membership.role == MembershipRole.OWNER and acting_membership.role != MembershipRole.OWNER:
            raise WorkspaceForbiddenError("Only owners can modify owner memberships")

        if target_membership.role == MembershipRole.OWNER and role != MembershipRole.OWNER:
            owner_count = await self.memberships.count_role(workspace_id, MembershipRole.OWNER)
            if owner_count <= 1:
                raise WorkspaceValidationError("Workspace must retain at least one owner")

        target_membership.role = role
        await self.memberships.update(target_membership)
        return target_membership

    async def remove_member(self, *, workspace_id: UUID, acting_user_id: UUID, target_user_id: UUID) -> None:
        """Remove a member while enforcing owner protections."""
        acting_membership = await self._get_membership_or_not_found(workspace_id=workspace_id, user_id=acting_user_id)
        target_membership = await self.memberships.get_by_workspace_and_user(workspace_id, target_user_id)
        if target_membership is None:
            raise WorkspaceNotFoundError("Membership not found")

        # Self-removal is allowed for non-owners; owner self-removal still follows owner constraints.
        if acting_user_id != target_user_id:
            self._ensure_manage_permission(acting_membership.role)

        if target_membership.role == MembershipRole.OWNER:
            if acting_membership.role != MembershipRole.OWNER:
                raise WorkspaceForbiddenError("Only owners can remove owner memberships")

            owner_count = await self.memberships.count_role(workspace_id, MembershipRole.OWNER)
            if owner_count <= 1:
                raise WorkspaceValidationError("Workspace must retain at least one owner")

        await self.memberships.delete(target_membership)

    async def _get_membership_or_not_found(self, *, workspace_id: UUID, user_id: UUID) -> Membership:
        membership = await self.memberships.get_by_workspace_and_user(workspace_id, user_id)
        if membership is None:
            raise WorkspaceNotFoundError("Workspace not found")
        return membership

    @staticmethod
    def _ensure_manage_permission(role: MembershipRole) -> None:
        if role not in {MembershipRole.OWNER, MembershipRole.ADMIN}:
            raise WorkspaceForbiddenError("Insufficient permissions to manage membership")

    @staticmethod
    def _ensure_role_assignment_allowed(acting_role: MembershipRole, target_role: MembershipRole) -> None:
        if acting_role == MembershipRole.ADMIN and target_role in {MembershipRole.ADMIN, MembershipRole.OWNER}:
            raise WorkspaceForbiddenError("Admins can only assign member role")
