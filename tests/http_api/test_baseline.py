
from uuid import uuid4

from fastapi.testclient import TestClient

from phoenix_core.licensing.service import EntitlementService
from phoenix_core.http_api.app import create_development_app
from phoenix_core.http_api.authorization import (
    _require_password_reset_complete,
)
from phoenix_core.users.application import UserApplicationService
from phoenix_company.application.memberships import (
    CompanyMembershipApplicationService,
)
from phoenix_system.application.companies import (
    SystemCompanyApplicationService,
)


def client(tmp_path):
    database_path = tmp_path / "core.db"
    app = create_development_app(str(database_path))
    core_api = app.state.core_api

    system_company_service = SystemCompanyApplicationService(core_api)
    user_service = UserApplicationService(core_api)
    membership_service = CompanyMembershipApplicationService(core_api)
    entitlement_service = EntitlementService(core_api.db)

    system = user_service.create_user(
        username="system.admin",
        display_name="System Admin",
        password="Phoenix-V1-System-2026!",
    )
    core_api.db.execute(
        "UPDATE users SET platform_level='SYSTEM_ADMIN' WHERE id=?",
        (str(system.id),),
    )

    org = system_company_service.create_company(
        "DEMO",
        "Demo Company",
    )

    admin = user_service.create_user(
        username="company.admin",
        display_name="Company Admin",
        password="Phoenix-V1-Company-2026!",
    )
    core_api.db.execute(
        "UPDATE users SET platform_level='COMPANY_ADMIN' WHERE id=?",
        (str(admin.id),),
    )

    membership_service.add_membership(
        admin.identity_id,
        org.id,
    )

    module_id = uuid4()
    core_api.db.execute(
        """
        INSERT INTO modules(
            id, code, name, version, status, created_at
        )
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            str(module_id),
            "sales_360",
            "Sales 360",
            "0.1.0",
            "ENABLED",
        ),
    )

    entitlement_service.grant(org.id, module_id)
    core_api.db.commit()

    return TestClient(app, base_url="https://testserver"), org


def test_baseline_company_user_flow(tmp_path):
    c, _ = client(tmp_path)

    login_response = c.post(
        "/api/v1/auth/login",
        json={
            "username": "company.admin",
            "password": "Phoenix-V1-Company-2026!",
        },
    )
    assert login_response.status_code == 200

    context_response = c.get("/api/v1/baseline/context")

    assert context_response.status_code == 200

    ctx = context_response.json()["data"]
    assert ctx["company"]["code"] == "DEMO"
    assert ctx["user"]["platform_level"] == "COMPANY_ADMIN"
    assert ctx["modules"][0]["active"] is True


def test_baseline_system_can_create_company_and_activate_module(tmp_path):
    c, _ = client(tmp_path)

    login_response = c.post(
        "/api/v1/auth/login",
        json={
            "username": "system.admin",
            "password": "Phoenix-V1-System-2026!",
        },
    )
    assert login_response.status_code == 200

    new = c.post(
        "/api/v1/system/companies",
        json={
            "code": "ACME",
            "name": "Acme",
        },
    )

    assert new.status_code == 200

    company_id = new.json()["data"]["id"]

    activation_response = c.post(
        f"/api/v1/system/companies/{company_id}/modules/sales_360/activate"
    )

    assert activation_response.status_code == 200

    admin_response = c.post(
        f"/api/v1/system/companies/{company_id}/admin",
        json={
            "username": "acme.admin",
            "display_name": "Acme Admin",
            "password": "Acme-V1-Admin-2026!",
        },
    )

    assert admin_response.status_code == 200
