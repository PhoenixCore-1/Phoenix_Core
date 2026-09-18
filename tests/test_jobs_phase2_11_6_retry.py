import pytest

from phoenix_core.errors import ConflictError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.jobs.contracts import JobRequest
from phoenix_core.jobs.service import JobService
from phoenix_core.services import CoreFoundationService


def make_service(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "test.db"))

    core = CoreFoundationService(db)
    core.initialise()

    return db, JobService(db)


def fail_job(service, request_id, max_attempts=3):
    job = service.enqueue(
        JobRequest(
            request_id=request_id,
            job_type="retry.job",
        ),
        max_attempts=max_attempts,
    )

    service.claim(job.id)

    service.fail(
        job.id,
        "EXECUTION_ERROR",
        "Execution failed.",
    )

    return job


def test_failed_job_can_be_retried(tmp_path):
    db, service = make_service(tmp_path)

    job = fail_job(service, "retry-001")

    retried = service.retry(job.id)

    assert retried.status == "QUEUED"
    assert retried.attempt_count == 1
    assert retried.failed_at is None
    assert retried.error_code is None
    assert retried.error_message is None

    db.close()


def test_retry_preserves_attempt_count(tmp_path):
    db, service = make_service(tmp_path)

    job = fail_job(service, "retry-002")

    service.retry(job.id)
    claimed = service.claim(job.id)

    assert claimed.status == "RUNNING"
    assert claimed.attempt_count == 2

    db.close()


def test_retry_can_be_claimed_again(tmp_path):
    db, service = make_service(tmp_path)

    job = fail_job(service, "retry-003")

    service.retry(job.id)
    retried_claim = service.claim(job.id)

    assert retried_claim.status == "RUNNING"
    assert retried_claim.attempt_count == 2

    db.close()


def test_retry_rejected_at_max_attempts(tmp_path):
    db, service = make_service(tmp_path)

    job = fail_job(service, "retry-004", max_attempts=1)

    with pytest.raises(ConflictError):
        service.retry(job.id)

    stored = service.get(job.id)

    assert stored.status == "FAILED"
    assert stored.attempt_count == 1
    assert stored.max_attempts == 1

    db.close()


def test_completed_job_cannot_be_retried(tmp_path):
    db, service = make_service(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="retry-005",
            job_type="retry.job",
        )
    )

    service.claim(job.id)
    service.complete(job.id)

    with pytest.raises(ConflictError):
        service.retry(job.id)

    db.close()


def test_queued_job_cannot_be_retried(tmp_path):
    db, service = make_service(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="retry-006",
            job_type="retry.job",
        )
    )

    with pytest.raises(ConflictError):
        service.retry(job.id)

    db.close()


def test_running_job_cannot_be_retried(tmp_path):
    db, service = make_service(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="retry-007",
            job_type="retry.job",
        )
    )

    service.claim(job.id)

    with pytest.raises(ConflictError):
        service.retry(job.id)

    db.close()
