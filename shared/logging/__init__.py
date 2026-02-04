"""
Structured logging module for the Gamification service.

Provides JSON-formatted logging with correlation IDs (request_id, trace_id, tenant_id)
for consistent log aggregation and search across the microservices ecosystem.

Usage:
    from shared.logging import get_logger, LogContext

    logger = get_logger(__name__)
    logger.info("freebet_created", freebet_id="abc-123", tenant_id="t1")
"""

from shared.logging.context import LogContext, log_context
from shared.logging.formatter import (
    LogJsonFormatter,
    configure_logging,
    get_logger,
)

__all__ = [
    "LogJsonFormatter",
    "LogContext",
    "configure_logging",
    "get_logger",
    "log_context",
]
