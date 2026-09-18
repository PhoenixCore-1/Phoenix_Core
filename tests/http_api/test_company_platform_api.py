"""Tests for the Company Platform People & Access HTTP surface."""

from fastapi.testclient import TestClient
from uuid import uuid4

from phoenix_core.api.application import CoreApi
from phoenix_core.http_api.app import ORGANISATION_HEADER, create_app
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.services import CoreFoundationService


MANAGEMENT_PERMISSIONS = (
    "company.users.manage",
    "company.memberships.manage",
    "company.roles.manage",
)


def build_client(tmp_path, *, admin=True):
    db = SQLiteDatabase(tmp_path / "core.db")
    core = CoreFoundationService(db)
    core.initialise()
    organisation = core.create_organisation("TEST", "Test Company")
    user = core.create_user("test.user", "Test User", "test-password")
    membership = core.add_membership(user.identity_id, organisation.id)

    if admin:
        role = core.create_role(organisation.id, "company_admin", "Company Administrator")
        for code in MANAGEMENT_PERMISSIONS:
            permission = core.create_permission(code, code.replace(".", " ").title())
            core.grant_permission(role.id, permission.id)
        core.assign_role(membership.id, role.id)

    return TestClient(create_app(CoreApi(db, core)), base_url="https://testserver"), organisation, core


def login(client, organisation):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "test.user",
            "password": "test-password",
            "organisation_id": str(organisation.id),
        },
    )
    assert response.status_code == 200
    return {ORGANISATION_HEADER: str(organisation.id)}


def test_company_platform_router_defines_people_access_routes():
    from phoenix_core.http_api.company import router

    paths = {route.path for route in router.routes}

    expected = {
        "/api/v1/company",
        "/api/v1/company/users",
        "/api/v1/company/users/{user_id}",
        "/api/v1/company/memberships",
        "/api/v1/company/memberships/{membership_id}/suspend",
        "/api/v1/company/memberships/{membership_id}/restore",
        "/api/v1/company/memberships/{membership_id}/remove",
        "/api/v1/company/memberships/{membership_id}/roles/{role_id}",
        "/api/v1/company/roles",
        "/api/v1/company/roles/{role_id}",
        "/api/v1/company/roles/{role_id}/disable",
        "/api/v1/company/roles/{role_id}/enable",
        "/api/v1/company/roles/{role_id}/permissions",
        "/api/v1/company/roles/{role_id}/permissions/{permission_id}",
        "/api/v1/company/permissions",
    }
    assert expected.issubset(paths)


def test_company_platform_route_paths_are_tenant_scoped():
    from phoenix_core.http_api.company import router

    for route in router.routes:
        assert "{organisation_id}" not in route.path
        assert str(uuid4()) not in route.path


def test_company_admin_can_create_user_and_core_records_audit(tmp_path):
    client, organisation, core = build_client(tmp_path, admin=True)
    headers = login(client, organisation)

    response = client.post(
        "/api/v1/company/users",
        headers=headers,
        json={
            "username": "new.user",
            "display_name": "New User",
            "password": "new-password",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user"]["username"] == "new.user"
    assert data["membership"]["status"] == "ACTIVE"

    memberships = core.list_memberships(organisation.id)
    assert len(memberships) == 2
    audits = core.audit_service.list(organisation_id=organisation.id)
    actions = {event.action for event in audits}
    assert "COMPANY_USER_CREATED" in actions
    assert "COMPANY_MEMBERSHIP_CREATED" in actions


def test_company_user_management_requires_server_side_permission(tmp_path):
    client, organisation, _ = build_client(tmp_path, admin=False)
    headers = login(client, organisation)

    response = client.post(
        "/api/v1/company/users",
        headers=headers,
        json={
            "username": "blocked.user",
            "display_name": "Blocked User",
            "password": "blocked-password",
        },
    )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTHORIZATION_ERROR"


def test_membership_mutations_are_tenant_scoped_and_audited(tmp_path):
    client, organisation, core = build_client(tmp_path, admin=True)
    headers = login(client, organisation)

    user = core.create_user("member.user", "Member User", "member-password")
    membership = core.add_membership(user.identity_id, organisation.id)

    response = client.post(
        f"/api/v1/company/memberships/{membership.id}/suspend",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "SUSPENDED"

    response = client.post(
        f"/api/v1/company/memberships/{membership.id}/restore",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ACTIVE"

    actions = {event.action for event in core.audit_service.list(organisation_id=organisation.id)}
    assert "COMPANY_MEMBERSHIP_SUSPENDED" in actions
    assert "COMPANY_MEMBERSHIP_ACTIVE" in actions


def test_role_management_and_permission_assignment_are_audited(tmp_path):
    client, organisation, core = build_client(tmp_path, admin=True)
    headers = login(client, organisation)

    response = client.post(
        "/api/v1/company/roles",
        headers=headers,
        json={"code": "sales_manager", "name": "Sales Manager"},
    )
    assert response.status_code == 200
    role_id = response.json()["data"]["id"]

    permission = core.create_permission("sales.quote.view", "View Sales Quotes")
    response = client.post(
        f"/api/v1/company/roles/{role_id}/permissions/{permission.id}",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["granted"] is True

    response = client.post(
        f"/api/v1/company/roles/{role_id}/disable",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "DISABLED"

    actions = {event.action for event in core.audit_service.list(organisation_id=organisation.id)}
    assert "COMPANY_ROLE_CREATED" in actions
    assert "COMPANY_ROLE_PERMISSION_GRANTED" in actions
    assert "COMPANY_ROLE_DISABLED" in actions


def test_company_cannot_mutate_role_from_another_organisation(tmp_path):
    client, organisation, core = build_client(tmp_path, admin=True)
    headers = login(client, organisation)

    other = core.create_organisation("OTHER", "Other Company")
    foreign_role = core.create_role(other.id, "foreign", "Foreign Role")

    response = client.post(
        f"/api/v1/company/roles/{foreign_role.id}/disable",
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "AUTHORIZATION_ERROR"
