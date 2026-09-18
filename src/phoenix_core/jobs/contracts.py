"""Framework-independent Phoenix Core background-job contracts."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping
from uuid import UUID


@dataclass(frozen=True)
class JobRequest:
    """Canonical request for creating or scheduling a Core background job."""

    request_id: str
    job_type: str
    organisation_id: UUID | None = None
    identity_id: UUID | None = None
    payload: Mapping[str, Any] | None = None
    scheduled_at: datetime | None = None
    idempotency_key: str | None = None


@dataclass(frozen=True)
class JobResult:
    """Canonical result returned after a job operation."""

    request_id: str
    job_id: UUID
    status: str
    data: Any = None


class JobExecutor:
    """Framework-independent execution contract for a background job."""

    def execute(self, job_type: str, payload: Mapping[str, Any] | None) -> Any:
        """Execute a registered job operation."""
        raise NotImplementedError
