"""
Scheduler integration module for the Gamification service.

Per technical guideline §8 - Scheduler (cron jobs) integration:
- Receives ExecuteJob requests from the central Scheduler service
- Maps job names to handlers (use cases)
- Reports job status back to Scheduler (completed/failed)

Same pattern as Identity and Payment services.

Usage:
    from shared.scheduler import JobDispatcher, SchedulerClient

    # Register jobs
    dispatcher = JobDispatcher()
    dispatcher.register("expiring-freebets-notification", handle_expiring_freebets)

    # Execute a job (called from gRPC servicer)
    result = dispatcher.execute("expiring-freebets-notification", payload={})

    # Report status to Scheduler
    client = SchedulerClient()
    client.report_completed(job_id, result)
"""

from shared.scheduler.client import SchedulerClient
from shared.scheduler.dispatcher import JobDispatcher, JobHandler, JobResult

__all__ = [
    "JobDispatcher",
    "JobHandler",
    "JobResult",
    "SchedulerClient",
]
