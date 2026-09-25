import sqlite3
import uuid

import pytest

from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.migration_runner import apply_all

from phoenix_production_module.production.integration import (
    get_eta_operational_snapshot,
)


@pytest.fixture
def db(tmp_path):
    test_db = (
        tmp_path
        / "eta_operational_snapshot_integration_test.db"
    )

    core_db = SQLiteDatabase(test_db)
    apply_all(core_db)

    connection = core_db.connection

    organisation_id = str(uuid.uuid4())
    identity_id = str(uuid.uuid4())

    connection.execute(
        """
        INSERT INTO organisations(
            id,
            code,
            name,
            status,
            created_at
        )
        VALUES(?,?,?,'ACTIVE',datetime('now'))
        """,
        (
            organisation_id,
            "TEST_ETA",
            "ETA Integration Test",
        ),
    )

    connection.execute(
        """
        INSERT INTO identities(
            id,
            identity_type,
            status,
            created_at
        )
        VALUES(?,'HUMAN','ACTIVE',datetime('now'))
        """,
        (
            identity_id,
        ),
    )

    order = connection.execute(
        """
        INSERT INTO production_orders(
            organisation_id,
            order_number,
            purpose,
            product_ref,
            product_description,
            quantity_ordered,
            priority,
            status,
            required_date,
            created_by,
            created_at,
            updated_at
        )
        VALUES(
            ?,?,?,?,?,?,?,?,?,?,
            datetime('now'),
            datetime('now')
        )
        """,
        (
            organisation_id,
            "ETA-TEST-001",
            "Customer Order",
            "ETA-TEST-PRODUCT",
            "ETA Integration Test Product",
            100,
            "Normal",
            "In Production",
            "2026-08-28T16:00:00+00:00",
            identity_id,
        ),
    )

    production_order_id = order.lastrowid

    stage = connection.execute(
        """
        INSERT INTO production_stages(
            production_order_id,
            stage_code,
            stage_name,
            stage_sequence,
            location,
            status
        )
        VALUES(
            ?,?,?,?,?, 'In Progress'
        )
        """,
        (
            production_order_id,
            "ETA-TEST",
            "ETA Test Stage",
            1,
            "ETA",
        ),
    )

    stage_id = stage.lastrowid

    connection.commit()

    yield {
        "db": connection,
        "organisation_id": organisation_id,
        "identity_id": identity_id,
        "production_order_id": production_order_id,
        "stage_id": stage_id,
    }

    connection.close()


def test_core_integration_returns_operational_eta_snapshot(
    db,
):
    result = get_eta_operational_snapshot(
        db["db"],
        organisation_id=db["organisation_id"],
        production_order_id=db["production_order_id"],
    )

    assert isinstance(result, dict)
    assert result["production_order_id"] == db["production_order_id"]


def test_core_integration_returns_core_safe_types(
    db,
):
    result = get_eta_operational_snapshot(
        db["db"],
        organisation_id=db["organisation_id"],
        production_order_id=db["production_order_id"],
    )

    assert isinstance(result, dict)

    for value in result.values():
        assert value is None or isinstance(
            value,
            (str, int, float, bool),
        )


def test_core_integration_is_read_only(
    db,
):
    before = db["db"].execute(
        """
        SELECT
            production_order_id,
            status,
            planned_eta_at,
            current_eta_at,
            required_date
        FROM production_orders
        WHERE production_order_id=?
        """,
        (db["production_order_id"],),
    ).fetchone()

    result = get_eta_operational_snapshot(
        db["db"],
        organisation_id=db["organisation_id"],
        production_order_id=db["production_order_id"],
    )

    after = db["db"].execute(
        """
        SELECT
            production_order_id,
            status,
            planned_eta_at,
            current_eta_at,
            required_date
        FROM production_orders
        WHERE production_order_id=?
        """,
        (db["production_order_id"],),
    ).fetchone()

    assert result is not None
    assert dict(before) == dict(after)


def test_core_integration_handles_missing_eta_values(
    db,
):
    db["db"].execute(
        """
        UPDATE production_orders
        SET planned_eta_at=NULL,
            current_eta_at=NULL
        WHERE production_order_id=?
        """,
        (db["production_order_id"],),
    )
    db["db"].commit()

    result = get_eta_operational_snapshot(
        db["db"],
        organisation_id=db["organisation_id"],
        production_order_id=db["production_order_id"],
    )

    assert isinstance(result, dict)
    assert result["planned_eta"] is None
    assert result["current_eta"] is None


def test_core_integration_can_be_called_repeatedly(
    db,
):
    first = get_eta_operational_snapshot(
        db["db"],
        organisation_id=db["organisation_id"],
        production_order_id=db["production_order_id"],
    )

    second = get_eta_operational_snapshot(
        db["db"],
        organisation_id=db["organisation_id"],
        production_order_id=db["production_order_id"],
    )

    assert first == second


def test_core_integration_does_not_create_quantity_ledger_entries(
    db,
):
    before = db["db"].execute(
        """
        SELECT COUNT(*)
        FROM production_quantity_ledger
        WHERE production_order_id=?
        """,
        (db["production_order_id"],),
    ).fetchone()[0]

    get_eta_operational_snapshot(
        db["db"],
        organisation_id=db["organisation_id"],
        production_order_id=db["production_order_id"],
    )

    after = db["db"].execute(
        """
        SELECT COUNT(*)
        FROM production_quantity_ledger
        WHERE production_order_id=?
        """,
        (db["production_order_id"],),
    ).fetchone()[0]

    assert before == after


def test_core_integration_does_not_change_production_order_status(
    db,
):
    before = db["db"].execute(
        """
        SELECT status
        FROM production_orders
        WHERE production_order_id=?
        """,
        (db["production_order_id"],),
    ).fetchone()["status"]

    get_eta_operational_snapshot(
        db["db"],
        organisation_id=db["organisation_id"],
        production_order_id=db["production_order_id"],
    )

    after = db["db"].execute(
        """
        SELECT status
        FROM production_orders
        WHERE production_order_id=?
        """,
        (db["production_order_id"],),
    ).fetchone()["status"]

    assert before == after


def test_core_integration_does_not_create_events(
    db,
):
    before = db["db"].execute(
        """
        SELECT COUNT(*)
        FROM production_events
        WHERE production_order_id=?
        """,
        (db["production_order_id"],),
    ).fetchone()[0]

    get_eta_operational_snapshot(
        db["db"],
        organisation_id=db["organisation_id"],
        production_order_id=db["production_order_id"],
    )

    after = db["db"].execute(
        """
        SELECT COUNT(*)
        FROM production_events
        WHERE production_order_id=?
        """,
        (db["production_order_id"],),
    ).fetchone()[0]

    assert before == after
