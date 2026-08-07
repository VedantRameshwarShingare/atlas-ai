"""Context-local request tracing without a vendor dependency."""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager, AbstractContextManager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Literal
from uuid import uuid4

TraceKind = Literal["request", "capability", "service"]


@dataclass(slots=True, frozen=True)
class TraceContext:
    request_id: str
    correlation_id: str
    capability_chain: tuple[str, ...] = ()
    service_calls: tuple[str, ...] = ()


_trace_context: ContextVar[TraceContext | None] = ContextVar("atlas_trace_context", default=None)


def current_trace() -> TraceContext | None:
    return _trace_context.get()


def start_trace(*, request_id: str | None = None, correlation_id: str | None = None) -> Token[TraceContext | None]:
    """Install an isolated trace context; callers reset it with ``end_trace``."""
    context = TraceContext(request_id or str(uuid4()), correlation_id or str(uuid4()))
    return _trace_context.set(context)


def end_trace(token: Token[TraceContext | None]) -> None:
    _trace_context.reset(token)


class TraceSpan(AbstractContextManager[TraceContext], AbstractAsyncContextManager[TraceContext]):
    """Append a capability or service name to the request-local trace chain."""

    def __init__(self, name: str, *, kind: TraceKind) -> None:
        self._name, self._kind = name, kind
        self._token: Token[TraceContext | None] | None = None

    def __enter__(self) -> TraceContext:
        parent = current_trace() or TraceContext(str(uuid4()), str(uuid4()))
        context = TraceContext(
            request_id=parent.request_id,
            correlation_id=parent.correlation_id,
            capability_chain=parent.capability_chain + ((self._name,) if self._kind == "capability" else ()),
            service_calls=parent.service_calls + ((self._name,) if self._kind == "service" else ()),
        )
        self._token = _trace_context.set(context)
        return context

    def __exit__(self, *_: object) -> None:
        if self._token is not None:
            _trace_context.reset(self._token)

    async def __aenter__(self) -> TraceContext:
        return self.__enter__()

    async def __aexit__(self, *_: object) -> None:
        self.__exit__()


def capability_span(name: str) -> TraceSpan:
    return TraceSpan(name, kind="capability")


def service_span(name: str) -> TraceSpan:
    return TraceSpan(name, kind="service")
