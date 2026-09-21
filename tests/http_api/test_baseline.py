from fastapi.testclient import TestClient

from phoenix_core.licensing.service import EntitlementService
from phoenix_core.http_api.app import create_development_app
from phoenix_core.users.application import UserApplicationService
from phoenix_company.application.memberships import CompanyMembershipApplicationService
from phoenix_system.application.companies import SystemCompanyApplicationService


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

    import uuid

    mid = uuid.uuid4()
    core_api.db.execute(
        """
        INSERT INTO modules(
            id, code, name, version, status, created_at
        )
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            str(mid),
            "sales_360",
            "Sales 360",
            "0.1.0",
            "ENABLED",
        ),
    )

    entitlement_service.grant(
        org.id,
        mid,
    )
    core_api.db.commit()

    return (
        TestClient(
            app,
            base_url="https://testserver",
        ),
        org,
    )


def test_baseline_company_user_flow(tmp_path):
    c, org = client(tmp_path)

    assert c.post(
        "/api/v1/auth/login",
        json={
            "username": "company.admin",
            "password": "Phoenix-V1-Company-2026!",
        },
    ).status_code == 200

    context_response = c.get(
        "/api/v1/baseline/context"
    )
    print("CONTEXT STATUS:", context_response.status_code)
    print("CONTEXT BODY:", context_response.json())

    ctx = context_response.json()["data"]

    assert ctx["company"]["code"] == "DEMO"
    assert ctx["user"]["platform_level"] == "COMPANY_ADMIN"
    assert ctx["modules"][0]["active"] is True

def test_baseline_system_can_create_company_and_activate_module(tmp_path):
    c, _ = client(tmp_path)

    assert c.post(
        "/api/v1/auth/login",
        json={
            "username": "system.admin",
            "password": "Phoenix-V1-System-2026!",
        },
    ).status_code == 200

    new = c.post(
        "/api/v1/system/companies",
        json={
            "code": "ACME",
            "name": "Acme",
        },
    )

    print("CREATE COMPANY STATUS:", new.status_code)
    print("CREATE COMPANY BODY:", new.json())
    assert new.status_code == 200

    cid = new.json()["data"]["id"]

    assert c.post(
        f"/api/v1/system/companies/{cid}/modules/sales_360/activate"
    ).status_code == 200

    assert c.post(
        f"/api/v1/system/companies/{cid}/admin",
        json={
            "username": "acme.admin",
            "display_name": "Acme Admin",
            "password": "Acme-V1-Admin-2026!",
        },
    ).status_code == 200









