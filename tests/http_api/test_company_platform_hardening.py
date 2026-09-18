"""Regression coverage for the Company Platform hardening boundary."""

from uuid import UUID

from fastapi.testclient import TestClient

from phoenix_core.api.application import CoreApi
from phoenix_core.http_api.app import ORGANISATION_HEADER, create_app
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.migration_runner import apply_all
from phoenix_core.services import CoreFoundationService


def test_all_checked_in_migrations_install_company_platform_foundation(tmp_path):
    db = SQLiteDatabase(tmp_path / "core.db")
    apply_all(db)

    permission_rows = db.execute(
        "SELECT id, code FROM permissions WHERE code LIKE 'company.%' ORDER BY code"
    ).fetchall()
    assert len(permission_rows) == 8
    assert all(UUID(row["id"]) for row in permission_rows)
    assert {row["code"] for row in permission_rows} == {
        "company.activity.view",
        "company.configuration.manage",
        "company.memberships.manage",
        "company.reports.view",
        "company.roles.manage",
        "company.users.manage",
        "company.visibility.manage",
        "company.workspaces.manage",
    }

    for table in ("company_workspaces", "company_visibility_rules"):
        assert db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()

    db.close()


def test_company_platform_routes_are_registered():
    from phoenix_core.http_api.company import router as company_router
    from phoenix_core.http_api.reports import router as reports_router
    from phoenix_core.http_api.workspaces import router as workspaces_router

    company_paths = {route.path for route in company_router.routes}
    assert "/api/v1/company/activity" in company_paths
    assert "/api/v1/company/users" in company_paths
    assert "/api/v1/company/roles" in company_paths

    assert {route.path for route in reports_router.routes} == {"/api/v1/company/reports"}
    assert {route.path for route in workspaces_router.routes} == {
        "/api/v1/company/workspaces",
        "/api/v1/company/workspaces/{module_code}",
    }


def _client(tmp_path):
    db = SQLiteDatabase(tmp_path / "core.db")
    apply_all(db)
    core = CoreFoundationService(db)
    organisation = core.create_organisation("TEST", "Test Company")
    user = core.create_user("admin", "Company Admin", "password")
    membership = core.add_membership(user.identity_id, organisation.id)
    client = TestClient(create_app(CoreApi(db, core)), base_url="https://testserver")
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "password", "organisation_id": str(organisation.id)},
    )
    assert login.status_code == 200
    return client, organisation


def test_cross_origin_state_change_is_rejected(tmp_path):
    client, organisation = _client(tmp_path)
    response = client.post(
        "/api/v1/auth/logout",
        headers={
            "Origin": "https://attacker.example",
            ORGANISATION_HEADER: str(organisation.id),
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_same_origin_state_change_is_allowed_to_reach_authentication_layer(tmp_path):
    client, organisation = _client(tmp_path)
    response = client.post(
        "/api/v1/auth/logout",
        headers={
            "Origin": "https://testserver",
            ORGANISATION_HEADER: str(organisation.id),
        },
    )
    assert response.status_code == 200
