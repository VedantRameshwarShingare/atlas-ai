"""Dependency providers for the FastAPI layer."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, Request

from app.ai.orchestrator import AtlasOrchestrator
from app.config import settings
from app.core.logging import get_logger
from app.database.session import get_db_session


async def get_settings() -> Any:
    """Provide application settings."""
    return settings


async def get_logger() -> Any:
    """Provide a logger instance."""
    return get_logger()


async def get_orchestrator() -> AtlasOrchestrator:
    """Provide the orchestrator dependency."""
    return AtlasOrchestrator()


async def get_request_id(request: Request) -> str:
    """Return a request identifier from headers or create one."""
    request_id = request.headers.get("X-Request-ID") or "req-unknown"
    return request_id


async def get_authenticated_user() -> dict[str, Any]:
    """Provide a minimal authenticated user placeholder."""
    return {"id": "anonymous", "authenticated": True}


SettingsDependency = Annotated[Any, Depends(get_settings)]
LoggerDependency = Annotated[Any, Depends(get_logger)]
OrchestratorDependency = Annotated[AtlasOrchestrator, Depends(get_orchestrator)]
RequestIdDependency = Annotated[str, Depends(get_request_id)]
AuthenticatedUserDependency = Annotated[dict[str, Any], Depends(get_authenticated_user)]
