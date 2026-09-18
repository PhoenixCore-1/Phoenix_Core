from phoenix_core.api.application import CoreApi
from phoenix_core.api.contracts import ApiResponse


def make_service(tmp_path):
    from phoenix_core.infrastructure import SQLiteDatabase
    from phoenix_core.services import CoreFoundationService

    db = SQLiteDatabase(str(tmp_path / "api.db"))
    service = CoreFoundationService(db)
    service.initialise()
    return db, service


def setup_user(service):
    org = service.create_organisation("API-TEST", "API Test Organisation")
    user = service.create_user(
        "apiuser",
        "API User",
        "CorrectPassword123!",
    )
    service.add_membership(user.identity_id, org.id)
    return user, org


def test_current_identity_endpoint_returns_api_response(tmp_path):
    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    session, token = service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    api = CoreApi(db, service)

    response = api.get_current_identity(
        request_id="req-api-001",
        session_id=session.id,
        organisation_id=org.id,
    )

    assert isinstance(response, ApiResponse)
    assert response.request_id == "req-api-001"
    assert response.data["id"] == str(user.identity_id)
    assert response.data["type"] == "HUMAN"
    assert response.data["status"] == "ACTIVE"

    db.close()


def test_current_identity_endpoint_enforces_tenant_boundary(tmp_path):
    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    other_org = service.create_organisation(
        "API-OTHER",
        "Other Organisation",
    )

    session, token = service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    api = CoreApi(db, service)

    from phoenix_core.errors import AuthenticationError

    try:
        api.get_current_identity(
            request_id="req-api-002",
            session_id=session.id,
            organisation_id=other_org.id,
        )
        assert False, "Expected AuthenticationError"
    except AuthenticationError:
        pass

    db.close()

def test_api_permission_guard_allows_granted_permission(tmp_path):
    from phoenix_core.security.context import RequestContext

    db, service = make_service(tmp_path)
    api = CoreApi(db, service)

    context = RequestContext(
        request_id="req-api-003",
        permissions=frozenset({"crm.customer.read"}),
    )

    api.require_permission(context, "crm.customer.read")

    db.close()


def test_api_permission_guard_rejects_missing_permission(tmp_path):
    from phoenix_core.security.context import RequestContext
    from phoenix_core.errors import AuthorizationError

    db, service = make_service(tmp_path)
    api = CoreApi(db, service)

    context = RequestContext(
        request_id="req-api-004",
        permissions=frozenset(),
    )

    try:
        api.require_permission(context, "crm.customer.read")
        assert False, "Expected AuthorizationError"
    except AuthorizationError:
        pass

    db.close()


def test_api_entitlement_guard_allows_enabled_module(tmp_path):
    from phoenix_core.security.context import RequestContext

    db, service = make_service(tmp_path)
    api = CoreApi(db, service)

    context = RequestContext(
        request_id="req-api-005",
        entitlements=frozenset({"crm"}),
    )

    api.require_entitlement(context, "crm")

    db.close()


def test_api_entitlement_guard_rejects_missing_module(tmp_path):
    from phoenix_core.security.context import RequestContext
    from phoenix_core.errors import AuthorizationError

    db, service = make_service(tmp_path)
    api = CoreApi(db, service)

    context = RequestContext(
        request_id="req-api-006",
        entitlements=frozenset(),
    )

    try:
        api.require_entitlement(context, "crm")
        assert False, "Expected AuthorizationError"
    except AuthorizationError:
        pass

    db.close()

def test_api_authenticate_returns_session_token(tmp_path):
    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    api = CoreApi(db, service)

    response = api.authenticate(
        request_id="req-api-auth-001",
        username=user.username,
        password="CorrectPassword123!",
        organisation_id=org.id,
    )

    assert isinstance(response, ApiResponse)
    assert response.request_id == "req-api-auth-001"
    assert response.data["identity_id"] == str(user.identity_id)
    assert response.data["status"] == "ACTIVE"
    assert response.data["token"]
    assert response.data["session_id"]
    assert response.data["expires_at"]

    db.close()


def test_api_authenticate_rejects_invalid_credentials(tmp_path):
    from phoenix_core.errors import AuthenticationError

    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    api = CoreApi(db, service)

    try:
        api.authenticate(
            request_id="req-api-auth-002",
            username=user.username,
            password="WrongPassword123!",
            organisation_id=org.id,
        )
        assert False, "Expected AuthenticationError"
    except AuthenticationError:
        pass

    db.close()


def test_api_revoke_session_revokes_active_session(tmp_path):
    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    api = CoreApi(db, service)

    auth_response = api.authenticate(
        request_id="req-api-auth-003",
        username=user.username,
        password="CorrectPassword123!",
        organisation_id=org.id,
    )

    token = auth_response.data["token"]

    response = api.revoke_session(
        request_id="req-api-auth-004",
        token=token,
    )

    assert isinstance(response, ApiResponse)
    assert response.request_id == "req-api-auth-004"
    assert response.data["revoked"] is True

    db.close()


def test_api_revoke_unknown_session_returns_false(tmp_path):
    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    api = CoreApi(db, service)

    response = api.revoke_session(
        request_id="req-api-auth-005",
        token="not-a-valid-session-token",
    )

    assert isinstance(response, ApiResponse)
    assert response.data["revoked"] is False

    db.close()

def test_api_current_organisation_returns_current_tenant(tmp_path):
    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    api = CoreApi(db, service)

    session, token = api.authentication_service.authenticate(
        user.username,
        "CorrectPassword123!",
        org.id,
    )

    response = api.get_current_organisation(
        request_id="req-api-org-001",
        session_id=session.id,
        organisation_id=org.id,
    )

    assert isinstance(response, ApiResponse)
    assert response.request_id == "req-api-org-001"
    assert response.data["id"] == str(org.id)
    assert response.data["code"] == org.code
    assert response.data["name"] == org.name
    assert response.data["status"] == "ACTIVE"
    assert response.data["created_at"] == org.created_at.isoformat()

    db.close()


def test_api_current_organisation_rejects_other_tenant(tmp_path):
    from phoenix_core.errors import AuthenticationError

    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    other_org = service.create_organisation(
        "API-OTHER",
        "Other Organisation",
    )

    api = CoreApi(db, service)

    session, token = api.authentication_service.authenticate(
        user.username,
        "CorrectPassword123!",
        org.id,
    )

    try:
        api.get_current_organisation(
            request_id="req-api-org-002",
            session_id=session.id,
            organisation_id=other_org.id,
        )
        assert False, "Expected AuthenticationError"
    except AuthenticationError:
        pass

    db.close()


def test_api_current_user_returns_authenticated_user_without_password_hash(tmp_path):
    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    api = CoreApi(db, service)

    session, token = api.authentication_service.authenticate(
        user.username,
        "CorrectPassword123!",
        org.id,
    )

    response = api.get_current_user(
        request_id="req-api-user-001",
        session_id=session.id,
        organisation_id=org.id,
    )

    assert isinstance(response, ApiResponse)
    assert response.request_id == "req-api-user-001"
    assert response.data["id"] == str(user.id)
    assert response.data["identity_id"] == str(user.identity_id)
    assert response.data["username"] == user.username
    assert response.data["display_name"] == user.display_name
    assert response.data["status"] == "ACTIVE"
    assert response.data["created_at"] == user.created_at.isoformat()
    assert "password_hash" not in response.data

    db.close()


def test_api_current_user_rejects_other_tenant(tmp_path):
    from phoenix_core.errors import AuthenticationError

    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    other_org = service.create_organisation(
        "API-OTHER",
        "Other Organisation",
    )

    api = CoreApi(db, service)

    session, token = api.authentication_service.authenticate(
        user.username,
        "CorrectPassword123!",
        org.id,
    )

    try:
        api.get_current_user(
            request_id="req-api-user-002",
            session_id=session.id,
            organisation_id=other_org.id,
        )
        assert False, "Expected AuthenticationError"
    except AuthenticationError:
        pass

    db.close()
