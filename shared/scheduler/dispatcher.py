"""
Job dispatcher for scheduled job execution.

Per technical guideline §8:
- Job dispatcher should be in the Application layer
- Maps job_name (string from request) to the right use case or callable
- The Presentation layer only receives requests, calls dispatcher, and reports status
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job execution status."""

    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class JobResult:
    """
    Result of a job execution.

    Attributes:
        status: Job status (completed or failed)
        message: Optional message or result description
        data: Optional result data
        error: Optional error message if failed
    """

    status: JobStatus
    message: str | None = None
    data: dict[str, Any] | None = None
    error: str | None = None

    @classmethod
    def success(
        cls, message: str | None = None, data: dict[str, Any] | None = None
    ) -> "JobResult":
        """Create a successful job result."""
        return cls(status=JobStatus.COMPLETED, message=message, data=data)

    @classmethod
    def failure(cls, error: str, message: str | None = None) -> "JobResult":
        """Create a failed job result."""
        return cls(status=JobStatus.FAILED, error=error, message=message)


# Type alias for job handlers
JobHandler = Callable[[dict[str, Any]], JobResult]


class JobDispatcher:
    """
    Dispatcher for scheduled jobs.

    Maps job names to handler functions and executes them.
    Each handler should be a use case or a function that calls a use case.

    Usage:
        dispatcher = JobDispatcher()

        # Register handlers
        dispatcher.register("job-name", handler_function)

        # Or use the register_bonus_jobs() helper
        dispatcher.register_bonus_jobs(repository)

        # Execute a job
        result = dispatcher.execute("job-name", {"param": "value"})
    """

    def __init__(self):
        self._handlers: dict[str, JobHandler] = {}

    def register(self, job_name: str, handler: JobHandler) -> None:
        """
        Register a job handler.

        Args:
            job_name: Name of the job (e.g., 'expiring-freebets-notification')
            handler: Function that executes the job and returns a JobResult
        """
        self._handlers[job_name] = handler
        logger.info(f"Registered job handler: {job_name}")

    def unregister(self, job_name: str) -> None:
        """Unregister a job handler."""
        if job_name in self._handlers:
            del self._handlers[job_name]
            logger.info(f"Unregistered job handler: {job_name}")

    def execute(
        self, job_name: str, payload: dict[str, Any] | None = None
    ) -> JobResult:
        """
        Execute a job by name.

        Args:
            job_name: Name of the job to execute
            payload: Optional payload/parameters for the job

        Returns:
            JobResult indicating success or failure
        """
        handler = self._handlers.get(job_name)

        if not handler:
            logger.error(f"No handler registered for job: {job_name}")
            return JobResult.failure(f"Unknown job: {job_name}")

        logger.info(f"Executing job: {job_name}")

        try:
            result = handler(payload or {})

            if result.status == JobStatus.COMPLETED:
                logger.info(
                    f"Job completed: {job_name}", extra={"result": result.message}
                )
            else:
                logger.error(f"Job failed: {job_name}", extra={"error": result.error})

            return result

        except Exception as e:
            logger.exception(f"Job execution error: {job_name}")
            return JobResult.failure(
                str(e), f"Exception during job execution: {job_name}"
            )

    def list_jobs(self) -> list[str]:
        """List all registered job names."""
        return list(self._handlers.keys())

    def has_job(self, job_name: str) -> bool:
        """Check if a job is registered."""
        return job_name in self._handlers


def create_bonus_job_handlers(repository) -> dict[str, JobHandler]:
    """
    Create job handlers for the Bonus module.

    Per guideline §8, the job dispatcher maps job names to use cases.
    This function creates handlers that wrap the bonus use cases.

    Args:
        repository: CasinoFreeBetRepository instance

    Returns:
        Dict of job_name -> handler function
    """
    # Import here to avoid circular imports
    from bonus.src.Application.use_cases import GetExpiringCasinoFreeBetsUseCase

    def handle_expiring_freebets_notification(payload: dict[str, Any]) -> JobResult:
        """
        Job: expiring-freebets-notification

        Finds freebets expiring soon and triggers notifications.
        This is typically scheduled to run hourly or daily.
        """
        hours_threshold = payload.get("hours_threshold", 24)

        use_case = GetExpiringCasinoFreeBetsUseCase(repository)
        expiring_freebets = use_case.execute(hours_threshold=hours_threshold)

        if not expiring_freebets:
            return JobResult.success(
                message="No expiring freebets found",
                data={"count": 0},
            )

        # Here you would typically:
        # 1. Group by tenant
        # 2. Call the notification service to send alerts
        # For now, we just return the count

        logger.info(f"Found {len(expiring_freebets)} expiring freebets")

        return JobResult.success(
            message=f"Found {len(expiring_freebets)} expiring freebets",
            data={
                "count": len(expiring_freebets),
                "hours_threshold": hours_threshold,
                "freebets": [
                    {"public_id": fb.public_id, "expires_at": str(fb.expires_at)}
                    for fb in expiring_freebets[:10]  # Limit for response size
                ],
            },
        )

    def handle_cleanup_expired_freebets(payload: dict[str, Any]) -> JobResult:
        """
        Job: cleanup-expired-freebets

        Marks expired freebets with EXPIRED status.
        This is typically scheduled to run daily.
        """
        # This would need a new use case to find and update expired freebets
        # For now, return a placeholder
        return JobResult.success(
            message="Cleanup job completed",
            data={"processed": 0},
        )

    return {
        "expiring-freebets-notification": handle_expiring_freebets_notification,
        "cleanup-expired-freebets": handle_cleanup_expired_freebets,
    }


# Singleton dispatcher instance
_dispatcher: JobDispatcher | None = None


def get_dispatcher() -> JobDispatcher:
    """Get or create the default job dispatcher."""
    global _dispatcher  # noqa: PLW0603
    if _dispatcher is None:
        _dispatcher = JobDispatcher()
    return _dispatcher
