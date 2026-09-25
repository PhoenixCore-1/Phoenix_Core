from datetime import datetime, timezone
from decimal import Decimal
import sqlite3

from phoenix_core.migration_runner import apply_all
from phoenix_production_module.production.service import ProductionService


def _db(tmp_path):
    db_path = tmp_path / "production_service_performance.db"
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    apply_all(db)
    return db


def _ensure_organisation(db, organisation_id):
    db.execute(
        """
        INSERT OR IGNORE INTO organisations(
            id, code, name, status, created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            str(organisation_id),
            str(organisation_id),
            f"Test Organisation {organisation_id}",
            "ACTIVE",
            "2026-09-01T08:00:00+00:00",
        ),
    )


def _ensure_identity(db, identity_id="test-service-user"):
    db.execute(
        """
        INSERT OR IGNORE INTO identities(
            id, identity_type, status, created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            str(identity_id),
            "SERVICE",
            "ACTIVE",
            "2026-09-01T08:00:00+00:00",
        ),
    )


def _insert_order(
    db,
    *,
    organisation_id,
    order_number,
    quantity,
    created_by="test-service-user",
):
    _ensure_organisation(db, organisation_id)
    _ensure_identity(db, created_by)

    cursor = db.execute(
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
            created_by,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(organisation_id),
            order_number,
            "Service performance test",
            "TEST-PRODUCT",
            "Test product",
            quantity,
            "Normal",
            "In Production",
            created_by,
            "2026-09-01T08:00:00+00:00",
            "2026-09-01T08:00:00+00:00",
        ),
    )

    return cursor.lastrowid


def _insert_stage(
    db,
    *,
    production_order_id,
    stage_code,
    start_datetime,
    finish_datetime,
):
    cursor = db.execute(
        """
        INSERT INTO production_stages(
            production_order_id,
            stage_code,
            stage_name,
            stage_sequence,
            status,
            start_datetime,
            finish_datetime,
            quantity_completed,
            quantity_rejected
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            production_order_id,
            stage_code,
            stage_code,
            1,
            "Complete",
            start_datetime,
            finish_datetime,
            0,
            0,
        ),
    )

    return cursor.lastrowid


def _insert_quantity(
    db,
    *,
    organisation_id,
    production_order_id,
    quantity,
    quantity_type="ACCEPTED",
):
    db.execute(
        """
        INSERT INTO production_quantity_ledger(
            organisation_id,
            production_order_id,
            quantity_type,
            quantity,
            uom_code,
            recorded_by,
            recorded_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(organisation_id),
            production_order_id,
            quantity_type,
            quantity,
            "EA",
            "test-service-user",
            "2026-09-01T12:00:00+00:00",
        ),
    )


def test_service_delegates_to_core_performance(
    tmp_path,
):
    db = _db(tmp_path)

    order_id = _insert_order(
        db,
        organisation_id="org-1",
        order_number="PO-001",
        quantity=100,
    )

    _insert_stage(
        db,
        production_order_id=order_id,
        stage_code="CUT",
        start_datetime="2026-09-01T08:00:00+00:00",
        finish_datetime="2026-09-01T10:00:00+00:00",
    )

    _insert_quantity(
        db,
        organisation_id="org-1",
        production_order_id=order_id,
        quantity=75,
    )

    db.commit()

    result = ProductionService().calculate_performance(
        db,
        organisation_id="org-1",
    )

    assert result.organisation_id == "org-1"
    assert result.order_count == 1
    assert result.completed_order_count == 1
    assert result.open_order_count == 0
    assert result.planned_quantity == Decimal("100")
    assert result.actual_quantity == Decimal("75")
    assert result.completion_ratio == Decimal("0.75")
    assert result.total_production_seconds == Decimal("7200")
    assert result.average_production_seconds == Decimal("7200")
    assert result.average_actual_rate == Decimal("0.01041666666666666666666666667")


def test_service_passes_time_window_to_core(
    tmp_path,
):
    db = _db(tmp_path)

    first_order = _insert_order(
        db,
        organisation_id="org-1",
        order_number="PO-001",
        quantity=100,
    )
    second_order = _insert_order(
        db,
        organisation_id="org-1",
        order_number="PO-002",
        quantity=200,
    )

    _insert_stage(
        db,
        production_order_id=first_order,
        stage_code="CUT",
        start_datetime="2026-09-01T08:00:00+00:00",
        finish_datetime="2026-09-01T10:00:00+00:00",
    )
    _insert_stage(
        db,
        production_order_id=second_order,
        stage_code="CUT",
        start_datetime="2026-09-03T08:00:00+00:00",
        finish_datetime="2026-09-03T10:00:00+00:00",
    )

    _insert_quantity(
        db,
        organisation_id="org-1",
        production_order_id=first_order,
        quantity=80,
    )
    _insert_quantity(
        db,
        organisation_id="org-1",
        production_order_id=second_order,
        quantity=150,
    )

    db.commit()

    result = ProductionService().calculate_performance(
        db,
        organisation_id="org-1",
        start_at=datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ),
        end_at=datetime(
            2026,
            9,
            2,
            tzinfo=timezone.utc,
        ),
    )

    assert result.order_count == 1
    assert result.planned_quantity == Decimal("100")
    assert result.actual_quantity == Decimal("80")
    assert result.completed_order_count == 1



