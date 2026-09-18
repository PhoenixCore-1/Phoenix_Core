"""Phase 2.11.7 background-job audit integration tests."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_core.audit.service import AuditService
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.jobs.contracts import JobRequest
from phoenix_core.jobs.service import JobService
from phoenix_core.services import CoreFoundationService


def make_services(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "phoenix.db"))
    core = CoreFoundationService(db)
    core.initialise()

    audit = AuditService(db)
    jobs = JobService(db, audit_service=audit)

    return db, core, jobs, audit


def test_enqueue_records_audit_event(tmp_path):
    db, core, jobs, audit = make_services(tmp_path)

    organisation = core.create_organisation("ACME", "Acme")
    user = core.create_user("alice", "Alice", "StrongPass123!")
    membership = core.add_membership(user.identity_id, organisation.id)

    job = jobs.enqueue(
        JobRequest(
            request_id="REQ-2.11.7-001",
            job_type="test.job",
            organisation_id=organisation.id,
            identity_id=user.identity_id,
        )
    )

    events = audit.list(
        organisation_id=organisation.id,
        target_type="JOB",
        target_id=job.id,
    )

    assert len(events) == 1
    assert events[0].action == "JOB_ENQUEUED"
    assert events[0].organisation_id == organisation.id
    assert events[0].identity_id == user.identity_id
    assert events[0].request_id == job.request_id

    db.close()


def test_system_job_audit_has_no_tenant_or_identity(tmp_path):
    db, core, jobs, audit = make_services(tmp_path)

    job = jobs.enqueue(
        JobRequest(
            request_id="REQ-2.11.7-002",
            job_type="system.job",
        )
    )

    events = audit.list(
        target_type="JOB",
        target_id=job.id,
    )

    assert len(events) == 1
    assert events[0].action == "JOB_ENQUEUED"
    assert events[0].organisation_id is None
    assert events[0].identity_id is None
    assert events[0].request_id == job.request_id

    db.close()


def test_claim_records_audit_event(tmp_path):
    db, core, jobs, audit = make_services(tmp_path)

    organisation = core.create_organisation("ACME", "Acme")
    user = core.create_user("alice", "Alice", "StrongPass123!")
    core.add_membership(user.identity_id, organisation.id)

    job = jobs.enqueue(
        JobRequest(
            request_id="REQ-2.11.7-003",
            job_type="test.job",
            organisation_id=organisation.id,
            identity_id=user.identity_id,
        )
    )

    jobs.claim(job.id)

    events = audit.list(
        organisation_id=organisation.id,
        target_type="JOB",
        target_id=job.id,
    )

    assert [event.action for event in events] == [
        "JOB_CLAIMED",
        "JOB_ENQUEUED",
    ]

    db.close()


def test_complete_records_audit_event(tmp_path):
    db, core, jobs, audit = make_services(tmp_path)

    organisation = core.create_organisation("ACME", "Acme")
    user = core.create_user("alice", "Alice", "StrongPass123!")
    core.add_membership(user.identity_id, organisation.id)

    job = jobs.enqueue(
        JobRequest(
            request_id="REQ-2.11.7-004",
            job_type="test.job",
            organisation_id=organisation.id,
            identity_id=user.identity_id,
        )
    )

    jobs.claim(job.id)
    jobs.complete(job.id)

    events = audit.list(
        organisation_id=organisation.id,
        target_type="JOB",
        target_id=job.id,
    )

    assert [event.action for event in events] == [
        "JOB_COMPLETED",
        "JOB_CLAIMED",
        "JOB_ENQUEUED",
    ]

    db.close()


def test_fail_records_audit_event(tmp_path):
    db, core, jobs, audit = make_services(tmp_path)

    organisation = core.create_organisation("ACME", "Acme")
    user = core.create_user("alice", "Alice", "StrongPass123!")
    core.add_membership(user.identity_id, organisation.id)

    job = jobs.enqueue(
        JobRequest(
            request_id="REQ-2.11.7-005",
            job_type="test.job",
            organisation_id=organisation.id,
            identity_id=user.identity_id,
        )
    )

    jobs.claim(job.id)
    jobs.fail(job.id, "TEST_ERROR", "Test failure")

    events = audit.list(
        organisation_id=organisation.id,
        target_type="JOB",
        target_id=job.id,
    )

    assert [event.action for event in events] == [
        "JOB_FAILED",
        "JOB_CLAIMED",
        "JOB_ENQUEUED",
    ]

    db.close()


def test_retry_records_audit_event(tmp_path):
    db, core, jobs, audit = make_services(tmp_path)

    organisation = core.create_organisation("ACME", "Acme")
    user = core.create_user("alice", "Alice", "StrongPass123!")
    core.add_membership(user.identity_id, organisation.id)

    job = jobs.enqueue(
        JobRequest(
            request_id="REQ-2.11.7-006",
            job_type="test.job",
            organisation_id=organisation.id,
            identity_id=user.identity_id,
        )
    )

    jobs.claim(job.id)
    jobs.fail(job.id, "TEST_ERROR", "Test failure")
    jobs.retry(job.id)

    events = audit.list(
        organisation_id=organisation.id,
        target_type="JOB",
        target_id=job.id,
    )

    assert [event.action for event in events] == [
        "JOB_RETRIED",
        "JOB_FAILED",
        "JOB_CLAIMED",
        "JOB_ENQUEUED",
    ]

    db.close()
