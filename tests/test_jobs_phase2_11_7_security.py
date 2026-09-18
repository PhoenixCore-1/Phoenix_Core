from uuid import uuid4

import pytest

from phoenix_core.errors import AuthorizationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.jobs.contracts import JobRequest
from phoenix_core.jobs.security import JobSecurityService
from phoenix_core.jobs.service import JobService
from phoenix_core.security.context import RequestContext
from phoenix_core.services import CoreFoundationService


def make_service(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "test.db"))
    core = CoreFoundationService(db)
    core.initialise()
    jobs = JobService(db)
    security = JobSecurityService(db, core)
    return db, core, jobs, security


def make_organisation(core, suffix=None):
    suffix = suffix or uuid4().hex[:8].upper()
    return core.create_organisation(
        f"ORG-{suffix}",
        f"Test Organisation {suffix}",
    )


def make_user(core, suffix=None):
    suffix = suffix or uuid4().hex[:8]
    return core.create_user(
        f"user_{suffix}",
        "Test User",
        "TestPassword123!",
    )


def test_tenant_job_requires_active_membership(tmp_path):
    db, core, jobs, security = make_service(tmp_path)

    organisation = make_organisation(core)
    user = make_user(core)

    job = jobs.enqueue(
        JobRequest(
            request_id="security-001",
            job_type="tenant.job",
            organisation_id=organisation.id,
            identity_id=user.identity_id,
        )
    )

    with pytest.raises(AuthorizationError):
        security.validate_execution(job)

    db.close()


def test_tenant_job_allows_active_member(tmp_path):
    db, core, jobs, security = make_service(tmp_path)

    organisation = make_organisation(core)
    user = make_user(core)

    core.add_membership(user.identity_id, organisation.id)

    job = jobs.enqueue(
        JobRequest(
            request_id="security-002",
            job_type="tenant.job",
            organisation_id=organisation.id,
            identity_id=user.identity_id,
        )
    )

    security.validate_execution(job)

    db.close()


def test_cross_tenant_context_rejected(tmp_path):
    db, core, jobs, security = make_service(tmp_path)

    organisation_a = make_organisation(core, "A")
    organisation_b = make_organisation(core, "B")
    user = make_user(core)

    core.add_membership(user.identity_id, organisation_a.id)

    job = jobs.enqueue(
        JobRequest(
            request_id="security-003",
            job_type="tenant.job",
            organisation_id=organisation_a.id,
            identity_id=user.identity_id,
        )
    )

    context = RequestContext(
        request_id="security-context-003",
        identity_id=user.identity_id,
        organisation_id=organisation_b.id,
    )

    with pytest.raises(AuthorizationError):
        security.validate_execution(job, context)

    db.close()


def test_cross_identity_context_rejected(tmp_path):
    db, core, jobs, security = make_service(tmp_path)

    organisation = make_organisation(core)
    user_a = make_user(core, "A")
    user_b = make_user(core, "B")

    core.add_membership(user_a.identity_id, organisation.id)
    core.add_membership(user_b.identity_id, organisation.id)

    job = jobs.enqueue(
        JobRequest(
            request_id="security-004",
            job_type="tenant.job",
            organisation_id=organisation.id,
            identity_id=user_a.identity_id,
        )
    )

    context = RequestContext(
        request_id="security-context-004",
        identity_id=user_b.identity_id,
        organisation_id=organisation.id,
    )

    with pytest.raises(AuthorizationError):
        security.validate_execution(job, context)

    db.close()


def test_inactive_identity_rejected(tmp_path):
    db, core, jobs, security = make_service(tmp_path)

    organisation = make_organisation(core)
    user = make_user(core)

    core.add_membership(user.identity_id, organisation.id)

    job = jobs.enqueue(
        JobRequest(
            request_id="security-005",
            job_type="tenant.job",
            organisation_id=organisation.id,
            identity_id=user.identity_id,
        )
    )

    core.deactivate_user(user.id)

    with pytest.raises(AuthorizationError):
        security.validate_execution(job)

    db.close()


def test_inactive_organisation_rejected(tmp_path):
    db, core, jobs, security = make_service(tmp_path)

    organisation = make_organisation(core)
    user = make_user(core)

    core.add_membership(user.identity_id, organisation.id)

    job = jobs.enqueue(
        JobRequest(
            request_id="security-006",
            job_type="tenant.job",
            organisation_id=organisation.id,
            identity_id=user.identity_id,
        )
    )

    core.suspend_organisation(organisation.id)

    with pytest.raises(AuthorizationError):
        security.validate_execution(job)

    db.close()


def test_missing_permission_rejected(tmp_path):
    db, core, jobs, security = make_service(tmp_path)

    organisation = make_organisation(core)
    user = make_user(core)

    core.add_membership(user.identity_id, organisation.id)

    job = jobs.enqueue(
        JobRequest(
            request_id="security-007",
            job_type="protected.job",
            organisation_id=organisation.id,
            identity_id=user.identity_id,
        )
    )

    with pytest.raises(AuthorizationError):
        security.validate_execution(
            job,
            required_permission="jobs.execute",
        )

    db.close()


def test_system_job_requires_no_user_context(tmp_path):
    db, core, jobs, security = make_service(tmp_path)

    job = jobs.enqueue(
        JobRequest(
            request_id="security-008",
            job_type="system.job",
        )
    )

    security.validate_execution(job)

    db.close()


def test_system_job_rejects_user_context(tmp_path):
    db, core, jobs, security = make_service(tmp_path)

    job = jobs.enqueue(
        JobRequest(
            request_id="security-009",
            job_type="system.job",
        )
    )

    context = RequestContext(
        request_id="security-context-009",
        identity_id=uuid4(),
        organisation_id=uuid4(),
    )

    with pytest.raises(AuthorizationError):
        security.validate_execution(job, context)

    db.close()


def test_partial_tenant_context_rejected(tmp_path):
    db, core, jobs, security = make_service(tmp_path)

    organisation = make_organisation(core)

    job = jobs.enqueue(
        JobRequest(
            request_id="security-010",
            job_type="invalid.job",
            organisation_id=organisation.id,
        )
    )

    with pytest.raises(AuthorizationError):
        security.validate_execution(job)

    db.close()
