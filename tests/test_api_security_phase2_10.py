from phoenix_core.api.application import CoreApi
from phoenix_core.errors import AuthenticationError, AuthorizationError


def make_service(tmp_path):
    from phoenix_core.infrastructure import SQLiteDatabase
    from phoenix_core.services import CoreFoundationService

    db = SQLiteDatabase(str(tmp_path / "security.db"))
    service = CoreFoundationService(db)
    service.initialise()
    return db, service


def setup_user(service, code="SEC-TEST", username="securityuser"):
    org = service.create_organisation(
        code,
        "Security Test Organisation",
    )
    user = service.create_user(
        username,
        "Security User",
        "CorrectPassword123!",
    )
    service.add_membership(user.identity_id, org.id)
    return user, org


def test_api_rejects_revoked_session(tmp_path):
    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    session, token = service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    service.revoke_session(token)

    api = CoreApi(db, service)

    try:
        api.get_current_identity(
            request_id="req-sec-001",
            session_id=session.id,
            organisation_id=org.id,
        )
        assert False, "Expected AuthenticationError"
    except AuthenticationError:
        pass

    db.close()


def test_api_rejects_cross_tenant_context(tmp_path):
    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    other_org = service.create_organisation(
        "SEC-OTHER",
        "Other Security Organisation",
    )

    session, token = service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    api = CoreApi(db, service)

    try:
        api.get_current_identity(
            request_id="req-sec-002",
            session_id=session.id,
            organisation_id=other_org.id,
        )
        assert False, "Expected AuthenticationError"
    except AuthenticationError:
        pass

    db.close()


def test_api_rejects_missing_organisation_context(tmp_path):
    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    session, token = service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    api = CoreApi(db, service)

    try:
        api.get_current_identity(
            request_id="req-sec-003",
            session_id=session.id,
            organisation_id=None,
        )
        assert False, "Expected AuthenticationError"
    except AuthenticationError:
        pass

    db.close()


def test_api_permission_guard_denies_missing_permission(tmp_path):
    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    session, token = service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    api = CoreApi(db, service)
    context = api.resolve_context(
        request_id="req-sec-004",
        session_id=session.id,
        organisation_id=org.id,
    )

    try:
        api.require_permission(
            context,
            "security.nonexistent.permission",
        )
        assert False, "Expected AuthorizationError"
    except AuthorizationError:
        pass

    db.close()


def test_api_entitlement_guard_denies_missing_entitlement(tmp_path):
    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    session, token = service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    api = CoreApi(db, service)
    context = api.resolve_context(
        request_id="req-sec-005",
        session_id=session.id,
        organisation_id=org.id,
    )

    try:
        api.require_entitlement(
            context,
            "nonexistent-module",
        )
        assert False, "Expected AuthorizationError"
    except AuthorizationError:
        pass

    db.close()
