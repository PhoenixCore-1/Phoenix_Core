"""Phoenix Core background-job executor registry."""

from phoenix_core.errors import ConflictError, NotFoundError, ValidationError
from phoenix_core.jobs.contracts import JobExecutor


class JobExecutorRegistry:
    """Authoritative registry for background-job executors."""

    def __init__(self):
        self._executors: dict[str, JobExecutor] = {}

    def register(self, job_type: str, executor: JobExecutor) -> None:
        if not job_type or not job_type.strip():
            raise ValidationError("job_type is required.")

        if executor is None:
            raise ValidationError("executor is required.")

        key = job_type.strip()

        if key in self._executors:
            raise ConflictError(
                f"Executor already registered for job type '{key}'."
            )

        self._executors[key] = executor

    def unregister(self, job_type: str) -> bool:
        if not job_type or not job_type.strip():
            raise ValidationError("job_type is required.")

        return self._executors.pop(job_type.strip(), None) is not None

    def get(self, job_type: str) -> JobExecutor:
        if not job_type or not job_type.strip():
            raise ValidationError("job_type is required.")

        key = job_type.strip()
        executor = self._executors.get(key)

        if executor is None:
            raise NotFoundError(
                f"No executor registered for job type '{key}'."
            )

        return executor

    def has(self, job_type: str) -> bool:
        if not job_type or not job_type.strip():
            return False

        return job_type.strip() in self._executors

    def list_types(self) -> tuple[str, ...]:
        return tuple(sorted(self._executors))
