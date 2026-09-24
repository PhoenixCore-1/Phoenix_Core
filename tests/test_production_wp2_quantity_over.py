from decimal import Decimal
from pathlib import Path

import pytest

from phoenix_core.api.application import CoreApi
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.integration import record_stage_quantities


def test_record_stage_quantities_rejects_over_available_input(tmp_path: Path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()
    api = CoreApi(db)

    organisation = api.organisation_service.create_organisation(
        code="PROD-WP2-QTY-OVER",
        name="Production WP2 Quantity Over",
    )
    user = api.user_service.create_user(
        username="prod-wp2-qty-over-user",
        display_name="Production WP2 Quantity Over User",
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
            "MO-WP2-QTY-OVER-001",
            "WP2 over-recording test",
            "PROD-QTY-OVER-001",
            "Over-recording test product",
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

    with pytest.raises(ValueError):
        record_stage_quantities(
            db,
            organisation_id=str(organisation.id),
            production_order_id=order_id,
            stage_id=stage_id,
            accepted_quantity=Decimal("11"),
            recorded_by=str(user.identity_id),
            accepted_idempotency_key="WP2-OVER-001",
        )

    count = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM production_quantity_ledger
        WHERE organisation_id=?
          AND production_order_id=?
        """,
        (str(organisation.id), order_id),
    ).fetchone()["count"]

    assert count == 0

    db.close()
