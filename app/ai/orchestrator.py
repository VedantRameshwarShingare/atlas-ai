"""Main orchestrator for AI request handling."""

from __future__ import annotations

from typing import Any

from app.ai.capabilities import CapabilityExecutor, CapabilityRegistry
from app.ai.context_manager import ContextManager
from app.ai.enums import IntentType, ResponseType
from app.ai.intent_detector import IntentDetector
from app.ai.llm import OpenAIClient
from app.ai.memory_manager import MemoryManager
from app.ai.prompt_builder import PromptBuilder
from app.ai.response_formatter import ResponseFormatter
from app.ai.response_validator import ResponseValidator
from app.ai.tool_executor import ToolExecutor
from app.ai.tool_registry import ToolRegistry
from app.ai.types import ChatRequest, ChatResponse, ConversationContext, ToolResult


class AtlasOrchestrator:
    """Coordinate AI request handling without embedding business logic."""

    def __init__(
        self,
        *,
        llm_client: OpenAIClient | None = None,
        intent_detector: IntentDetector | None = None,
        tool_registry: ToolRegistry | None = None,
        tool_executor: ToolExecutor | None = None,
        capability_registry: CapabilityRegistry | None = None,
        capability_executor: CapabilityExecutor | None = None,
        context_manager: ContextManager | None = None,
        memory_manager: MemoryManager | None = None,
        prompt_builder: PromptBuilder | None = None,
        response_formatter: ResponseFormatter | None = None,
        response_validator: ResponseValidator | None = None,
    ) -> None:
        self._llm_client = llm_client or OpenAIClient()
        self._intent_detector = intent_detector or IntentDetector()
        self._tool_registry = tool_registry or ToolRegistry()
        self._tool_executor = tool_executor or ToolExecutor(self._tool_registry)
        self._capability_registry = capability_registry or CapabilityRegistry()
        self._capability_executor = capability_executor or CapabilityExecutor(self._capability_registry)
        self._context_manager = context_manager or ContextManager()
        self._memory_manager = memory_manager or MemoryManager()
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._response_formatter = response_formatter or ResponseFormatter()
        self._response_validator = response_validator or ResponseValidator()

    async def handle_request(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request by routing through intent, tools, LLM, and validation."""
        intent_result = self._intent_detector.detect(request.text)
        tool_names = [tool.name for tool in self._tool_registry.list()]
        tool_results = await self._tool_executor.execute_many(tool_names, request=request)
        capability_names = [capability.name for capability in self._capability_registry.list()]
        capability_results = await self._capability_executor.execute_many(capability_names, request=request)

        conversation_context = self._context_manager.build_context(
            request=request,
            conversation_history=[],
            memories=await self._memory_manager.load(user_id=str(request.user_id)),
            workspace_context={},
            documents=[],
            tool_results=tool_results,
            metadata={"intent": intent_result.intent.value, "capabilities": capability_names},
        )

        prompt = self._prompt_builder.build(conversation_context)
        llm_response = await self._llm_client.create_response(input_text=prompt)
        raw_content = getattr(llm_response, "output_text", None) or str(llm_response)

        formatted_response = self._response_formatter.format(
            raw_content,
            response_type=ResponseType.MARKDOWN,
            sources=[],
            tool_citations=[result.tool_name for result in tool_results if result.success] + [result.capability_name for result in capability_results if result.success],
        )
        validated_response = self._response_validator.validate(formatted_response)

        await self._memory_manager.store(user_id=str(request.user_id), key="last_request", value=request.text)

        return validated_response
