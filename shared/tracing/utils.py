"""
OpenTelemetry tracing utilities.

Provides helper functions for creating spans and extracting trace context.
"""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)


@contextmanager
def create_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    kind: str | None = None,
) -> Generator[Any, None, None]:
    """
    Create a new span for tracing.

    Usage:
        with create_span("operation_name", {"key": "value"}) as span:
            # ... your code ...
            span.set_attribute("another_key", "value")

    Args:
        name: Name of the span
        attributes: Optional initial attributes
        kind: Span kind (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)

    Yields:
        The span object (or a no-op if tracing is disabled)
    """
    try:
        from opentelemetry import trace
        from opentelemetry.trace import SpanKind

        tracer = trace.get_tracer(__name__)

        # Map kind string to SpanKind enum
        span_kind = SpanKind.INTERNAL
        if kind:
            kind_map = {
                "INTERNAL": SpanKind.INTERNAL,
                "SERVER": SpanKind.SERVER,
                "CLIENT": SpanKind.CLIENT,
                "PRODUCER": SpanKind.PRODUCER,
                "CONSUMER": SpanKind.CONSUMER,
            }
            span_kind = kind_map.get(kind.upper(), SpanKind.INTERNAL)

        with tracer.start_as_current_span(name, kind=span_kind) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            yield span

    except ImportError:
        # OpenTelemetry not installed, yield a no-op
        yield _NoOpSpan()
    except Exception as e:
        logger.debug(f"Error creating span: {e}")
        yield _NoOpSpan()


class _NoOpSpan:
    """No-op span for when tracing is disabled."""

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def add_event(self, name: str, attributes: dict | None = None) -> None:
        pass

    def record_exception(self, exception: BaseException) -> None:
        pass

    def set_status(self, status: Any) -> None:
        pass


def get_current_trace_id() -> str | None:
    """
    Get the current trace ID.

    Useful for including in logs or passing to other services.

    Returns:
        Trace ID as hex string, or None if no active span
    """
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            return format(span.get_span_context().trace_id, "032x")
        return None
    except ImportError:
        return None
    except Exception:
        return None


def get_current_span_id() -> str | None:
    """
    Get the current span ID.

    Returns:
        Span ID as hex string, or None if no active span
    """
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            return format(span.get_span_context().span_id, "016x")
        return None
    except ImportError:
        return None
    except Exception:
        return None


def inject_trace_context(headers: dict) -> dict:
    """
    Inject trace context into HTTP headers.

    Use when making outgoing HTTP requests to propagate trace context.

    Args:
        headers: Dictionary of headers to inject into

    Returns:
        Headers with trace context added
    """
    try:
        from opentelemetry.propagate import inject

        inject(headers)
        return headers
    except ImportError:
        return headers
    except Exception:
        return headers


def extract_trace_context(headers: dict) -> Any | None:
    """
    Extract trace context from HTTP headers.

    Use when receiving incoming HTTP requests to continue the trace.

    Args:
        headers: Dictionary of headers to extract from

    Returns:
        Extracted context or None
    """
    try:
        from opentelemetry.propagate import extract

        return extract(headers)
    except ImportError:
        return None
    except Exception:
        return None
