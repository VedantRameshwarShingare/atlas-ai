"""Chat endpoint for the API layer."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.ai.orchestrator import AtlasOrchestrator
from app.ai.types import ChatRequest, ChatResponse
from app.api.dependencies import OrchestratorDependency
from app.api.responses import APIResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=APIResponse)
async def chat(
    request: ChatRequest,
    orchestrator: OrchestratorDependency,
) -> APIResponse:
    """Accept a chat request and forward it to the orchestrator."""
    response = await orchestrator.handle_request(request)
    return APIResponse(data={"content": response.content, "response_type": response.response_type.value}, metadata={"sources": response.sources})
