"""Main orchestrator for AI request handling."""

from __future__ import annotations

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
from app.ai.types import ChatRequest, ChatResponse
from app.rag.engine import RAGEngine
from app.services.finance.service import FinanceService
from app.tools.finance import FinanceTool


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
        rag_engine: RAGEngine | None = None,
        context_budget: int = 12_000,
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
        self._rag_engine = rag_engine
        self._context_budget = context_budget
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register default tools for built-in intent routes."""
        if self._tool_registry.get("finance") is None:
            self._tool_registry.register(FinanceTool(FinanceService()))

    async def handle_request(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request through the AI pipeline."""

        intent_result = self._intent_detector.detect(request.text)

        required_tool_types = set(intent_result.required_tools)
        tool_names = [
            tool.name for tool in self._tool_registry.list() if getattr(tool, "tool_type", None) in required_tool_types
        ]

        tool_results = await self._tool_executor.execute_many(
            tool_names,
            request=request,
        )

        capability_names = [
            capability.name
            for capability in self._capability_registry.list()
            if getattr(capability, "tool_type", None) in required_tool_types
        ]

        capability_results = await self._capability_executor.execute_many(
            capability_names,
            request=request,
        )

        documents: list[dict[str, object]] = []
        citations: list[str] = []
        if self._rag_engine is not None and intent_result.intent in {
            IntentType.DOCUMENT_QA,
            IntentType.DOCUMENT_SUMMARY,
        }:
            rag_context = await self._rag_engine.build_context(query=request.text)
            documents = list(rag_context.retrieved_chunks)
            citations = [citation.source or citation.document for citation in rag_context.citations]

        memories = await self._memory_manager.load(user_id=str(request.user_id), query=request.text)
        conversation_context = self._context_manager.build_context(
            request=request,
            conversation_history=request.conversation_history,
            memories=memories,
            workspace_context={},
            documents=documents,
            tool_results=tool_results,
            metadata={
                "intent": intent_result.intent.value,
                "capabilities": capability_names,
            },
        )

        prompt = self._prompt_builder.build(conversation_context, max_characters=self._context_budget)

        llm_response = await self._llm_client.create_response(input_text=prompt)

        raw_content = getattr(llm_response, "output_text", None) or str(llm_response)

        tool_citations = [result.tool_name for result in tool_results if result.success]

        tool_citations.extend(result.capability_name for result in capability_results if result.success)

        formatted_response = self._response_formatter.format(
            raw_content,
            response_type=ResponseType.MARKDOWN,
            sources=citations,
            tool_citations=tool_citations,
        )

        validated_response = self._response_validator.validate(formatted_response)

        await self._extract_explicit_memory(request)

        return validated_response

    async def _extract_explicit_memory(self, request: ChatRequest) -> None:
        """Persist only explicit preference statements, never every conversation turn."""
        lowered = request.text.lower().strip()
        marker = "remember that "
        if request.user_id is not None and lowered.startswith(marker):
            value = request.text[len(marker) :].strip()
            if value:
                await self._memory_manager.store(user_id=str(request.user_id), key="preference", value=value)
