import logging
import uuid

from shared.logging.context import LogContext

logger = logging.getLogger(__name__)


class GrpcCorrelationInterceptor:
    """
    gRPC interceptor for extracting correlation IDs from metadata.

    Usage:
        from shared.middleware.correlation_grpc import GrpcCorrelationInterceptor

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
        metadata = {}
        if handler_call_details.invocation_metadata:
            for key, value in handler_call_details.invocation_metadata:
                metadata[key.lower()] = value

        # With fallback to UUID if request_id is missing
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
