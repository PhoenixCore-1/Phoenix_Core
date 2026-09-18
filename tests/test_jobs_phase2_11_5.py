from uuid import uuid4

import pytest

from phoenix_core.errors import ConflictError, ValidationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.jobs.contracts import JobRequest
from phoenix_core.jobs.service import JobService
from phoenix_core.services import CoreFoundationService


def make_service(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "test.db"))

    core = CoreFoundationService(db)
    core.initialise()

    return db, JobService(db)


def test_complete_running_job(tmp_path):
    db, service = make_service(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="lifecycle-001",
            job_type="lifecycle.job",
        )
    )

    service.claim(job.id)
    completed = service.complete(job.id)

    assert completed.status == "COMPLETED"
    assert completed.completed_at is not None
    assert completed.attempt_count == 1

    db.close()


def test_completed_job_cannot_be_completed_again(tmp_path):
    db, service = make_service(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="lifecycle-002",
            job_type="lifecycle.job",
        )
    )

    service.claim(job.id)
    service.complete(job.id)

    with pytest.raises(ConflictError):
        service.complete(job.id)

    db.close()


def test_completed_job_cannot_be_failed(tmp_path):
    db, service = make_service(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="lifecycle-003",
            job_type="lifecycle.job",
        )
    )

    service.claim(job.id)
    service.complete(job.id)

    with pytest.raises(ConflictError):
        service.fail(
            job.id,
            "TEST_ERROR",
            "This should not be recorded.",
        )

    db.close()


def test_fail_running_job(tmp_path):
    db, service = make_service(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="lifecycle-004",
            job_type="lifecycle.job",
        )
    )

    service.claim(job.id)

    failed = service.fail(
        job.id,
        "EXECUTION_ERROR",
        "Executor failed during processing.",
    )

    assert failed.status == "FAILED"
    assert failed.failed_at is not None
    assert failed.error_code == "EXECUTION_ERROR"
    assert failed.error_message == "Executor failed during processing."
    assert failed.attempt_count == 1

    db.close()


def test_failed_job_cannot_be_completed(tmp_path):
    db, service = make_service(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="lifecycle-005",
            job_type="lifecycle.job",
        )
    )

    service.claim(job.id)
    service.fail(
        job.id,
        "EXECUTION_ERROR",
        "Execution failed.",
    )

    with pytest.raises(ConflictError):
        service.complete(job.id)

    db.close()


def test_fail_requires_error_code(tmp_path):
    db, service = make_service(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="lifecycle-006",
            job_type="lifecycle.job",
        )
    )

    service.claim(job.id)

    with pytest.raises(ValidationError):
        service.fail(
            job.id,
            "",
            "Execution failed.",
        )

    stored = service.get(job.id)

    assert stored.status == "RUNNING"

    db.close()


def test_fail_requires_error_message(tmp_path):
    db, service = make_service(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="lifecycle-007",
            job_type="lifecycle.job",
        )
    )

    service.claim(job.id)

    with pytest.raises(ValidationError):
        service.fail(
            job.id,
            "EXECUTION_ERROR",
            "",
        )

    stored = service.get(job.id)

    assert stored.status == "RUNNING"

    db.close()


def test_queued_job_cannot_be_completed(tmp_path):
    db, service = make_service(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="lifecycle-008",
            job_type="lifecycle.job",
        )
    )

    with pytest.raises(ConflictError):
        service.complete(job.id)

    db.close()


def test_queued_job_cannot_be_failed(tmp_path):
    db, service = make_service(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="lifecycle-009",
            job_type="lifecycle.job",
        )
    )

    with pytest.raises(ConflictError):
        service.fail(
            job.id,
            "EXECUTION_ERROR",
            "Job was never running.",
        )

    db.close()


def test_unknown_job_cannot_be_completed(tmp_path):
    db, service = make_service(tmp_path)

    with pytest.raises(ConflictError):
        service.complete(uuid4())

    db.close()


def test_unknown_job_cannot_be_failed(tmp_path):
    db, service = make_service(tmp_path)

    with pytest.raises(ConflictError):
        service.fail(
            uuid4(),
            "EXECUTION_ERROR",
            "Unknown job.",
        )

    db.close()
