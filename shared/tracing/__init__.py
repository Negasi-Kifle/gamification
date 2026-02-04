"""
OpenTelemetry tracing module for the Gamification service.

Per technical requirements:
- OpenTelemetry for spans and metrics
- Jaeger for distributed tracing

Usage:
    # Initialize at application startup (e.g., in settings.py or wsgi.py or grpc server)
    from shared.tracing import init_tracing
    init_tracing()

    # Create spans in your code
    from shared.tracing import create_span, get_current_trace_id

    with create_span("operation_name") as span:
        span.set_attribute("key", "value")
        # ... your code ...
"""

from shared.tracing.setup import init_tracing, shutdown_tracing
from shared.tracing.utils import create_span, get_current_span_id, get_current_trace_id

__all__ = [
    "create_span",
    "get_current_span_id",
    "get_current_trace_id",
    "init_tracing",
    "shutdown_tracing",
]
