"""
Audit and exception log publishers.

Per technical guideline §6:
- Publishes to 'audit-logs' after important actions
- Publishes to 'exception-logs' on errors
- Uses Kafka for reliable delivery
"""

import logging
import traceback
from typing import Any

from shared.audit.models import AuditAction, AuditLogMessage, ExceptionLogMessage
from shared.kafka import KafkaProducer
from shared.kafka.config import KafkaConfig
from shared.logging.context import LogContext

logger = logging.getLogger(__name__)


class AuditPublisher:
    """
    Publisher for audit logs.

    Sends audit events to the 'audit-logs' Kafka topic for
    central storage and analysis by the AuditReport service.

    Usage:
        audit = AuditPublisher()
        audit.log(
            action=AuditAction.CASINO_FREEBET_CREATED,
            entity_type="CasinoFreeBet",
            entity_id="abc-123",
            tenant_id="t1",
        )
    """

    def __init__(
        self,
        producer: KafkaProducer | None = None,
        config: KafkaConfig | None = None,
    ):
        """
        Initialize audit publisher.

        Args:
            producer: Kafka producer instance (creates one if not provided)
            config: Kafka configuration (uses defaults if not provided)
        """
        self.config = config or KafkaConfig.from_django_settings()
        self._producer = producer
        self._initialized = False

    def _ensure_producer(self) -> KafkaProducer | None:
        """Lazily initialize the producer."""
        if not self._initialized:
            self._initialized = True
            try:
                if self._producer is None:
                    self._producer = KafkaProducer(self.config)
            except Exception as e:
                logger.warning(f"Failed to initialize audit producer: {e}")
        return self._producer

    def log(
        self,
        action: AuditAction | str,
        entity_type: str,
        entity_id: str,
        tenant_id: str,
        payload: dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> bool:
        """
        Publish an audit log entry.

        Args:
            action: Action that was performed
            entity_type: Type of entity (e.g., 'CasinoFreeBet')
            entity_id: Public ID of the entity
            tenant_id: Tenant identifier
            payload: Additional data about the action
            user_id: ID of the user who performed the action

        Returns:
            True if published successfully, False otherwise
        """
        producer = self._ensure_producer()
        if not producer:
            logger.warning("Audit publisher not available, skipping audit log")
            return False

        # Get correlation IDs from log context
        context = LogContext.get()

        # Create audit message
        message = AuditLogMessage(
            action=action.value if isinstance(action, AuditAction) else action,
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            payload=payload,
            user_id=user_id,
            request_id=context.get("request_id"),
            trace_id=context.get("trace_id"),
        )

        # Publish to Kafka
        success = producer.produce(
            topic=self.config.audit_logs_topic,
            value=message.to_dict(),
            key=tenant_id,  # Partition by tenant
            headers={
                "service": "gamification",
                "action": message.action,
            },
        )

        if success:
            logger.debug(
                "audit_log_published",
                extra={
                    "action": message.action,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                },
            )

        return success

    def flush(self) -> None:
        """Flush pending messages."""
        if self._producer:
            self._producer.flush()


class ExceptionPublisher:
    """
    Publisher for exception logs.

    Sends exception events to the 'exception-logs' Kafka topic for
    central error tracking and alerting.

    Usage:
        exception_pub = ExceptionPublisher()
        try:
            do_something()
        except Exception as e:
            exception_pub.log(e, tenant_id="t1")
    """

    def __init__(
        self,
        producer: KafkaProducer | None = None,
        config: KafkaConfig | None = None,
    ):
        """
        Initialize exception publisher.

        Args:
            producer: Kafka producer instance
            config: Kafka configuration
        """
        self.config = config or KafkaConfig.from_django_settings()
        self._producer = producer
        self._initialized = False

    def _ensure_producer(self) -> KafkaProducer | None:
        """Lazily initialize the producer."""
        if not self._initialized:
            self._initialized = True
            try:
                if self._producer is None:
                    self._producer = KafkaProducer(self.config)
            except Exception as e:
                logger.warning(f"Failed to initialize exception producer: {e}")
        return self._producer

    def log(
        self,
        error: BaseException,
        tenant_id: str | None = None,
        context: dict[str, Any] | None = None,
        include_traceback: bool = True,
    ) -> bool:
        """
        Publish an exception log entry.

        Args:
            error: The exception to log
            tenant_id: Tenant identifier (if known)
            context: Additional context about the error
            include_traceback: Whether to include the full stack trace

        Returns:
            True if published successfully, False otherwise
        """
        producer = self._ensure_producer()
        if not producer:
            logger.warning("Exception publisher not available, skipping exception log")
            return False

        # Get correlation IDs from log context
        log_ctx = LogContext.get()

        # Build stack trace
        stack_trace = None
        if include_traceback:
            stack_trace = "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )

        # Create exception message
        message = ExceptionLogMessage(
            exception_type=type(error).__name__,
            message=str(error),
            stack_trace=stack_trace,
            tenant_id=tenant_id or log_ctx.get("tenant_id"),
            request_id=log_ctx.get("request_id"),
            trace_id=log_ctx.get("trace_id"),
            context=context,
        )

        # Publish to Kafka
        success = producer.produce(
            topic=self.config.exception_logs_topic,
            value=message.to_dict(),
            key=message.tenant_id or "unknown",
            headers={
                "service": "gamification",
                "exception_type": message.exception_type,
            },
        )

        if success:
            logger.debug(
                "exception_log_published",
                extra={
                    "exception_type": message.exception_type,
                    "message": message.message[:100],  # Truncate for logging
                },
            )

        return success

    def flush(self) -> None:
        """Flush pending messages."""
        if self._producer:
            self._producer.flush()


# Singleton instances for convenience
_audit_publisher: AuditPublisher | None = None
_exception_publisher: ExceptionPublisher | None = None


def get_audit_publisher() -> AuditPublisher:
    """Get or create the default audit publisher instance."""
    global _audit_publisher  # noqa: PLW0603
    if _audit_publisher is None:
        _audit_publisher = AuditPublisher()
    return _audit_publisher


def get_exception_publisher() -> ExceptionPublisher:
    """Get or create the default exception publisher instance."""
    global _exception_publisher  # noqa: PLW0603
    if _exception_publisher is None:
        _exception_publisher = ExceptionPublisher()
    return _exception_publisher


def audit_log(
    action: AuditAction | str,
    entity_type: str,
    entity_id: str,
    tenant_id: str,
    payload: dict[str, Any] | None = None,
    user_id: str | None = None,
) -> bool:
    """
    Convenience function to publish an audit log using the default publisher.

    Args:
        action: Action that was performed
        entity_type: Type of entity
        entity_id: Public ID of the entity
        tenant_id: Tenant identifier
        payload: Additional data
        user_id: User ID

    Returns:
        True if published successfully
    """
    return get_audit_publisher().log(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        tenant_id=tenant_id,
        payload=payload,
        user_id=user_id,
    )


def exception_log(
    error: BaseException,
    tenant_id: str | None = None,
    context: dict[str, Any] | None = None,
) -> bool:
    """
    Convenience function to publish an exception log using the default publisher.

    Args:
        error: The exception to log
        tenant_id: Tenant identifier
        context: Additional context

    Returns:
        True if published successfully
    """
    return get_exception_publisher().log(
        error=error,
        tenant_id=tenant_id,
        context=context,
    )
