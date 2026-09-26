from phoenix_core.api.application import CoreApi
from phoenix_core.api.context import RequestContextResolver
from phoenix_core.errors import AuthenticationError, AuthorizationError, AuthorizationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.security.context import RequestContext
from phoenix_core.sessions.service import SessionService



def make_service(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "test.db"))
    service = CoreApi(db)
    db.initialise_schema()
    return db, service


def setup_user(service, suffix):
    org = service.organisation_service.create_organisation(
        code=f"ORG-{suffix.upper()}",
        name=f"Organisation {suffix}",
    )
    user = service.user_service.create_user(
        username=f"user_{suffix}",
        display_name=f"User {suffix}",
        password="CorrectPassword123!",
    )
    membership = service.company_membership_service.add_membership(
        user.identity_id,
        org.id,
    )
    return user, org, membership


def test_resolver_builds_authenticated_context(tmp_path):
    db, service = make_service(tmp_path)
    user, org, _ = setup_user(service, "contextuser")

    session, token, _ = service.authentication_service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    context = RequestContextResolver(db, service.entitlement_service).resolve(
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

    session, token, _ = service.authentication_service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    try:
        RequestContextResolver(db, service.entitlement_service).resolve(
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

    other_org = service.organisation_service.create_organisation(
        code="OTHER",
        name="Other Organisation",
    )

    session, token, _ = service.authentication_service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    try:
        RequestContextResolver(db, service.entitlement_service).resolve(
            request_id="req-003",
            session_id=session.id,
            organisation_id=other_org.id,
        )
        assert False, "Expected AuthorizationError"
    except AuthorizationError:
        pass

    db.close()


def test_resolver_rejects_revoked_session(tmp_path):
    db, service = make_service(tmp_path)
    user, org, _ = setup_user(service, "contextrevoked")

    session, token, _ = service.authentication_service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    SessionService(db).revoke(session.id)

    try:
        RequestContextResolver(db, service.entitlement_service).resolve(
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

    session, token, _ = service.authentication_service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    service.user_service.deactivate_user(user.id)

    try:
        RequestContextResolver(db, service.entitlement_service).resolve(
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

    session, token, _ = service.authentication_service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    service.company_membership_service.suspend_membership(membership.id)

    try:
        RequestContextResolver(db, service.entitlement_service).resolve(
            request_id="req-006",
            session_id=session.id,
            organisation_id=org.id,
        )
        assert False, "Expected AuthorizationError"
    except AuthorizationError:
        pass

    db.close()
