"""
Bonus module job dispatcher.

Per technical guideline §8, the job dispatcher:
- Lives in the Application layer
- Maps job_name (string) to the right use case or callable
- Is called by the Presentation layer (gRPC servicer or HTTP view)

Example flow:
1. Scheduler calls ExecuteJob(job_name="expiring-freebets-notification")
2. Presentation layer receives request
3. Presentation calls BonusJobDispatcher.execute(job_name)
4. Dispatcher finds handler and executes use case
5. Presentation reports result to Scheduler via SchedulerClient
"""

import logging
from typing import Any

from bonus.src.Application.use_cases import GetExpiringCasinoFreeBetsUseCase
from bonus.src.Domain.repositories import CasinoFreeBetRepositoryInterface
from shared.scheduler.dispatcher import JobDispatcher, JobResult

logger = logging.getLogger(__name__)


class BonusJobDispatcher:
    """
    Job dispatcher for the Bonus module.
    Extends the shared JobDispatcher with Bonus-specific job handlers.

    Usage:
        # With dependency injection
        dispatcher = BonusJobDispatcher(repository)
        result = dispatcher.execute("expiring-freebets-notification", {})

        # Or use the global instance
        from bonus.src.Application.jobs import get_bonus_dispatcher
        dispatcher = get_bonus_dispatcher(repository)
    """

    # Job name constants
    JOB_EXPIRING_FREEBETS_NOTIFICATION = "expiring-freebets-notification"
    JOB_CLEANUP_EXPIRED_FREEBETS = "cleanup-expired-freebets"

    def __init__(self, repository: CasinoFreeBetRepositoryInterface):
        """
        Initialize the bonus job dispatcher.

        Args:
            repository: Repository for casino freebets
        """
        self._repository = repository
        self._dispatcher = JobDispatcher()
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all bonus job handlers."""
        self._dispatcher.register(
            self.JOB_EXPIRING_FREEBETS_NOTIFICATION,
            self._handle_expiring_freebets_notification,
        )
        self._dispatcher.register(
            self.JOB_CLEANUP_EXPIRED_FREEBETS,
            self._handle_cleanup_expired_freebets,
        )

    def execute(
        self, job_name: str, payload: dict[str, Any] | None = None
    ) -> JobResult:
        """
        Execute a job by name.

        Args:
            job_name: Name of the job to execute
            payload: Optional parameters for the job

        Returns:
            JobResult with status and details
        """
        return self._dispatcher.execute(job_name, payload)

    def list_jobs(self) -> list[str]:
        """List all registered job names."""
        return self._dispatcher.list_jobs()

    def _handle_expiring_freebets_notification(
        self, payload: dict[str, Any]
    ) -> JobResult:
        """
        Job: expiring-freebets-notification

        Finds freebets that are expiring within a threshold and prepares
        notification data. Typically scheduled to run hourly.

        Payload:
            hours_threshold (int): Hours until expiry (default: 24)

        Next steps (to be implemented):
            - Group expiring freebets by tenant
            - Call notification service for each tenant
        """
        hours_threshold = payload.get("hours_threshold", 24)

        logger.info(
            "Running expiring freebets notification job",
            extra={"hours_threshold": hours_threshold},
        )

        try:
            # Execute use case
            use_case = GetExpiringCasinoFreeBetsUseCase(self._repository)
            expiring_freebets = use_case.execute(hours_threshold=hours_threshold)

            count = len(expiring_freebets)

            if count == 0:
                return JobResult.success(
                    message="No freebets expiring soon",
                    data={"count": 0, "hours_threshold": hours_threshold},
                )

            # Group by tenant for notification
            by_tenant: dict[str, list] = {}
            for fb in expiring_freebets:
                tenant_id = fb.tenant_id
                if tenant_id not in by_tenant:
                    by_tenant[tenant_id] = []
                by_tenant[tenant_id].append(
                    {
                        "public_id": fb.public_id,
                        "name": fb.name,
                        "expires_at": fb.expires_at.isoformat()
                        if fb.expires_at
                        else None,
                        "total_value": str(fb.total_value),
                    }
                )

            # TODO: Call notification service for each tenant
            #   Example implementation:
            #   notification_client.send_expiring_freebets_alert(tenant_id, freebets)

            logger.info(
                f"Found {count} expiring freebets across {len(by_tenant)} tenants",
                extra={"count": count, "tenants": len(by_tenant)},
            )

            return JobResult.success(
                message=f"Found {count} freebets expiring within {hours_threshold} hours",
                data={
                    "count": count,
                    "hours_threshold": hours_threshold,
                    "tenants_affected": len(by_tenant),
                    "by_tenant": {
                        tenant_id: len(freebets)
                        for tenant_id, freebets in by_tenant.items()
                    },
                },
            )

        except Exception as e:
            logger.exception("Error in expiring freebets notification job")
            return JobResult.failure(str(e), "Failed to process expiring freebets")

    def _handle_cleanup_expired_freebets(self, payload: dict[str, Any]) -> JobResult:
        """
        Job: cleanup-expired-freebets

        Finds freebets that have passed their expiry time but still have
        ACTIVE or INACTIVE status, and marks them as EXPIRED.
        Typically scheduled to run daily.

        Note: This requires a new use case to update expired freebets.
        For now, returns a placeholder result.
        """
        logger.info("Running cleanup expired freebets job")

        # TODO: Implement use case for updating expired freebets
        # Steps:
        # 1. Find all freebets where status is ACTIVE/INACTIVE
        # 2. Filter those where expiry_time < now
        # 3. Update status to EXPIRED
        # 4. Publish audit logs for each update

        return JobResult.success(
            message="Cleanup job completed (not yet implemented)",
            data={"processed": 0},
        )


# Singleton instance
_bonus_dispatcher: BonusJobDispatcher | None = None


def get_bonus_dispatcher(
    repository: CasinoFreeBetRepositoryInterface,
) -> BonusJobDispatcher:
    """
    Get or create the bonus job dispatcher.

    Args:
        repository: Repository instance (required for first call)

    Returns:
        BonusJobDispatcher instance
    """
    global _bonus_dispatcher  # noqa: PLW0603
    if _bonus_dispatcher is None:
        _bonus_dispatcher = BonusJobDispatcher(repository)
    return _bonus_dispatcher
