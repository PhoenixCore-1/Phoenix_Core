"""Phoenix Core background-job worker boundary."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from phoenix_core.jobs.registry import JobExecutorRegistry
from phoenix_core.jobs.service import JobService


@dataclass(frozen=True)
class WorkerResult:
    """Result returned by a worker execution attempt."""

    job_id: UUID
    status: str
    data: Any = None


class JobWorker:
    """Framework-independent worker for executing registered Core jobs."""

    def __init__(
        self,
        job_service: JobService,
        executor_registry: JobExecutorRegistry,
    ):
        self.job_service = job_service
        self.executor_registry = executor_registry

    def process(self, job_id: UUID) -> WorkerResult:
        job = self.job_service.claim(job_id)

        try:
            executor = self.executor_registry.get(job.job_type)

            data = executor.execute(
                job.job_type,
                job.payload,
            )

            completed = self.job_service.complete(job.id)

            return WorkerResult(
                job_id=completed.id,
                status=completed.status,
                data=data,
            )

        except Exception as exc:
            self.job_service.fail(
                job.id,
                type(exc).__name__,
                str(exc) or "Job execution failed.",
            )
            raise
