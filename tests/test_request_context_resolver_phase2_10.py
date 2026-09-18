from phoenix_core.api.context import RequestContextResolver
from phoenix_core.errors import AuthenticationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.security.context import RequestContext
from phoenix_core.sessions.service import SessionService
from phoenix_core.services import CoreFoundationService


def make_service(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "test.db"))
    service = CoreFoundationService(db)
    service.initialise()
    return db, service


def setup_user(service, suffix):
    org = service.create_organisation(
        f"ORG-{suffix.upper()}",
        f"Organisation {suffix}",
    )
    user = service.create_user(
        f"user_{suffix}",
        f"User {suffix}",
        "CorrectPassword123!",
    )
    membership = service.add_membership(
        user.identity_id,
        org.id,
    )
    return user, org, membership


def test_resolver_builds_authenticated_context(tmp_path):
    db, service = make_service(tmp_path)
    user, org, _ = setup_user(service, "contextuser")

    session, token = service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    context = RequestContextResolver(db, service).resolve(
        request_id="req-001",
        session_id=session.id,
        organisation_id=org.id,
    )

    assert isinstance(context, RequestContext)
    assert context.request_id == "req-001"
    assert context.session_id == session.id
    assert context.identity_id == user.identity_id
    assert context.organisation_id == org.id
    assert context.permissions == frozenset()
    assert context.entitlements == frozenset()

    db.close()


def test_resolver_rejects_missing_organisation_context(tmp_path):
    db, service = make_service(tmp_path)
    user, org, _ = setup_user(service, "contextmissing")

    session, token = service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    try:
        RequestContextResolver(db, service).resolve(
            request_id="req-002",
            session_id=session.id,
        )
        assert False, "Expected AuthenticationError"
    except AuthenticationError:
        pass

    db.close()


def test_resolver_rejects_organisation_without_membership(tmp_path):
    db, service = make_service(tmp_path)
    user, org, _ = setup_user(service, "contextboundary")

    other_org = service.create_organisation(
        "OTHER",
        "Other Organisation",
    )

    session, token = service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    try:
        RequestContextResolver(db, service).resolve(
            request_id="req-003",
            session_id=session.id,
            organisation_id=other_org.id,
        )
        assert False, "Expected AuthenticationError"
    except AuthenticationError:
        pass

    db.close()


def test_resolver_rejects_revoked_session(tmp_path):
    db, service = make_service(tmp_path)
    user, org, _ = setup_user(service, "contextrevoked")

    session, token = service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    SessionService(db).revoke(session.id)

    try:
        RequestContextResolver(db, service).resolve(
            request_id="req-004",
            session_id=session.id,
            organisation_id=org.id,
        )
        assert False, "Expected AuthenticationError"
    except AuthenticationError:
        pass

    db.close()

def test_resolver_rejects_inactive_identity_session(tmp_path):
    db, service = make_service(tmp_path)
    user, org, _ = setup_user(service, "contextinactive")

    session, token = service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    service.suspend_user(user.id)

    try:
        RequestContextResolver(db, service).resolve(
            request_id="req-005",
            session_id=session.id,
            organisation_id=org.id,
        )
        assert False, "Expected AuthenticationError"
    except AuthenticationError:
        pass

    db.close()


def test_resolver_rejects_suspended_membership(tmp_path):
    db, service = make_service(tmp_path)
    user, org, membership = setup_user(service, "contextmembership")

    session, token = service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    service.suspend_membership(membership.id)

    try:
        RequestContextResolver(db, service).resolve(
            request_id="req-006",
            session_id=session.id,
            organisation_id=org.id,
        )
        assert False, "Expected AuthenticationError"
    except AuthenticationError:
        pass

    db.close()
