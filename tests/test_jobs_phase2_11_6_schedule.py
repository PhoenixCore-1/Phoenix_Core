from datetime import datetime, timedelta, timezone

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


def test_job_without_schedule_can_be_claimed(tmp_path):
    db, service = make_service(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="schedule-001",
            job_type="schedule.job",
        )
    )

    claimed = service.claim(job.id)

    assert claimed.status == "RUNNING"
    assert claimed.attempt_count == 1

    db.close()


def test_future_scheduled_job_cannot_be_claimed(tmp_path):
    db, service = make_service(tmp_path)

    scheduled_at = datetime.now(timezone.utc) + timedelta(hours=1)

    job = service.enqueue(
        JobRequest(
            request_id="schedule-002",
            job_type="schedule.job",
            scheduled_at=scheduled_at,
        )
    )

    with pytest.raises(ConflictError):
        service.claim(job.id)

    stored = service.get(job.id)

    assert stored.status == "QUEUED"
    assert stored.attempt_count == 0
    assert stored.started_at is None

    db.close()


def test_due_scheduled_job_can_be_claimed(tmp_path):
    db, service = make_service(tmp_path)

    scheduled_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    job = service.enqueue(
        JobRequest(
            request_id="schedule-003",
            job_type="schedule.job",
            scheduled_at=scheduled_at,
        )
    )

    claimed = service.claim(job.id)

    assert claimed.status == "RUNNING"
    assert claimed.attempt_count == 1
    assert claimed.started_at is not None

    db.close()


def test_current_time_scheduled_job_can_be_claimed(tmp_path):
    db, service = make_service(tmp_path)

    scheduled_at = datetime.now(timezone.utc)

    job = service.enqueue(
        JobRequest(
            request_id="schedule-004",
            job_type="schedule.job",
            scheduled_at=scheduled_at,
        )
    )

    claimed = service.claim(job.id)

    assert claimed.status == "RUNNING"
    assert claimed.attempt_count == 1

    db.close()


def test_future_schedule_does_not_increment_attempt_count(tmp_path):
    db, service = make_service(tmp_path)

    scheduled_at = datetime.now(timezone.utc) + timedelta(hours=1)

    job = service.enqueue(
        JobRequest(
            request_id="schedule-005",
            job_type="schedule.job",
            scheduled_at=scheduled_at,
        )
    )

    with pytest.raises(ConflictError):
        service.claim(job.id)

    stored = service.get(job.id)

    assert stored.attempt_count == 0
    assert stored.status == "QUEUED"

    db.close()
