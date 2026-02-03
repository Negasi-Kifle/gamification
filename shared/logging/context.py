"""
Log context management for correlation IDs.

Provides thread-local storage for request_id, trace_id, and tenant_id
that can be automatically included in all log messages.
"""

import contextvars
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

# Context variable for storing log context
_log_context: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "log_context", default={}
)


class LogContext:
    """
    Context manager for setting log correlation IDs.

    Usage:
        with LogContext(request_id="req-123", tenant_id="t1"):
            logger.info("Processing request")  # Includes request_id and tenant_id

    Or use the set/clear methods for middleware:
        LogContext.set(request_id="req-123")
        # ... handle request ...
        LogContext.clear()
    """

    def __init__(
        self,
        request_id: str | None = None,
        trace_id: str | None = None,
        tenant_id: str | None = None,
        **extra: Any,
    ):
        self.context = {}
        if request_id:
            self.context["request_id"] = request_id
        if trace_id:
            self.context["trace_id"] = trace_id
        if tenant_id:
            self.context["tenant_id"] = tenant_id
        self.context.update(extra)
        self._token: contextvars.Token | None = None

    def __enter__(self) -> "LogContext":
        # Merge with existing context
        current = _log_context.get()
        new_context = {**current, **self.context}
        self._token = _log_context.set(new_context)
        return self

    def __exit__(self, *args: Any) -> None:
        if self._token:
            _log_context.reset(self._token)

    @staticmethod
    def set(
        request_id: str | None = None,
        trace_id: str | None = None,
        tenant_id: str | None = None,
        **extra: Any,
    ) -> None:
        """Set context values (for use in middleware)."""
        current = _log_context.get()
        new_context = dict(current)
        if request_id:
            new_context["request_id"] = request_id
        if trace_id:
            new_context["trace_id"] = trace_id
        if tenant_id:
            new_context["tenant_id"] = tenant_id
        new_context.update(extra)
        _log_context.set(new_context)

    @staticmethod
    def get() -> dict[str, Any]:
        """Get the current log context."""
        return _log_context.get()

    @staticmethod
    def clear() -> None:
        """Clear the log context."""
        _log_context.set({})

    @staticmethod
    def generate_request_id() -> str:
        """Generate a new request ID."""
        return str(uuid.uuid4())


@contextmanager
def log_context(
    request_id: str | None = None,
    trace_id: str | None = None,
    tenant_id: str | None = None,
    **extra: Any,
) -> Generator[None, None, None]:
    """
    Context manager function for setting log context.

    Usage:
        with log_context(request_id="req-123", tenant_id="t1"):
            logger.info("Processing request")
    """
    ctx = LogContext(
        request_id=request_id, trace_id=trace_id, tenant_id=tenant_id, **extra
    )
    with ctx:
        yield
