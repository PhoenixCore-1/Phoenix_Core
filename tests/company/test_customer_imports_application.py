"""Customer Master import application-service tests."""

from pathlib import Path

import pytest

from phoenix_company.application.customer_imports import (
    CustomerImportApplicationService,
)
from phoenix_company.application.memberships import (
    CompanyMembershipApplicationService,
)
from phoenix_core.users.application import UserApplicationService
from phoenix_system.application.companies import (
    SystemCompanyApplicationService,
)
from phoenix_core.http_api.app import create_development_app


def _application_context(tmp_path):
    app = create_development_app(
        str(tmp_path / "core.db")
    )

    core = app.state.core_api

    system_company = SystemCompanyApplicationService(core)
    user_service = UserApplicationService(core)
    membership_service = CompanyMembershipApplicationService(
        core
    )

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

    login_response = core.authenticate(
        request_id="test-request",
        username="admin",
        password="password",
        organisation_id=organisation.id,
    )

    session_id = core.resolve_session_id(
        login_response.data["token"]
    )

    context = core.resolve_context(
        request_id="test-request",
        session_id=session_id,
        organisation_id=organisation.id,
    )

    service = CustomerImportApplicationService(core)

    return app, core, service, context, organisation


def _write_csv(
    tmp_path: Path,
    rows: list[tuple[str, str]],
) -> Path:
    path = tmp_path / "customers.csv"

    content = (
        "Customer ID,Customer name\n"
        + "\n".join(
            f"{customer_id},{display_name}"
            for customer_id, display_name in rows
        )
        + "\n"
    )

    path.write_bytes(
        content.encode("utf-8")
    )

    return path


def _create_validated_job(
    tmp_path,
    service,
    context,
    rows,
):
    file_path = _write_csv(
        tmp_path,
        rows,
    )

    create_response = service.create_import_job(
        context,
        source_filename=file_path.name,
        source_system="PHOENIX",
        file_hash="test-hash",
        total_rows=0,
    )

    job_id = create_response.data["id"]

    service.validate_import_job(
        context,
        job_id,
        file_path=file_path,
    )

    return job_id


def test_confirm_import_inserts_new_customers(tmp_path):
    (
        app,
        core,
        service,
        context,
        organisation,
    ) = _application_context(tmp_path)

    job_id = _create_validated_job(
        tmp_path,
        service,
        context,
        [
            ("CUST-001", "Customer One"),
            ("CUST-002", "Customer Two"),
        ],
    )

    response = service.confirm_import(
        context,
        job_id,
    )

    assert response.data["status"] == "COMPLETED"
    assert response.data["inserted_rows"] == 2
    assert response.data["updated_rows"] == 0
    assert response.data["unchanged_rows"] == 0

    rows = core.db.execute(
        """
        SELECT
            external_customer_id,
            display_name,
            status
        FROM customer_references
        WHERE organisation_id=?
        ORDER BY external_customer_id
        """,
        (str(organisation.id),),
    ).fetchall()

    assert len(rows) == 2
    assert rows[0]["external_customer_id"] == "CUST-001"
    assert rows[0]["display_name"] == "Customer One"
    assert rows[0]["status"] == "ACTIVE"
    assert rows[1]["external_customer_id"] == "CUST-002"


def test_confirm_import_marks_existing_identical_customers_unchanged(
    tmp_path,
):
    (
        app,
        core,
        service,
        context,
        organisation,
    ) = _application_context(tmp_path)

    core.db.execute(
        """
        INSERT INTO customer_references (
            id,
            organisation_id,
            source_system,
            external_customer_id,
            display_name,
            status,
            source_record_url,
            created_at,
            updated_at
        )
        VALUES (
            'existing-customer-1',
            ?,
            'PHOENIX',
            'CUST-001',
            'Customer One',
            'ACTIVE',
            NULL,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
        """,
        (str(organisation.id),),
    )
    core.db.commit()

    job_id = _create_validated_job(
        tmp_path,
        service,
        context,
        [
            ("CUST-001", "Customer One"),
        ],
    )

    response = service.confirm_import(
        context,
        job_id,
    )

    assert response.data["status"] == "COMPLETED"
    assert response.data["inserted_rows"] == 0
    assert response.data["updated_rows"] == 0
    assert response.data["unchanged_rows"] == 1


def test_confirm_import_updates_existing_changed_customers(
    tmp_path,
):
    (
        app,
        core,
        service,
        context,
        organisation,
    ) = _application_context(tmp_path)

    core.db.execute(
        """
        INSERT INTO customer_references (
            id,
            organisation_id,
            source_system,
            external_customer_id,
            display_name,
            status,
            source_record_url,
            created_at,
            updated_at
        )
        VALUES (
            'existing-customer-1',
            ?,
            'PHOENIX',
            'CUST-001',
            'Old Customer Name',
            'ACTIVE',
            NULL,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
        """,
        (str(organisation.id),),
    )
    core.db.commit()

    job_id = _create_validated_job(
        tmp_path,
        service,
        context,
        [
            ("CUST-001", "New Customer Name"),
        ],
    )

    response = service.confirm_import(
        context,
        job_id,
    )

    assert response.data["status"] == "COMPLETED"
    assert response.data["inserted_rows"] == 0
    assert response.data["updated_rows"] == 1
    assert response.data["unchanged_rows"] == 0

    row = core.db.execute(
        """
        SELECT display_name
        FROM customer_references
        WHERE organisation_id=?
          AND source_system='PHOENIX'
          AND external_customer_id='CUST-001'
        """,
        (str(organisation.id),),
    ).fetchone()

    assert row["display_name"] == "New Customer Name"


def test_confirm_import_rejects_invalid_job_without_changes(
    tmp_path,
):
    (
        app,
        core,
        service,
        context,
        organisation,
    ) = _application_context(tmp_path)

    file_path = _write_csv(
        tmp_path,
        [
            ("", "Missing Customer ID"),
            ("CUST-002", "Valid Customer"),
        ],
    )

    create_response = service.create_import_job(
        context,
        source_filename=file_path.name,
        source_system="PHOENIX",
        file_hash="invalid-test-hash",
        total_rows=0,
    )

    job_id = create_response.data["id"]

    service.validate_import_job(
        context,
        job_id,
        file_path=file_path,
    )

    with pytest.raises(Exception):
        service.confirm_import(
            context,
            job_id,
        )

    customer_count = core.db.execute(
        """
        SELECT COUNT(*) AS count
        FROM customer_references
        WHERE organisation_id=?
        """,
        (str(organisation.id),),
    ).fetchone()["count"]

    assert customer_count == 0

    job = core.db.execute(
        """
        SELECT
            status,
            inserted_rows,
            updated_rows,
            unchanged_rows
        FROM import_jobs
        WHERE id=?
        """,
        (job_id,),
    ).fetchone()

    assert job["status"] == "VALIDATED"
    assert job["inserted_rows"] == 0
    assert job["updated_rows"] == 0
    assert job["unchanged_rows"] == 0


def test_confirm_import_rolls_back_all_changes_on_failure(
    tmp_path,
):
    (
        app,
        core,
        service,
        context,
        organisation,
    ) = _application_context(tmp_path)

    job_id = _create_validated_job(
        tmp_path,
        service,
        context,
        [
            ("CUST-001", "Customer One"),
            ("CUST-002", "Customer Two"),
        ],
    )

    original_execute = core.db.execute
    call_count = {"count": 0}

    def failing_execute(sql, params=()):
        if (
            "INSERT INTO customer_references" in sql
            and call_count["count"] == 1
        ):
            raise RuntimeError(
                "Simulated customer reference failure."
            )

        if "INSERT INTO customer_references" in sql:
            call_count["count"] += 1

        return original_execute(sql, params)

    core.db.execute = failing_execute

    with pytest.raises(RuntimeError):
        service.confirm_import(
            context,
            job_id,
        )

    core.db.execute = original_execute

    customer_count = core.db.execute(
        """
        SELECT COUNT(*) AS count
        FROM customer_references
        WHERE organisation_id=?
        """,
        (str(organisation.id),),
    ).fetchone()["count"]

    assert customer_count == 0

    job = core.db.execute(
        """
        SELECT
            status,
            inserted_rows,
            updated_rows,
            unchanged_rows,
            confirmed_at,
            completed_at
        FROM import_jobs
        WHERE id=?
        """,
        (job_id,),
    ).fetchone()

    assert job["status"] == "VALIDATED"
    assert job["inserted_rows"] == 0
    assert job["updated_rows"] == 0
    assert job["unchanged_rows"] == 0
    assert job["confirmed_at"] is None
    assert job["completed_at"] is None