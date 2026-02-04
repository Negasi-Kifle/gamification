"""
JSON structured logging formatter.

Implements structured logging per technical:
- One JSON object per log line
- Standard fields: timestamp, level, event/message, trace_id, request_id, tenant_id, service
- Log level configurable via LOG_LEVEL environment variable
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any, ClassVar

from shared.logging.context import LogContext


class LogJsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Produces one JSON object per log line with standard fields.
    Automatically includes correlation IDs from log context.
    """

    # Map Python log levels to lowercase strings
    LEVEL_MAP: ClassVar[dict[int, str]] = {
        logging.DEBUG: "debug",
        logging.INFO: "info",
        logging.WARNING: "warning",
        logging.ERROR: "error",
        logging.CRITICAL: "error",  # Map critical to error for consistency
    }

    def __init__(self, service_name: str | None = None):
        super().__init__()
        self.service_name = service_name or os.environ.get(
            "SERVICE_NAME", "gamification"
        )

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Get correlation IDs from context
        context = LogContext.get()

        # Build the log record
        log_dict: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": self.LEVEL_MAP.get(record.levelno, "info"),
            "event": record.getMessage(),
            "service": self.service_name,
        }

        # Add correlation IDs from context
        if context.get("trace_id"):
            log_dict["trace_id"] = context["trace_id"]
        if context.get("request_id"):
            log_dict["request_id"] = context["request_id"]
        if context.get("tenant_id"):
            log_dict["tenant_id"] = context["tenant_id"]

        # Add logger name and location for debugging
        log_dict["logger"] = record.name

        # Add exception info if present
        if record.exc_info:
            log_dict["exception"] = self.formatException(record.exc_info)

        # Add any extra fields from the record
        # These come from logger.info("msg", extra={"key": "value"})
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "message",
                "taskName",
            ):
                log_dict[key] = value

        return json.dumps(log_dict, default=str)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the JSON formatter configured.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def configure_logging(log_level: str | None = None) -> None:
    """
    Configure logging for the application.

    Sets up JSON formatting and log level from environment.
    Should be called once at application startup.

    Args:
        log_level: Optional override for LOG_LEVEL environment variable
    """
    level_str = log_level or os.environ.get("LOG_LEVEL", "INFO")
    level = getattr(logging, level_str.upper(), logging.INFO)

    # Create JSON formatter
    formatter = LogJsonFormatter()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Add console handler with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("django").setLevel(logging.INFO)
    logging.getLogger("django.db.backends").setLevel(logging.WARNING)
