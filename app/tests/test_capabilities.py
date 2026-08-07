import asyncio

from app.ai.capabilities import BaseCapability, CapabilityExecutor, CapabilityRegistry


class DummyCapability(BaseCapability):
    name = "dummy"
    description = "A dummy capability for testing"

    async def execute(self, **kwargs):
        return {"ok": True, "services": self.services}


def test_capability_registry_tracks_registered_capabilities() -> None:
    registry = CapabilityRegistry()
    capability = DummyCapability(services={"openai": object()})
    registry.register(capability)

    assert registry.get("dummy") is capability
    assert [item.name for item in registry.list()] == ["dummy"]


def test_capability_executor_returns_standardized_results() -> None:
    registry = CapabilityRegistry()
    registry.register(DummyCapability())
    executor = CapabilityExecutor(registry)

    results = asyncio.run(executor.execute_many(["dummy"]))

    assert len(results) == 1
    assert results[0].success is True
    assert results[0].output["ok"] is True
