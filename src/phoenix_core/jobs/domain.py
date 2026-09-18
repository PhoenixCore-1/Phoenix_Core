"""Phoenix Core background-job domain model."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import UUID, uuid4


JOB_STATUSES = frozenset({
    "QUEUED",
    "RUNNING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
})


@dataclass(frozen=True)
class Job:
    id: UUID
    request_id: str
    job_type: str
    organisation_id: UUID | None
    identity_id: UUID | None
    payload: Mapping[str, Any] | None
    status: str
    scheduled_at: datetime | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    failed_at: datetime | None
    attempt_count: int
    max_attempts: int
    idempotency_key: str | None
    error_code: str | None
    error_message: str | None

    @staticmethod
    def create(
        request_id: str,
        job_type: str,
        *,
        organisation_id: UUID | None = None,
        identity_id: UUID | None = None,
        payload: Mapping[str, Any] | None = None,
        scheduled_at: datetime | None = None,
        idempotency_key: str | None = None,
        max_attempts: int = 3,
    ) -> "Job":
        if not request_id or not request_id.strip():
            raise ValueError("request_id is required.")

        if not job_type or not job_type.strip():
            raise ValueError("job_type is required.")

        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")

        return Job(
            id=uuid4(),
            request_id=request_id,
            job_type=job_type.strip(),
            organisation_id=organisation_id,
            identity_id=identity_id,
            payload=payload,
            status="QUEUED",
            scheduled_at=scheduled_at,
            created_at=datetime.now(timezone.utc),
            started_at=None,
            completed_at=None,
            failed_at=None,
            attempt_count=0,
            max_attempts=max_attempts,
            idempotency_key=idempotency_key,
            error_code=None,
            error_message=None,
        )
