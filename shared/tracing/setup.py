import logging
import os

logger = logging.getLogger(__name__)

# Global tracer provider reference
_tracer_provider = None


def init_tracing(
    service_name: str | None = None,
    service_version: str | None = None,
    jaeger_endpoint: str | None = None,
    enabled: bool | None = None,
) -> bool:
    """
    Initialize OpenTelemetry tracing.

    Should be called once at application startup, before any spans are created.

    Args:
        service_name: Service name for traces (default: from SERVICE_NAME env var)
        service_version: Service version (default: from SERVICE_VERSION env var)
        jaeger_endpoint: Jaeger collector endpoint (default: from JAEGER_ENDPOINT env var)
        enabled: Whether tracing is enabled (default: from OTEL_ENABLED env var)

    Returns:
        True if tracing was initialized successfully, False otherwise
    """
    global _tracer_provider  # noqa: PLW0603

    if _tracer_provider is not None:
        logger.debug("OpenTelemetry tracing already initialized")
        return True

    # Check if tracing is enabled
    if enabled is None:
        enabled = os.environ.get("OTEL_ENABLED", "false").lower() in (
            "true",
            "1",
            "yes",
        )

    if not enabled:
        logger.info("OpenTelemetry tracing is disabled")
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
        from opentelemetry.sdk.trace import TracerProvider

        # Get configuration
        service_name = service_name or os.environ.get("SERVICE_NAME", "gamification")
        service_version = service_version or os.environ.get("SERVICE_VERSION", "0.1.0")
        jaeger_endpoint = jaeger_endpoint or os.environ.get("JAEGER_ENDPOINT")

        # Create resource with service information
        resource = Resource.create(
            {
                SERVICE_NAME: service_name,
                SERVICE_VERSION: service_version,
            }
        )

        # Create tracer provider
        _tracer_provider = TracerProvider(resource=resource)

        # Configure exporter
        if jaeger_endpoint:
            _setup_jaeger_exporter(_tracer_provider, jaeger_endpoint)
        else:
            _setup_otlp_exporter(_tracer_provider)

        # Set as global tracer provider
        trace.set_tracer_provider(_tracer_provider)

        # Auto-instrument Django
        _instrument_django()

        # Auto-instrument gRPC
        _instrument_grpc()

        logger.info(f"OpenTelemetry tracing initialized for service: {service_name}")
        return True

    except ImportError as e:
        logger.warning(f"OpenTelemetry not installed: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        return False


def _setup_jaeger_exporter(tracer_provider, endpoint: str) -> None:
    """Configure Jaeger exporter."""
    try:
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        exporter = JaegerExporter(
            collector_endpoint=endpoint,
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info(f"Jaeger exporter configured: {endpoint}")
    except ImportError:
        logger.warning("Jaeger exporter not available, trying OTLP")
        _setup_otlp_exporter(tracer_provider)


def _setup_otlp_exporter(tracer_provider) -> None:
    """Configure OTLP exporter (fallback)."""
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        if otlp_endpoint:
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(f"OTLP exporter configured: {otlp_endpoint}")
        else:
            # Console exporter for development
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter

            tracer_provider.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )
            logger.info("Console span exporter configured (development mode)")
    except ImportError:
        logger.warning("OTLP exporter not available")


def _instrument_django() -> None:
    """Auto-instrument Django."""
    try:
        from opentelemetry.instrumentation.django import DjangoInstrumentor

        DjangoInstrumentor().instrument()
        logger.info("Django instrumentation enabled")
    except ImportError:
        logger.debug("Django instrumentation not available")


def _instrument_grpc() -> None:
    """Auto-instrument gRPC."""
    try:
        from opentelemetry.instrumentation.grpc import (
            GrpcInstrumentorClient,
            GrpcInstrumentorServer,
        )

        GrpcInstrumentorClient().instrument()
        GrpcInstrumentorServer().instrument()
        logger.info("gRPC instrumentation enabled")
    except ImportError:
        logger.debug("gRPC instrumentation not available")


def shutdown_tracing() -> None:
    """
    Shutdown tracing and flush pending spans.

    Should be called when the application is shutting down.
    """
    global _tracer_provider  # noqa: PLW0603

    if _tracer_provider:
        try:
            _tracer_provider.shutdown()
            logger.info("OpenTelemetry tracing shut down")
        except Exception as e:
            logger.error(f"Error shutting down tracing: {e}")
        finally:
            _tracer_provider = None
