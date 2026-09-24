from decimal import Decimal
from pathlib import Path

from phoenix_core.api.application import CoreApi
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.integration import (
    record_stage_quantities,
)


def test_record_stage_quantities_is_idempotent(tmp_path: Path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()
    api = CoreApi(db)

    organisation = api.organisation_service.create_organisation(
        code="PROD-WP2-QTY",
        name="Production WP2 Quantity",
    )
    user = api.user_service.create_user(
        username="prod-wp2-qty-user",
        display_name="Production WP2 Quantity User",
        password="CorrectPassword123!",
    )
    api.company_membership_service.add_membership(
        user.identity_id,
        organisation.id,
    )

    order_id = db.execute(
        """
        INSERT INTO production_orders(
            organisation_id,
            order_number,
            purpose,
            product_ref,
            product_description,
            quantity_ordered,
            created_by,
            created_at,
            updated_at
        )
        VALUES(?,?,?,?,?,?,?,?,?)
        """,
        (
            str(organisation.id),
            "MO-WP2-QTY-001",
            "WP2 quantity test",
            "PROD-QTY-001",
            "Quantity test product",
            10,
            str(user.identity_id),
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00",
        ),
    ).lastrowid

    stage_id = db.execute(
        """
        INSERT INTO production_stages(
            production_order_id,
            stage_code,
            stage_name,
            stage_sequence,
            location,
            status
        )
        VALUES(?,?,?,?,?,?)
        """,
        (
            order_id,
            "CUT",
            "Cutting",
            1,
            "Factory Floor",
            "In Progress",
        ),
    ).lastrowid
    db.commit()

    first = record_stage_quantities(
        db,
        organisation_id=str(organisation.id),
        production_order_id=order_id,
        stage_id=stage_id,
        accepted_quantity=Decimal("4"),
        rejected_quantity=Decimal("1"),
        recorded_by=str(user.identity_id),
        rejected_reason_code="DEFECT",
        accepted_idempotency_key="WP2-ACCEPTED-001",
        rejected_idempotency_key="WP2-REJECTED-001",
    )

    second = record_stage_quantities(
        db,
        organisation_id=str(organisation.id),
        production_order_id=order_id,
        stage_id=stage_id,
        accepted_quantity=Decimal("4"),
        rejected_quantity=Decimal("1"),
        recorded_by=str(user.identity_id),
        rejected_reason_code="DEFECT",
        accepted_idempotency_key="WP2-ACCEPTED-001",
        rejected_idempotency_key="WP2-REJECTED-001",
    )

    rows = db.execute(
        """
        SELECT quantity_type, quantity, idempotency_key
        FROM production_quantity_ledger
        WHERE organisation_id=?
          AND production_order_id=?
        ORDER BY quantity_ledger_id
        """,
        (str(organisation.id), order_id),
    ).fetchall()

    assert first["accepted_ledger_id"] == second["accepted_ledger_id"]
    assert first["rejected_ledger_id"] == second["rejected_ledger_id"]
    assert len(rows) == 2
    assert rows[0]["quantity_type"] == "ACCEPTED"
    assert rows[0]["quantity"] == 4
    assert rows[1]["quantity_type"] == "REJECTED"
    assert rows[1]["quantity"] == 1

    db.close()
