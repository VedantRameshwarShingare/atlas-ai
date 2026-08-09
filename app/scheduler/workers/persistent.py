"""Worker adapter for database-backed scheduled jobs."""

from __future__ import annotations

from typing import Any

from app.ai.capabilities import CapabilityRegistry


class PersistentJobWorker:
    """Execute a persistent job through the existing capability system."""

    def __init__(
        self,
        *,
        job_type: str,
        payload: dict[str, Any],
        capabilities: CapabilityRegistry,
    ) -> None:
        self.job_type = job_type
        self.payload = payload
        self.capabilities = capabilities

    async def run(self, **context: Any) -> Any:
        """Execute the configured persistent job."""

        capability = self.capabilities.get(self.job_type)

        if capability is None:
            raise ValueError(
                f"No capability registered for scheduled job type: {self.job_type}"
            )

        result = capability.execute(
            payload=self.payload,
            context=context,
        )

        if hasattr(result, "__await__"):
            return await result

        return result