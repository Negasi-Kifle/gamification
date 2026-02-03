"""
Audit logging module for the Gamification service.

Per technical guideline §6 - Audit: stream to audit service:
- Publishes to 'audit-logs' topic after important actions
- Publishes to 'exception-logs' topic on exceptions
- Uses same message shape as other Convex services

Usage:
    from shared.audit import AuditPublisher, ExceptionPublisher, AuditAction

    # Audit logging
    audit = AuditPublisher()
    audit.log(
        action=AuditAction.FREEBET_CREATED,
        entity_type="CasinoFreeBet",
        entity_id="abc-123",
        tenant_id="t1",
        payload={"name": "Welcome Bonus"},
    )

    # Exception logging
    exception_pub = ExceptionPublisher()
    exception_pub.log(
        error=exception,
        tenant_id="t1",
        context={"request_id": "req-123"},
    )
"""

from shared.audit.models import AuditAction, AuditLogMessage, ExceptionLogMessage
from shared.audit.publisher import AuditPublisher, ExceptionPublisher

__all__ = [
    "AuditAction",
    "AuditLogMessage",
    "AuditPublisher",
    "ExceptionLogMessage",
    "ExceptionPublisher",
]
