from uuid import uuid4

import pytest

from phoenix_core.errors import ConflictError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.jobs.contracts import JobRequest
from phoenix_core.jobs.service import JobService
from phoenix_core.services import CoreFoundationService


def make_services(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "test.db"))
    core = CoreFoundationService(db)
    core.initialise()
    return db, JobService(db)


def test_claim_moves_queued_job_to_running(tmp_path):
    db, service = make_services(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="claim-001",
            job_type="claim.job",
        )
    )

    claimed = service.claim(job.id)

    assert claimed.status == "RUNNING"
    assert claimed.attempt_count == 1
    assert claimed.started_at is not None

    db.close()


def test_claim_only_allows_queued_jobs(tmp_path):
    db, service = make_services(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="claim-002",
            job_type="claim.job",
        )
    )

    service.claim(job.id)

    with pytest.raises(ConflictError):
        service.claim(job.id)

    db.close()


def test_claim_does_not_increment_attempt_on_failed_claim(tmp_path):
    db, service = make_services(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="claim-003",
            job_type="claim.job",
        )
    )

    service.claim(job.id)

    with pytest.raises(ConflictError):
        service.claim(job.id)

    stored = service.get(job.id)

    assert stored.attempt_count == 1
    assert stored.status == "RUNNING"

    db.close()


def test_claim_unknown_job_rejected(tmp_path):
    db, service = make_services(tmp_path)

    with pytest.raises(ConflictError):
        service.claim(uuid4())

    db.close()
