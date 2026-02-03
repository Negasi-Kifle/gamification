"""
Middleware module for Django.

Provides middleware for:
- Correlation ID injection (request_id, trace_id, tenant_id)
- Request/response logging
"""

from shared.middleware.correlation import CorrelationIdMiddleware

__all__ = [
    "CorrelationIdMiddleware",
]
