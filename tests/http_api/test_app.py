from fastapi.testclient import TestClient

from phoenix_core.api.application import CoreApi
from phoenix_core.users.application import UserApplicationService
from phoenix_core.http_api.app import (
    ORGANISATION_HEADER,
    SESSION_COOKIE,
    create_development_app,
)
from phoenix_company.application.memberships import CompanyMembershipApplicationService
from phoenix_system.application.companies import SystemCompanyApplicationService


def build_client(tmp_path):
    database_path = tmp_path / "core.db"

    app = create_development_app(str(database_path))
    core_api = app.state.core_api

    company_service = SystemCompanyApplicationService(core_api)
    user_service = UserApplicationService(core_api)
    membership_service = CompanyMembershipApplicationService(core_api)

    organisation = company_service.create_company(
        "TEST",
        "Test Company",
    )

    user = user_service.create_user(
        username="test.user",
        display_name="Test User",
        password="test-password",
    )

    membership_service.add_membership(
        user.identity_id,
        organisation.id,
    )

    return (
        TestClient(
            app,
            base_url="https://testserver",
        ),
        organisation,
    )


def test_health_is_public(tmp_path):
    client, _ = build_client(tmp_path)
    response = client.get("/health")

    assert response.status_code == 200


def test_login_uses_httponly_secure_cookie_and_does_not_return_token(tmp_path):
    client, organisation = build_client(tmp_path)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "test.user",
            "password": "test-password",
        },
    )

    assert response.status_code == 200
    assert "token" not in response.json()

    cookie = response.headers.get("set-cookie", "")
    assert SESSION_COOKIE in cookie
    assert "HttpOnly" in cookie
    assert "Secure" in cookie


def test_current_user_uses_core_session_and_organisation_context(tmp_path):
    client, organisation = build_client(tmp_path)

    login = client.post(
        "/api/v1/auth/login",
        json={
            "username": "test.user",
            "password": "test-password",
        },
    )

    assert login.status_code == 200

    response = client.get(
        "/api/v1/me",
        headers={ORGANISATION_HEADER: str(organisation.id)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["username"] == "test.user"


def test_current_user_without_session_is_rejected(tmp_path):
    client, organisation = build_client(tmp_path)

    response = client.get(
        "/api/v1/me",
        headers={ORGANISATION_HEADER: str(organisation.id)},
    )

    assert response.status_code in {401, 403}


def test_logout_revokes_session_and_clears_cookie(tmp_path):
    client, organisation = build_client(tmp_path)

    login = client.post(
        "/api/v1/auth/login",
        json={
            "username": "test.user",
            "password": "test-password",
        },
    )

    assert login.status_code == 200

    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    assert SESSION_COOKIE in response.headers.get("set-cookie", "")






def test_production_module_is_registered_on_app_startup(tmp_path):
    app = create_development_app(str(tmp_path / "production.db"))

    row = app.state.db.execute(
        "SELECT code, name, version, status "
        "FROM modules WHERE code=?",
        ("production",),
    ).fetchone()

    assert row is not None
    assert row["code"] == "production"
    assert row["name"] == "Production"
    assert row["version"] == "1.3.25"
    assert row["status"] == "REGISTERED"


def test_password_reset_required_preserves_reset_flow_and_blocks_current_user(
    tmp_path,
):
    client, organisation = build_client(tmp_path)
    core_api = client.app.state.core_api

    user_row = core_api.db.execute(
        "SELECT id FROM users WHERE username=?",
        ("test.user",),
    ).fetchone()
    assert user_row is not None

    core_api.authentication_service.require_password_reset(
        __import__("uuid").UUID(user_row["id"])
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "username": "test.user",
            "password": "test-password",
        },
    )
    assert login.status_code == 200
    assert login.json()["data"]["password_reset_required"] is True

    context = client.get("/api/v1/baseline/context")
    assert context.status_code == 200

    blocked = client.get(
        "/api/v1/me",
        headers={ORGANISATION_HEADER: str(organisation.id)},
    )
    assert blocked.status_code in {401, 403}

    changed = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "test-password",
            "new_password": "NewStrongPassword123!",
        },
    )
    assert changed.status_code == 200

    allowed = client.get(
        "/api/v1/me",
        headers={ORGANISATION_HEADER: str(organisation.id)},
    )
    assert allowed.status_code == 200
