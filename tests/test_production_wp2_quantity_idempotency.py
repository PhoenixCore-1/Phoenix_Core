from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from phoenix_core.api.application import CoreApi
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.integration import (
    record_stage_quantities,
    release_order,
    start_order,
)


def test_quantity_recording_is_idempotent(tmp_path: Path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()
    api = CoreApi(db)

    organisation = api.organisation_service.create_organisation(
        "ORG-TEST",
        "Test Organisation",
    )

    identity_id = uuid4()
    db.execute(
        "INSERT INTO identities "
        "(id, identity_type, status, created_at) "
        "VALUES (?, ?, ?, ?)",
        (
            str(identity_id),
            "HUMAN",
            "ACTIVE",
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    db.commit()

    db.execute(
        """
        INSERT INTO production_orders (
            production_order_id,
            organisation_id,
            order_number,
            purpose,
            product_ref,
            quantity_ordered,
            required_date,
            created_by,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Planned', datetime('now'), datetime('now'))
        """,
        (
            1001,
            str(organisation.id),
            "MO-1001",
            "Standard production",
            "PROD-001",
            10,
            "2026-12-31",
            str(identity_id),
        ),
    )

    db.execute(
        """
        INSERT INTO production_stages (
            production_order_id,
            stage_id,
            stage_code,
            stage_name,
            stage_sequence,
            status,
            location,
            start_datetime,
            finish_datetime,
            quantity_completed,
            quantity_rejected,
            notes
        )
        VALUES (?, ?, ?, ?, ?, 'Ready', ?, NULL, NULL, 0, 0, NULL)
        """,
        (
            1001,
            1,
            "CUT",
            "Cutting",
            1,
            "Factory Floor",
        ),
    )
    db.commit()

    release_order(
        db,
        organisation_id=str(organisation.id),
        production_order_id=1001,
        recorded_by=str(identity_id),
    )
    start_order(
        db,
        organisation_id=str(organisation.id),
        production_order_id=1001,
        recorded_by=str(identity_id),
    )

    first = record_stage_quantities(
        db=db,
        organisation_id=str(organisation.id),
        production_order_id=1001,
        stage_id=1,
        accepted_quantity=Decimal("5"),
        rejected_quantity=Decimal("0"),
        recorded_by=str(identity_id),
        accepted_idempotency_key="qty-duplicate-001",
    )
    db.commit()

    second = record_stage_quantities(
        db=db,
        organisation_id=str(organisation.id),
        production_order_id=1001,
        stage_id=1,
        accepted_quantity=Decimal("5"),
        rejected_quantity=Decimal("0"),
        recorded_by=str(identity_id),
        accepted_idempotency_key="qty-duplicate-001",
    )
    db.commit()

    assert first
    assert second == {"accepted_ledger_id": first["accepted_ledger_id"]}

    row = db.execute(
        """
        SELECT COUNT(*) AS count, COALESCE(SUM(quantity), 0) AS total
        FROM production_quantity_ledger
        WHERE organisation_id=?
          AND production_order_id=?
          AND idempotency_key=?
        """,
        (
            str(organisation.id),
            1001,
            "qty-duplicate-001",
        ),
    ).fetchone()

    assert row["count"] == 1
    assert Decimal(str(row["total"])) == Decimal("5")

    db.close()






