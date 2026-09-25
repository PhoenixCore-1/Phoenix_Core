import sqlite3
from datetime import datetime, timezone
from decimal import Decimal

from phoenix_core.migration_runner import apply_all

from phoenix_production_module.production.core_adapter import (
    calculate_core_performance,
    load_performance_observations,
)
from phoenix_production_module.production.service import ProductionService


def _db(tmp_path):
    db_path = tmp_path / "performance_core_test.db"
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    apply_all(db)
    return db


def _ensure_test_organisation(db, organisation_id):
    db.execute(
        """
        INSERT OR IGNORE INTO organisations(
            id,
            code,
            name,
            status,
            created_at
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


def _ensure_test_identity(db, identity_id="test-user"):
    db.execute(
        """
        INSERT OR IGNORE INTO identities(
            id,
            identity_type,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            str(identity_id),
            "HUMAN",
            "ACTIVE",
            "2026-09-01T08:00:00+00:00",
        ),
    )

def _insert_order(
    db,
    *,
    organisation_id,
    production_order_id,
    quantity_ordered,
    status="Planned",
):
    _ensure_test_organisation(db, organisation_id)
    _ensure_test_identity(db)

    db.execute(
        """
        INSERT INTO production_orders(
            production_order_id,
            organisation_id,
            order_number,
            purpose,
            product_ref,
            product_description,
            quantity_ordered,
            status,
            created_by,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            production_order_id,
            str(organisation_id),
            f"ORD-{production_order_id}",
            "Production",
            f"PROD-{production_order_id}",
            "Test Product",
            quantity_ordered,
            status,
            "test-user",
            "2026-09-01T08:00:00+00:00",
            "2026-09-01T08:00:00+00:00",
        ),
    )


def _insert_stage(
    db,
    *,
    production_order_id,
    stage_id,
    start_datetime=None,
    finish_datetime=None,
):
    db.execute(
        """
        INSERT INTO production_stages(
            stage_id,
            production_order_id,
            stage_code,
            stage_name,
            stage_sequence,
            status,
            start_datetime,
            finish_datetime
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            stage_id,
            production_order_id,
            f"S{stage_id}",
            "Test Stage",
            1,
            "Complete"
            if finish_datetime
            else "Ready",
            start_datetime,
            finish_datetime,
        ),
    )


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
            stage_id,
            quantity_type,
            quantity,
            uom_code,
            recorded_by,
            recorded_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(organisation_id),
            production_order_id,
            None,
            quantity_type,
            quantity,
            "EA",
            "test-user",
            "2026-09-01T12:00:00+00:00",
        ),
    )


def test_core_adapter_loads_only_requested_organisation(tmp_path):
    db = _db(tmp_path)

    _insert_order(
        db,
        organisation_id="ORG-A",
        production_order_id=101,
        quantity_ordered=100,
    )

    _insert_order(
        db,
        organisation_id="ORG-B",
        production_order_id=201,
        quantity_ordered=500,
    )

    db.commit()

    rows = load_performance_observations(
        db,
        organisation_id="ORG-A",
    )

    assert len(rows) == 1
    assert rows[0].order_id == "101"
    assert rows[0].organisation_id == "ORG-A"


def test_core_adapter_maps_quantity_and_stage_duration(tmp_path):
    db = _db(tmp_path)

    started = "2026-09-01T08:00:00+00:00"
    completed = "2026-09-01T12:00:00+00:00"

    _insert_order(
        db,
        organisation_id="ORG-A",
        production_order_id=101,
        quantity_ordered=100,
        status="Completed",
    )

    _insert_stage(
        db,
        production_order_id=101,
        stage_id=1001,
        start_datetime=started,
        finish_datetime=completed,
    )

    _insert_quantity(
        db,
        organisation_id="ORG-A",
        production_order_id=101,
        quantity=80,
        quantity_type="ACCEPTED",
    )

    _insert_quantity(
        db,
        organisation_id="ORG-A",
        production_order_id=101,
        quantity=20,
        quantity_type="REJECTED",
    )

    db.commit()

    result = calculate_core_performance(
        db,
        organisation_id="ORG-A",
    )

    assert result.order_count == 1
    assert result.completed_order_count == 1
    assert result.open_order_count == 0
    assert result.planned_quantity == Decimal("100")
    assert result.actual_quantity == Decimal("100")
    assert result.total_production_seconds == Decimal("14400")


def test_service_exposes_core_performance_analytics(tmp_path):
    db = _db(tmp_path)

    _insert_order(
        db,
        organisation_id="ORG-A",
        production_order_id=101,
        quantity_ordered=200,
    )

    _insert_quantity(
        db,
        organisation_id="ORG-A",
        production_order_id=101,
        quantity=100,
    )

    db.commit()

    service = ProductionService()

    result = service.calculate_performance(
        db,
        organisation_id="ORG-A",
    )

    assert result.order_count == 1
    assert result.open_order_count == 1
    assert result.completed_order_count == 0
    assert result.completion_ratio == Decimal("0.5")


def test_service_performance_honours_time_window(tmp_path):
    db = _db(tmp_path)

    start = datetime(
        2026,
        9,
        1,
        8,
        0,
        tzinfo=timezone.utc,
    )
    finish = datetime(
        2026,
        9,
        1,
        10,
        0,
        tzinfo=timezone.utc,
    )

    _insert_order(
        db,
        organisation_id="ORG-A",
        production_order_id=101,
        quantity_ordered=100,
        status="Completed",
    )

    _insert_stage(
        db,
        production_order_id=101,
        stage_id=1001,
        start_datetime=start.isoformat(),
        finish_datetime=finish.isoformat(),
    )

    _insert_quantity(
        db,
        organisation_id="ORG-A",
        production_order_id=101,
        quantity=100,
    )

    db.commit()

    service = ProductionService()

    result = service.calculate_performance(
        db,
        organisation_id="ORG-A",
        start_at=start,
        end_at=finish,
    )

    assert result.order_count == 1
    assert result.completed_order_count == 1





