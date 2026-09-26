from phoenix_core.api.application import CoreApi
from phoenix_core.api.integration.contracts import (
    IntegrationRequest,
    IntegrationResponse,
)
from phoenix_core.api.integration.service import CoreIntegrationService
from phoenix_core.errors import AuthenticationError, AuthorizationError


def make_service(tmp_path):
    from phoenix_core.infrastructure import SQLiteDatabase

    db = SQLiteDatabase(str(tmp_path / "integration.db"))
    from phoenix_core.api.application import CoreApi
    db.initialise_schema()
    service = CoreApi(db)
    return db, service


def setup_user(service, code="INT-TEST"):
    org = service.organisation_service.create_organisation(code=code, name="Integration Test Organisation")
    user = service.user_service.create_user(username="integrationuser", display_name="Integration User", password="CorrectPassword123!")
    service.company_membership_service.add_membership(user.identity_id, org.id)
    return user, org


def test_identity_current_integration_succeeds_for_authenticated_user(tmp_path):
    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    session, token, _ = service.authentication_service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    integration = CoreIntegrationService(service)

    response = integration.handle(
        IntegrationRequest(
            request_id="req-int-success-001",
            operation="identity.current",
            session_id=session.id,
            organisation_id=org.id,
        )
    )

    assert isinstance(response, IntegrationResponse)
    assert response.request_id == "req-int-success-001"
    assert response.success is True
    assert response.data["id"] == str(user.identity_id)
    assert response.data["type"] == "HUMAN"
    assert response.data["status"] == "ACTIVE"

    db.close()


def test_identity_current_integration_enforces_tenant_boundary(tmp_path):
    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    other_org = service.organisation_service.create_organisation(code="INT-OTHER", name="Other Organisation")

    session, token, _ = service.authentication_service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    integration = CoreIntegrationService(service)

    try:
        integration.handle(
            IntegrationRequest(
                request_id="req-int-tenant-001",
                operation="identity.current",
                session_id=session.id,
                organisation_id=other_org.id,
            )
        )
        assert False, "Expected AuthenticationError"
    except AuthorizationError:
        pass

    db.close()


def test_identity_current_integration_rejects_revoked_session(tmp_path):
    db, service = make_service(tmp_path)
    user, org = setup_user(service)

    session, token, _ = service.authentication_service.authenticate(
        user.username,
        "CorrectPassword123!",
    )

    service.authentication_service.revoke_session(token)

    integration = CoreIntegrationService(service)

    try:
        integration.handle(
            IntegrationRequest(
                request_id="req-int-session-001",
                operation="identity.current",
                session_id=session.id,
                organisation_id=org.id,
            )
        )
        assert False, "Expected AuthenticationError"
    except AuthenticationError:
        pass

    db.close()
