"""
Scheduler service client for reporting job status.

Per technical guideline §8:
- After executing a job, report status back to Scheduler
- Call ReportJobCompleted or ReportJobFailed
"""

import logging
import os

from shared.scheduler.dispatcher import JobResult, JobStatus

logger = logging.getLogger(__name__)


class SchedulerClient:
    """
    Client for communicating with the Scheduler service.

    Per guideline §8, after executing a job, the service should report
    the status back to the Scheduler (ReportJobCompleted or ReportJobFailed).

    This can be done via gRPC (preferred) or HTTP.

    Usage:
        client = SchedulerClient()

        # After job execution
        if result.status == JobStatus.COMPLETED:
            client.report_completed(job_id, result)
        else:
            client.report_failed(job_id, result)
    """

    def __init__(
        self,
        scheduler_url: str | None = None,
        use_grpc: bool = True,
    ):
        """
        Initialize scheduler client.

        Args:
            scheduler_url: URL of the Scheduler service (defaults to SCHEDULER_SERVICE_URL env var)
            use_grpc: Whether to use gRPC (True) or HTTP (False)
        """
        self.scheduler_url = scheduler_url or os.environ.get(
            "SCHEDULER_SERVICE_URL", "localhost:50052"
        )
        self.use_grpc = use_grpc
        self._grpc_channel = None
        self._grpc_stub = None

    def report_processing(self, job_id: str) -> bool:
        """
        Report that a job has started processing.

        Args:
            job_id: ID of the job being processed

        Returns:
            True if reported successfully
        """
        logger.info(f"Reporting job processing: {job_id}")

        # TODO: Implement gRPC call to Scheduler.ReportJobProcessing
        # For now, just log the status
        return True

    def report_completed(
        self,
        job_id: str,
        result: JobResult | None = None,
    ) -> bool:
        """
        Report that a job has completed successfully.

        Args:
            job_id: ID of the completed job
            result: Optional job result with details

        Returns:
            True if reported successfully
        """
        logger.info(
            f"Reporting job completed: {job_id}",
            extra={
                "message": result.message if result else None,
                "data": result.data if result else None,
            },
        )

        # TODO: Implement gRPC call to Scheduler.ReportJobCompleted
        # The actual implementation would use the scheduler protos from convex-contracts
        # Example implementation:
        #   request = scheduler_pb2.ReportJobCompletedRequest(...)
        #   self._grpc_stub.ReportJobCompleted(request)

        return True

    def report_failed(
        self,
        job_id: str,
        result: JobResult | None = None,
        error_message: str | None = None,
    ) -> bool:
        """
        Report that a job has failed.

        Args:
            job_id: ID of the failed job
            result: Optional job result with error details
            error_message: Optional error message (uses result.error if not provided)

        Returns:
            True if reported successfully
        """
        error = error_message or (result.error if result else "Unknown error")

        logger.error(
            f"Reporting job failed: {job_id}",
            extra={"error": error},
        )

        # TODO: Implement gRPC call to Scheduler.ReportJobFailed
        # Example implementation:
        #   request = scheduler_pb2.ReportJobFailedRequest(...)
        #   self._grpc_stub.ReportJobFailed(request)

        return True

    def report_result(self, job_id: str, result: JobResult) -> bool:
        """
        Report job result (dispatches to completed or failed based on status).

        Args:
            job_id: ID of the job
            result: Job execution result

        Returns:
            True if reported successfully
        """
        if result.status == JobStatus.COMPLETED:
            return self.report_completed(job_id, result)
        else:
            return self.report_failed(job_id, result)

    def close(self) -> None:
        """Close the client and release resources."""
        if self._grpc_channel:
            self._grpc_channel.close()
            self._grpc_channel = None
            self._grpc_stub = None


# Singleton client instance
_client: SchedulerClient | None = None


def get_scheduler_client() -> SchedulerClient:
    """Get or create the default scheduler client."""
    global _client  # noqa: PLW0603
    if _client is None:
        _client = SchedulerClient()
    return _client
