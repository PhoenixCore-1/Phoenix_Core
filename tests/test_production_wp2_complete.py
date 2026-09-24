from decimal import Decimal
from pathlib import Path

from phoenix_core.api.application import CoreApi
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.integration import (
    complete_order,
    record_stage_quantities,
    release_order,
    start_order,
)


def test_complete_order_finishes_single_stage_order(tmp_path: Path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()
    api = CoreApi(db)

    organisation = api.organisation_service.create_organisation(
        code="PROD-WP2-COMPLETE",
        name="Production WP2 Complete",
    )
    user = api.user_service.create_user(
        username="prod-wp2-complete-user",
        display_name="Production WP2 Complete User",
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
            "MO-WP2-COMPLETE-001",
            "WP2 completion test",
            "PROD-COMPLETE-001",
            "Completion test product",
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
            "Ready",
        ),
    ).lastrowid
    db.commit()

    release_order(
        db,
        organisation_id=str(organisation.id),
        production_order_id=order_id,
        recorded_by=str(user.identity_id),
    )

    start_order(
        db,
        organisation_id=str(organisation.id),
        production_order_id=order_id,
        recorded_by=str(user.identity_id),
        stage_id=stage_id,
    )

    record_stage_quantities(
        db,
        organisation_id=str(organisation.id),
        production_order_id=order_id,
        stage_id=stage_id,
        accepted_quantity=Decimal("8"),
        rejected_quantity=Decimal("2"),
        recorded_by=str(user.identity_id),
        accepted_idempotency_key="WP2-COMPLETE-ACCEPTED-001",
        rejected_idempotency_key="WP2-COMPLETE-REJECTED-001",
    )
    db.commit()

    result = complete_order(
        db,
        organisation_id=str(organisation.id),
        production_order_id=order_id,
        recorded_by=str(user.identity_id),
        stage_id=stage_id,
    )

    order = db.execute(
        """
        SELECT status, current_stage_id
        FROM production_orders
        WHERE production_order_id=?
          AND organisation_id=?
        """,
        (order_id, str(organisation.id)),
    ).fetchone()

    stage = db.execute(
        """
        SELECT status, quantity_completed, quantity_rejected
        FROM production_stages
        WHERE stage_id=?
        """,
        (stage_id,),
    ).fetchone()

    event = db.execute(
        """
        SELECT event_type
        FROM production_events
        WHERE production_order_id=?
        ORDER BY production_event_id DESC
        LIMIT 1
        """,
        (order_id,),
    ).fetchone()

    assert result["status"] == "Completed"
    assert order["status"] == "Completed"
    assert order["current_stage_id"] == stage_id
    assert stage["status"] == "Complete"
    assert stage["quantity_completed"] == 8
    assert stage["quantity_rejected"] == 2
    assert event["event_type"] == "COMPLETE"

    db.close()
