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





