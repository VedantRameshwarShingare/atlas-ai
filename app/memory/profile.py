"""User profile abstraction for memory-based personalization."""

from __future__ import annotations

from app.memory.memory_types import UserProfileState


class ProfileMemory:
    """Keep user profile data as a memory-backed abstraction without persistence logic."""

    def __init__(self, state: UserProfileState | None = None) -> None:
        self._state = state or UserProfileState()

    async def load(self) -> UserProfileState:
        """Return the current profile state."""
        return self._state

    async def save(self, *, state: UserProfileState) -> UserProfileState:
        """Persist the profile state in memory."""
        self._state = state
        return self._state

    async def update(self, **kwargs: object) -> UserProfileState:
        """Partially update profile fields."""
        for key, value in kwargs.items():
            setattr(self._state, key, value)
        return self._state
