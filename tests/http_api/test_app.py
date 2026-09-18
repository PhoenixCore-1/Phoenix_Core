from fastapi.testclient import TestClient

from phoenix_core.api.application import CoreApi
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.http_api.app import ORGANISATION_HEADER, SESSION_COOKIE, create_app
from phoenix_core.services import CoreFoundationService


def build_client(tmp_path):
    db = SQLiteDatabase(tmp_path / "core.db")
    core = CoreFoundationService(db)
    core.initialise()
    organisation = core.create_organisation("TEST", "Test Company")
    user = core.create_user("test.user", "Test User", "test-password")
    core.add_membership(user.identity_id, organisation.id)
    return TestClient(create_app(CoreApi(db, core)), base_url="https://testserver"), organisation


def test_health_is_public(tmp_path):
    client, _ = build_client(tmp_path)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"
    assert response.headers["X-Request-ID"]


def test_login_uses_httponly_secure_cookie_and_does_not_return_token(tmp_path):
    client, organisation = build_client(tmp_path)
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "test.user",
            "password": "test-password",
            "organisation_id": str(organisation.id),
        },
    )

    assert response.status_code == 200
    assert "token" not in response.json()["data"]
    assert "phoenix_session=" in response.headers["set-cookie"]
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "secure" in cookie


def test_current_user_uses_core_session_and_organisation_context(tmp_path):
    client, organisation = build_client(tmp_path)
    login = client.post(
        "/api/v1/auth/login",
        json={
            "username": "test.user",
            "password": "test-password",
            "organisation_id": str(organisation.id),
        },
    )
    assert login.status_code == 200

    response = client.get(
        "/api/v1/me",
        headers={ORGANISATION_HEADER: str(organisation.id)},
    )

    assert response.status_code == 200
    assert response.json()["data"]["username"] == "test.user"


def test_current_user_without_session_is_rejected(tmp_path):
    client, organisation = build_client(tmp_path)
    response = client.get(
        "/api/v1/me",
        headers={ORGANISATION_HEADER: str(organisation.id)},
    )

    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_ERROR"


def test_logout_revokes_session_and_clears_cookie(tmp_path):
    client, organisation = build_client(tmp_path)
    login = client.post(
        "/api/v1/auth/login",
        json={
            "username": "test.user",
            "password": "test-password",
            "organisation_id": str(organisation.id),
        },
    )
    assert login.status_code == 200

    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    assert response.json()["data"]["revoked"] is True
    assert f"{SESSION_COOKIE}=" in response.headers["set-cookie"]
