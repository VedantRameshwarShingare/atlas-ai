"""Typed dependencies for the FastAPI application."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.orchestrator import AtlasOrchestrator
from app.core.config import Settings, settings
from app.core.security.jwt import decode_access_token
from app.database.session import get_async_session
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.chat.chat import ChatService

bearer_scheme = HTTPBearer(auto_error=False)


def get_settings() -> Settings:
    """Provide the application settings singleton to routes."""
    return settings


def get_orchestrator() -> AtlasOrchestrator:
    """Provide an Atlas AI orchestrator instance to routes."""
    return AtlasOrchestrator()


def get_chat_service(
    session: Annotated[
        AsyncSession,
        Depends(get_async_session),
    ],
    orchestrator: Annotated[
        AtlasOrchestrator,
        Depends(get_orchestrator),
    ],
) -> ChatService:
    """Provide the chat persistence service to routes."""
    return ChatService(session, orchestrator=orchestrator)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
    session: Annotated[
        AsyncSession,
        Depends(get_async_session),
    ],
) -> User:
    """Resolve the authenticated user from a JWT access token."""

    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials",
        )

    try:
        user_id = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        ) from exc

    user = await UserRepository(session).get(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


SettingsDependency = Annotated[
    Settings,
    Depends(get_settings),
]

OrchestratorDependency = Annotated[
    AtlasOrchestrator,
    Depends(get_orchestrator),
]

DatabaseSessionDependency = Annotated[
    AsyncSession,
    Depends(get_async_session),
]

ChatServiceDependency = Annotated[
    ChatService,
    Depends(get_chat_service),
]

CurrentUserDependency = Annotated[
    User,
    Depends(get_current_user),
]
