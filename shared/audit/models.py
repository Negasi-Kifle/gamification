"""
Audit log message models.

Per technical guideline §6:
- Message shape must match Convex.AuditReport.Contracts
- Required fields: Id, ServiceName, TenantId, Action, EntityType, EntityId, CreatedAt
- Optional: Payload, Message for details
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class AuditAction(str, Enum):
    """
    Audit action types for the Gamification service.

    Add new actions as needed for different operations.
    """

    # Freebet actions
    CASINO_FREEBET_CREATED = "casino_freebet_created"
    CASINO_FREEBET_ACTIVATED = "casino_freebet_activated"
    CASINO_FREEBET_DEACTIVATED = "casino_freebet_deactivated"
    CASINO_FREEBET_USED = "casino_freebet_used"
    CASINO_FREEBET_EXPIRED = "casino_freebet_expired"
    CASINO_FREEBET_DELETED = "casino_freebet_deleted"

    # Campaign actions (future)
    CAMPAIGN_CREATED = "campaign_created"
    CAMPAIGN_ACTIVATED = "campaign_activated"
    CAMPAIGN_DEACTIVATED = "campaign_deactivated"
    CAMPAIGN_ENDED = "campaign_ended"

    # Loyalty actions (future)
    POINTS_AWARDED = "points_awarded"
    POINTS_REDEEMED = "points_redeemed"
    LEVEL_UP = "level_up"

    # Wheel actions (future)
    WHEEL_SPIN = "wheel_spin"
    REWARD_CLAIMED = "reward_claimed"

    # Tournament actions (future)
    TOURNAMENT_JOINED = "tournament_joined"
    TOURNAMENT_COMPLETED = "tournament_completed"
    LEADERBOARD_UPDATED = "leaderboard_updated"

    # Generic actions
    ENTITY_CREATED = "entity_created"
    ENTITY_UPDATED = "entity_updated"
    ENTITY_DELETED = "entity_deleted"


@dataclass
class AuditLogMessage:
    """
    Audit log message structure.

    Matches the message shape used by other Convex services
    (Convex.AuditReport.Contracts).

    Attributes:
        id: Unique message ID (UUID)
        service_name: Name of the service (e.g., 'gamification')
        tenant_id: Tenant identifier
        action: Action that was performed
        entity_type: Type of entity (e.g., 'CasinoFreeBet')
        entity_id: Public ID of the entity
        created_at: Timestamp of the action (ISO 8601)
        payload: Additional data about the action
        user_id: ID of the user who performed the action (if applicable)
        request_id: Correlation ID for the request
        trace_id: Distributed tracing ID
    """

    action: str
    entity_type: str
    entity_id: str
    tenant_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_name: str = "gamification"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    payload: dict[str, Any] | None = None
    user_id: str | None = None
    request_id: str | None = None
    trace_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            "Id": self.id,
            "ServiceName": self.service_name,
            "TenantId": self.tenant_id,
            "Action": self.action,
            "EntityType": self.entity_type,
            "EntityId": self.entity_id,
            "CreatedAt": self.created_at,
        }

        if self.payload:
            data["Payload"] = self.payload
        if self.user_id:
            data["UserId"] = self.user_id
        if self.request_id:
            data["RequestId"] = self.request_id
        if self.trace_id:
            data["TraceId"] = self.trace_id

        return data


@dataclass
class ExceptionLogMessage:
    """
    Exception log message structure.

    Used for logging errors and exceptions to the central audit service.

    Attributes:
        id: Unique message ID (UUID)
        service_name: Name of the service
        tenant_id: Tenant identifier (if known)
        exception_type: Type of exception (e.g., 'ValueError')
        message: Exception message
        stack_trace: Full stack trace
        created_at: Timestamp
        request_id: Correlation ID
        trace_id: Distributed tracing ID
        context: Additional context about the error
    """

    exception_type: str
    message: str
    stack_trace: str | None = None
    tenant_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_name: str = "gamification"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    request_id: str | None = None
    trace_id: str | None = None
    context: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            "Id": self.id,
            "ServiceName": self.service_name,
            "ExceptionType": self.exception_type,
            "Message": self.message,
            "CreatedAt": self.created_at,
        }

        if self.tenant_id:
            data["TenantId"] = self.tenant_id
        if self.stack_trace:
            data["StackTrace"] = self.stack_trace
        if self.request_id:
            data["RequestId"] = self.request_id
        if self.trace_id:
            data["TraceId"] = self.trace_id
        if self.context:
            data["Context"] = self.context

        return data
