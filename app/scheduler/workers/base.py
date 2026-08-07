"""Shared worker implementation that delegates all work to capabilities."""

from __future__ import annotations

from typing import Any, Protocol


class CapabilityProvider(Protocol):
    """Minimal dependency required by workers; compatible with CapabilityRegistry."""

    def get(self, name: str) -> Any | None:
        """Return a capability by name."""


class BaseWorker:
    """Worker base class. It intentionally has no OpenAI or service dependency."""

    capability_name = ""

    def __init__(self, capabilities: CapabilityProvider) -> None:
        self._capabilities = capabilities

    async def run(self, **context: Any) -> Any:
        capability = self._capabilities.get(self.capability_name)
        if capability is None:
            raise LookupError(f"Required capability is not registered: {self.capability_name}")
        return await capability.execute(**self.build_payload(**context))

    def build_payload(self, **context: Any) -> dict[str, Any]:
        """Map scheduler context to the capability's explicit work request."""
        return context
