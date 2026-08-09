"""Authentication endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUserDependency
from app.api.responses import APIResponse
from app.core.security.jwt import create_access_token, create_telegram_link_token, telegram_link_token_ttl_seconds
from app.core.security.passwords import hash_password, verify_password
from app.database.session import get_async_session
from app.models.user import User
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth", tags=["authentication"])


class TokenResponse(BaseModel):
    """JWT access-token response."""

    access_token: str
    token_type: str = "bearer"


class CredentialsRequest(BaseModel):
    """Registration and login credentials."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    """Safe public account representation."""

    id: str
    email: str | None
    is_active: bool
    telegram_user_id: str | None
    created_at: datetime
    updated_at: datetime


def _normalize_email(email: EmailStr) -> str:
    """Apply a consistent canonical form for identity matching."""
    return str(email).strip().lower()


async def _credentials(session: AsyncSession, request: CredentialsRequest, *, register: bool) -> TokenResponse:
    """Create or authenticate an account without exposing credential details."""
    repository = UserRepository(session)
    email = _normalize_email(request.email)
    user = await repository.get_by_email(email)

    if register:
        if user is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")

        user = User(
            email=email,
            password_hash=hash_password(request.password),
            is_active=True,
            language="en",
            timezone="UTC",
        )
        await repository.create(user)
    elif user is None or not verify_password(request.password, user.password_hash or "") or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: CredentialsRequest, session: AsyncSession = Depends(get_async_session)) -> TokenResponse:
    """Register an account and issue a bearer token."""
    return await _credentials(session, request, register=True)


@router.post("/login", response_model=TokenResponse)
async def login(request: CredentialsRequest, session: AsyncSession = Depends(get_async_session)) -> TokenResponse:
    """Authenticate an account and issue a bearer token."""
    return await _credentials(session, request, register=False)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUserDependency) -> UserResponse:
    """Return the authenticated user's safe public profile."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        is_active=current_user.is_active,
        telegram_user_id=current_user.telegram_user_id,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.post("/telegram/link-token", response_model=APIResponse)
async def create_telegram_linking_token(current_user: CurrentUserDependency) -> APIResponse:
    """Issue a short-lived token used to safely link a Telegram account."""
    return APIResponse(
        data={
            "link_token": create_telegram_link_token(current_user.id),
            "expires_in_seconds": telegram_link_token_ttl_seconds(),
        }
    )
