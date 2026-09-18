from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from phoenix_core.errors import ValidationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.jobs.contracts import JobRequest
from phoenix_core.jobs.service import JobService
from phoenix_core.services import CoreFoundationService


def make_service(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "test.db"))

    core = CoreFoundationService(db)
    core.initialise()

    return db, JobService(db)


def test_get_due_jobs_returns_immediate_jobs(tmp_path):
    db, service = make_service(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="due-001",
            job_type="due.job",
        )
    )

    jobs = service.get_due_jobs()

    assert [item.id for item in jobs] == [job.id]

    db.close()


def test_get_due_jobs_excludes_future_jobs(tmp_path):
    db, service = make_service(tmp_path)

    future_job = service.enqueue(
        JobRequest(
            request_id="due-002",
            job_type="due.job",
            scheduled_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
    )

    jobs = service.get_due_jobs()

    assert future_job.id not in [item.id for item in jobs]

    db.close()


def test_get_due_jobs_includes_due_scheduled_jobs(tmp_path):
    db, service = make_service(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="due-003",
            job_type="due.job",
            scheduled_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
    )

    jobs = service.get_due_jobs()

    assert [item.id for item in jobs] == [job.id]

    db.close()


def test_get_due_jobs_only_returns_queued_jobs(tmp_path):
    db, service = make_service(tmp_path)

    queued = service.enqueue(
        JobRequest(
            request_id="due-004",
            job_type="due.job",
        )
    )

    running = service.enqueue(
        JobRequest(
            request_id="due-005",
            job_type="due.job",
        )
    )
    service.claim(running.id)

    completed = service.enqueue(
        JobRequest(
            request_id="due-006",
            job_type="due.job",
        )
    )
    service.claim(completed.id)
    service.complete(completed.id)

    failed = service.enqueue(
        JobRequest(
            request_id="due-007",
            job_type="due.job",
        )
    )
    service.claim(failed.id)
    service.fail(
        failed.id,
        "TEST_ERROR",
        "Execution failed.",
    )

    jobs = service.get_due_jobs()

    assert [item.id for item in jobs] == [queued.id]

    db.close()


def test_get_due_jobs_filters_by_organisation(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "test.db"))
    core = CoreFoundationService(db)
    core.initialise()
    service = JobService(db)

    organisation_a = core.create_organisation("ORG-A", "Organisation A")
    organisation_b = core.create_organisation("ORG-B", "Organisation B")

    job_a = service.enqueue(
        JobRequest(
            request_id="due-008",
            job_type="due.job",
            organisation_id=organisation_a.id,
        )
    )

    job_b = service.enqueue(
        JobRequest(
            request_id="due-009",
            job_type="due.job",
            organisation_id=organisation_b.id,
        )
    )

    jobs = service.get_due_jobs(
        organisation_id=organisation_a.id,
    )

    assert [item.id for item in jobs] == [job_a.id]
    assert job_b.id not in [item.id for item in jobs]

    db.close()


def test_get_due_jobs_filters_by_job_type(tmp_path):
    db, service = make_service(tmp_path)

    job_a = service.enqueue(
        JobRequest(
            request_id="due-010",
            job_type="email.send",
        )
    )

    job_b = service.enqueue(
        JobRequest(
            request_id="due-011",
            job_type="report.generate",
        )
    )

    jobs = service.get_due_jobs(
        job_type="email.send",
    )

    assert [item.id for item in jobs] == [job_a.id]
    assert job_b.id not in [item.id for item in jobs]

    db.close()


def test_get_due_jobs_respects_limit(tmp_path):
    db, service = make_service(tmp_path)

    for index in range(5):
        service.enqueue(
            JobRequest(
                request_id=f"due-limit-{index}",
                job_type="due.job",
            )
        )

    jobs = service.get_due_jobs(limit=2)

    assert len(jobs) == 2

    db.close()


def test_get_due_jobs_rejects_invalid_limit(tmp_path):
    db, service = make_service(tmp_path)

    with pytest.raises(ValidationError):
        service.get_due_jobs(limit=0)

    with pytest.raises(ValidationError):
        service.get_due_jobs(limit=501)

    db.close()


def test_get_due_jobs_rejects_empty_job_type(tmp_path):
    db, service = make_service(tmp_path)

    with pytest.raises(ValidationError):
        service.get_due_jobs(job_type="")

    db.close()
