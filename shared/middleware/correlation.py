"""
Correlation ID middleware for Django.

Extracts or generates correlation IDs (request_id, trace_id, tenant_id) from
incoming requests and adds them to the log context for all subsequent log messages.

Per technical guideline §9:
- request_id: Per-request correlation ID (X-Request-ID header or generated)
- trace_id: OpenTelemetry/Jaeger trace ID (X-Trace-ID or traceparent header)
- tenant_id: Tenant identifier (X-Tenant-ID header)
"""

import logging
import time
import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from shared.logging.context import LogContext

logger = logging.getLogger(__name__)


class CorrelationIdMiddleware:
    """
    Django middleware that extracts/generates correlation IDs and adds them to log context.

    Headers:
    - X-Request-ID: Per-request correlation ID (generated if not present)
    - X-Trace-ID: OpenTelemetry trace ID (from header or traceparent)
    - X-Tenant-ID: Tenant identifier

    Response Headers:
    - Adds X-Request-ID to response for client correlation

    Usage in settings.py:
        MIDDLEWARE = [
            'shared.middleware.CorrelationIdMiddleware',
            ...
        ]
    """

    # Standard header names
    REQUEST_ID_HEADER = "HTTP_X_REQUEST_ID"
    TRACE_ID_HEADER = "HTTP_X_TRACE_ID"
    TRACEPARENT_HEADER = "HTTP_TRACEPARENT"
    TENANT_ID_HEADER = "HTTP_X_TENANT_ID"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Extract or generate correlation IDs
        request_id = self._get_request_id(request)
        trace_id = self._get_trace_id(request)
        tenant_id = self._get_tenant_id(request)

        # Store IDs on request object for access in views
        request.correlation_ids = {
            "request_id": request_id,
            "trace_id": trace_id,
            "tenant_id": tenant_id,
        }

        # Set log context for all logging in this request
        LogContext.set(
            request_id=request_id,
            trace_id=trace_id,
            tenant_id=tenant_id,
        )

        # Log request start
        start_time = time.time()
        logger.info(
            "request_started",
            extra={
                "method": request.method,
                "path": request.path,
                "query_string": request.META.get("QUERY_STRING", ""),
            },
        )

        try:
            # Process request
            response = self.get_response(request)

            # Log request end
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                "request_completed",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            # Add request ID to response headers for client correlation
            response["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Log exception
            duration_ms = (time.time() - start_time) * 1000
            logger.exception(
                "request_failed",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e),
                },
            )
            raise

        finally:
            # Clear log context
            LogContext.clear()

    def _get_request_id(self, request: HttpRequest) -> str:
        """Get request ID from header or generate a new one."""
        request_id = request.META.get(self.REQUEST_ID_HEADER)
        if not request_id:
            request_id = str(uuid.uuid4())
        return request_id

    def _get_trace_id(self, request: HttpRequest) -> str | None:
        """
        Get trace ID from headers.

        Supports:
        - X-Trace-ID: Simple trace ID header
        - traceparent: W3C Trace Context header (extracts trace ID portion)
        """
        # Try X-Trace-ID first
        trace_id = request.META.get(self.TRACE_ID_HEADER)
        if trace_id:
            return trace_id

        # Try traceparent (W3C Trace Context format: version-trace_id-parent_id-flags)
        traceparent = request.META.get(self.TRACEPARENT_HEADER)
        if traceparent:
            try:
                parts = traceparent.split("-")
                if len(parts) >= 2:
                    return parts[1]  # trace_id is the second part
            except (ValueError, IndexError):
                pass

        return None

    def _get_tenant_id(self, request: HttpRequest) -> str | None:
        """Get tenant ID from header."""
        return request.META.get(self.TENANT_ID_HEADER)


class GrpcCorrelationInterceptor:
    """
    gRPC interceptor for extracting correlation IDs from metadata.

    Usage:
        from shared.middleware.correlation import GrpcCorrelationInterceptor

        interceptor = GrpcCorrelationInterceptor()
        server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=10),
            interceptors=[interceptor]
        )
    """

    # Standard metadata keys for gRPC
    REQUEST_ID_KEY = "x-request-id"
    TRACE_ID_KEY = "x-trace-id"
    TENANT_ID_KEY = "x-tenant-id"

    def intercept_service(self, continuation, handler_call_details):
        """Intercept incoming gRPC calls to set log context."""
        # Extract metadata
        metadata = (
            dict(handler_call_details.invocation_metadata)
            if handler_call_details.invocation_metadata
            else {}
        )

        request_id = metadata.get(self.REQUEST_ID_KEY) or str(uuid.uuid4())
        trace_id = metadata.get(self.TRACE_ID_KEY)
        tenant_id = metadata.get(self.TENANT_ID_KEY)

        # Set log context
        LogContext.set(
            request_id=request_id,
            trace_id=trace_id,
            tenant_id=tenant_id,
        )

        try:
            return continuation(handler_call_details)
        finally:
            LogContext.clear()
