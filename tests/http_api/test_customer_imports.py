"""Customer Master import HTTP API tests."""

from io import BytesIO

from fastapi.testclient import TestClient

from phoenix_core.http_api.app import (
    ORGANISATION_HEADER,
    create_development_app,
)
from phoenix_core.users.application import UserApplicationService
from phoenix_system.application.companies import (
    SystemCompanyApplicationService,
)
from phoenix_company.application.memberships import (
    CompanyMembershipApplicationService,
)


def _client(tmp_path):
    app = create_development_app(str(tmp_path / "core.db"))
    core = app.state.core_api

    system_company = SystemCompanyApplicationService(core)
    user_service = UserApplicationService(core)
    membership_service = CompanyMembershipApplicationService(core)

    organisation = system_company.create_company(
        "TEST",
        "Test Company",
    )

    user = user_service.create_user(
        username="admin",
        display_name="Company Admin",
        password="password",
    )

    membership = membership_service.add_membership(
        user.identity_id,
        organisation.id,
    )

    role_service = core.role_service

    role = role_service.create_role(
        organisation.id,
        "company_admin",
        "Company Administrator",
    )

    for code in (
        "company.users.manage",
        "company.memberships.manage",
        "company.roles.manage",
        "company.data.import",
    ):
        permission_row = core.db.execute(
            "SELECT id FROM permissions WHERE code=?",
            (code,),
        ).fetchone()

        assert permission_row is not None

        role_service.db.execute(
            """
            INSERT INTO role_permissions(
                role_id,
                permission_id,
                created_at
            )
            VALUES (?, ?, datetime('now'))
            """,
            (
                str(role.id),
                permission_row["id"],
            ),
        )

        role_service.db.commit()

    role_service.assign_role(
        membership.id,
        role.id,
    )

    client = TestClient(
        app,
        base_url="https://testserver",
        raise_server_exceptions=True,
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": "password",
            "organisation_id": str(organisation.id),
        },
    )

    assert login.status_code == 200

    return client, organisation


def test_customer_master_upload_route_is_registered():
    from phoenix_core.http_api.company import router as company_router

    company_paths = {
        route.path
        for route in company_router.routes
    }

    assert (
        "/api/v1/company/imports/customer-master"
        in company_paths
    )

    assert (
        "/api/v1/company/imports/{job_id}/preview"
        in company_paths
    )


def test_customer_master_upload_valid_csv(tmp_path):
    client, organisation = _client(tmp_path)

    csv_content = (
        "Customer ID,Customer name\n"
        "CUST-001,Customer One\n"
        "CUST-002,Customer Two\n"
    )

    response = client.post(
        "/api/v1/company/imports/customer-master",
        headers={
            ORGANISATION_HEADER: str(organisation.id),
        },
        files={
            "file": (
                "customers.csv",
                BytesIO(csv_content.encode("utf-8")),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["status"] == "VALIDATED"
    assert data["total_rows"] == 2
    assert data["valid_rows"] == 2
    assert data["invalid_rows"] == 0


def test_customer_master_upload_rejects_missing_customer_id(
    tmp_path,
):
    client, organisation = _client(tmp_path)

    csv_content = (
        "Customer ID,Customer name\n"
        ",Missing ID Customer\n"
        "CUST-002,Valid Customer\n"
    )

    response = client.post(
        "/api/v1/company/imports/customer-master",
        headers={
            ORGANISATION_HEADER: str(organisation.id),
        },
        files={
            "file": (
                "customers.csv",
                BytesIO(csv_content.encode("utf-8")),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["status"] == "VALIDATED"
    assert data["total_rows"] == 2
    assert data["valid_rows"] == 1
    assert data["invalid_rows"] == 1


def test_customer_master_upload_rejects_duplicate_customer_id(
    tmp_path,
):
    client, organisation = _client(tmp_path)

    csv_content = (
        "Customer ID,Customer name\n"
        "CUST-001,Customer One\n"
        "CUST-001,Customer Duplicate\n"
    )

    response = client.post(
        "/api/v1/company/imports/customer-master",
        headers={
            ORGANISATION_HEADER: str(organisation.id),
        },
        files={
            "file": (
                "customers.csv",
                BytesIO(csv_content.encode("utf-8")),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["status"] == "VALIDATED"
    assert data["total_rows"] == 2
    assert data["valid_rows"] == 0
    assert data["invalid_rows"] == 2


def test_customer_master_upload_rejects_missing_customer_name(
    tmp_path,
):
    client, organisation = _client(tmp_path)

    csv_content = (
        "Customer ID,Customer name\n"
        "CUST-001,\n"
        "CUST-002,Valid Customer\n"
    )

    response = client.post(
        "/api/v1/company/imports/customer-master",
        headers={
            ORGANISATION_HEADER: str(organisation.id),
        },
        files={
            "file": (
                "customers.csv",
                BytesIO(csv_content.encode("utf-8")),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["status"] == "VALIDATED"
    assert data["total_rows"] == 2
    assert data["valid_rows"] == 1
    assert data["invalid_rows"] == 1


def test_customer_master_import_preview_returns_rows(tmp_path):
    client, organisation = _client(tmp_path)

    csv_content = (
        "Customer ID,Customer name\n"
        "CUST-001,Customer One\n"
        "CUST-002,Customer Two\n"
    )

    upload_response = client.post(
        "/api/v1/company/imports/customer-master",
        headers={
            ORGANISATION_HEADER: str(organisation.id),
        },
        files={
            "file": (
                "customers.csv",
                BytesIO(csv_content.encode("utf-8")),
                "text/csv",
            )
        },
    )

    assert upload_response.status_code == 200

    job_id = upload_response.json()["data"]["id"]

    preview_response = client.get(
        f"/api/v1/company/imports/{job_id}/preview",
        headers={
            ORGANISATION_HEADER: str(organisation.id),
        },
    )

    assert preview_response.status_code == 200, (
        preview_response.text
    )

    data = preview_response.json()["data"]

    assert data["id"] == job_id
    assert data["status"] == "VALIDATED"
    assert len(data["rows"]) == 2

    assert data["rows"][0]["row_number"] == 2
    assert data["rows"][0]["external_id"] == "CUST-001"
    assert data["rows"][0]["display_name"] == "Customer One"
    assert data["rows"][0]["validation_status"] == "VALID"
    assert data["rows"][0]["validation_errors"] == []
    assert data["rows"][0]["action"] is None


def test_customer_master_upload_persists_validation_counters(
    tmp_path,
):
    client, organisation = _client(tmp_path)

    csv_content = (
        "Customer ID,Customer name\n"
        "CUST-001,Customer One\n"
        "CUST-002,Customer Two\n"
    )

    response = client.post(
        "/api/v1/company/imports/customer-master",
        headers={
            ORGANISATION_HEADER: str(organisation.id),
        },
        files={
            "file": (
                "customers.csv",
                BytesIO(csv_content.encode("utf-8")),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    job_id = response.json()["data"]["id"]

    db = client.app.state.db

    row = db.execute(
        """
        SELECT
            status,
            total_rows,
            valid_rows,
            invalid_rows,
            warning_rows
        FROM import_jobs
        WHERE id=?
        """,
        (job_id,),
    ).fetchone()

    assert row is not None
    assert row["status"] == "VALIDATED"
    assert row["total_rows"] == 2
    assert row["valid_rows"] == 2
    assert row["invalid_rows"] == 0
    assert row["warning_rows"] == 0