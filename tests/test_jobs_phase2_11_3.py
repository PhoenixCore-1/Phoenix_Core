from datetime import datetime, timezone

import pytest
from uuid import uuid4

from phoenix_core.errors import ValidationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.jobs.contracts import JobRequest
from phoenix_core.jobs.service import JobService
from phoenix_core.services import CoreFoundationService


def make_service(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "test.db"))
    core = CoreFoundationService(db)
    core.initialise()
    return db, core, JobService(db)


def make_organisation(core):
    return core.create_organisation(
        f"ORG-{uuid4().hex[:8].upper()}",
        f"Test Organisation {uuid4().hex[:8]}",
    )


def make_user(core):
    return core.create_user(
        f"user_{uuid4().hex[:8]}",
        "Test User",
        "TestPassword123!",
    )


def test_enqueue_creates_queued_job(tmp_path):
    db, core, service = make_service(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="req-001",
            job_type="test.job",
            payload={"value": 123},
        )
    )

    assert job.status == "QUEUED"
    assert job.request_id == "req-001"
    assert job.job_type == "test.job"
    assert job.payload == {"value": 123}
    assert job.attempt_count == 0
    assert job.max_attempts == 3

    stored = service.get(job.id)

    assert stored.id == job.id
    assert stored.status == "QUEUED"
    assert stored.payload == {"value": 123}

    db.close()


def test_enqueue_preserves_organisation_and_identity(tmp_path):
    db, core, service = make_service(tmp_path)

    organisation = make_organisation(core)
    user = make_user(core)

    job = service.enqueue(
        JobRequest(
            request_id="req-002",
            job_type="tenant.job",
            organisation_id=organisation.id,
            identity_id=user.identity_id,
        )
    )

    assert job.organisation_id == organisation.id
    assert job.identity_id == user.identity_id

    stored = service.get(job.id)

    assert stored.organisation_id == organisation.id
    assert stored.identity_id == user.identity_id

    db.close()


def test_enqueue_supports_scheduled_jobs(tmp_path):
    db, core, service = make_service(tmp_path)

    scheduled_at = datetime(2030, 1, 1, tzinfo=timezone.utc)

    job = service.enqueue(
        JobRequest(
            request_id="req-003",
            job_type="scheduled.job",
            scheduled_at=scheduled_at,
        )
    )

    assert job.scheduled_at == scheduled_at
    assert service.get(job.id).scheduled_at == scheduled_at

    db.close()


def test_enqueue_is_idempotent_per_organisation(tmp_path):
    db, core, service = make_service(tmp_path)

    organisation = make_organisation(core)

    first = service.enqueue(
        JobRequest(
            request_id="req-004",
            job_type="duplicate.job",
            organisation_id=organisation.id,
            payload={"value": 1},
            idempotency_key="same-key",
        )
    )

    second = service.enqueue(
        JobRequest(
            request_id="req-005",
            job_type="duplicate.job",
            organisation_id=organisation.id,
            payload={"value": 2},
            idempotency_key="same-key",
        )
    )

    assert second.id == first.id
    assert second.payload == {"value": 1}

    jobs = service.list(organisation_id=organisation.id)

    assert len(jobs) == 1

    db.close()


def test_idempotency_requires_organisation(tmp_path):
    db, core, service = make_service(tmp_path)

    with pytest.raises(ValidationError):
        service.enqueue(
            JobRequest(
                request_id="req-006",
                job_type="invalid.job",
                idempotency_key="key",
            )
        )

    db.close()


def test_empty_idempotency_key_rejected(tmp_path):
    db, core, service = make_service(tmp_path)

    organisation = make_organisation(core)

    with pytest.raises(ValidationError):
        service.enqueue(
            JobRequest(
                request_id="req-007",
                job_type="invalid.job",
                organisation_id=organisation.id,
                idempotency_key="   ",
            )
        )

    db.close()


def test_custom_retry_limit_persisted(tmp_path):
    db, core, service = make_service(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="req-008",
            job_type="retry.job",
        ),
        max_attempts=7,
    )

    assert job.max_attempts == 7
    assert service.get(job.id).max_attempts == 7

    db.close()


def test_invalid_retry_limit_rejected(tmp_path):
    db, core, service = make_service(tmp_path)

    with pytest.raises(ValidationError):
        service.enqueue(
            JobRequest(
                request_id="req-009",
                job_type="retry.job",
            ),
            max_attempts=0,
        )

    db.close()


def test_list_filters_by_status_and_type(tmp_path):
    db, core, service = make_service(tmp_path)

    service.enqueue(
        JobRequest(
            request_id="req-010",
            job_type="email.send",
        )
    )

    service.enqueue(
        JobRequest(
            request_id="req-011",
            job_type="report.generate",
        )
    )

    email_jobs = service.list(
        status="QUEUED",
        job_type="email.send",
    )

    assert len(email_jobs) == 1
    assert email_jobs[0].job_type == "email.send"

    db.close()


def test_list_pagination(tmp_path):
    db, core, service = make_service(tmp_path)

    for index in range(5):
        service.enqueue(
            JobRequest(
                request_id=f"req-page-{index}",
                job_type="page.job",
            )
        )

    first_page = service.list(limit=2, offset=0)
    second_page = service.list(limit=2, offset=2)

    assert len(first_page) == 2
    assert len(second_page) == 2
    assert first_page[0].id != second_page[0].id

    db.close()


def test_invalid_list_parameters_rejected(tmp_path):
    db, core, service = make_service(tmp_path)

    with pytest.raises(ValidationError):
        service.list(limit=0)

    with pytest.raises(ValidationError):
        service.list(limit=501)

    with pytest.raises(ValidationError):
        service.list(offset=-1)

    with pytest.raises(ValidationError):
        service.list(status="INVALID")

    db.close()
