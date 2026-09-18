"""Tests for tenant-scoped Company Platform settings."""

from fastapi.testclient import TestClient

from phoenix_core.api.application import CoreApi
from phoenix_core.http_api.app import ORGANISATION_HEADER, create_app
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.services import CoreFoundationService


def build_client(tmp_path):
    db = SQLiteDatabase(tmp_path / "core.db")
    core = CoreFoundationService(db)
    core.initialise()
    organisation = core.create_organisation("TEST", "Test Company")
    user = core.create_user("admin", "Company Admin", "password")
    membership = core.add_membership(user.identity_id, organisation.id)
    role = core.create_role(organisation.id, "company_admin", "Company Administrator")
    permission = core.create_permission("company.configuration.manage", "Manage company configuration")
    core.grant_permission(role.id, permission.id)
    core.assign_role(membership.id, role.id)
    return TestClient(create_app(CoreApi(db, core)), base_url="https://testserver"), organisation, core


def login(client, organisation):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "password", "organisation_id": str(organisation.id)},
    )
    assert response.status_code == 200
    return {ORGANISATION_HEADER: str(organisation.id)}


def test_company_settings_are_tenant_scoped_and_audited(tmp_path):
    client, organisation, core = build_client(tmp_path)
    headers = login(client, organisation)

    response = client.patch(
        "/api/v1/company/settings/company.timezone",
        headers=headers,
        json={"value": "Africa/Johannesburg", "value_type": "STRING", "description": "Company timezone"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["value"] == "Africa/Johannesburg"

    response = client.get("/api/v1/company/settings", headers=headers)
    assert response.status_code == 200
    assert any(item["key"] == "company.timezone" for item in response.json()["data"]["items"])

    actions = {event.action for event in core.audit_service.list(organisation_id=organisation.id)}
    assert "COMPANY_SETTING_UPDATED" in actions


def test_company_settings_require_configuration_permission(tmp_path):
    db = SQLiteDatabase(tmp_path / "core.db")
    core = CoreFoundationService(db)
    core.initialise()
    organisation = core.create_organisation("TEST", "Test Company")
    user = core.create_user("user", "Company User", "password")
    membership = core.add_membership(user.identity_id, organisation.id)
    role = core.create_role(organisation.id, "user", "Company User")
    core.assign_role(membership.id, role.id)
    client = TestClient(create_app(CoreApi(db, core)), base_url="https://testserver")

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "user", "password": "password", "organisation_id": str(organisation.id)},
    )
    assert response.status_code == 200
    headers = {ORGANISATION_HEADER: str(organisation.id)}

    response = client.get("/api/v1/company/settings", headers=headers)
    assert response.status_code == 403
    assert response.json()["code"] == "AUTHORIZATION_ERROR"


def test_company_settings_cannot_be_read_using_foreign_organisation_context(tmp_path):
    client, organisation, core = build_client(tmp_path)
    headers = login(client, organisation)
    other = core.create_organisation("OTHER", "Other Company")

    response = client.get(
        "/api/v1/company/settings",
        headers={ORGANISATION_HEADER: str(other.id)},
    )
    assert response.status_code == 403
