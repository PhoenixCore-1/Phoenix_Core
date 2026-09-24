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


def test_complete_stage_advances_to_next_stage(tmp_path: Path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()
    api = CoreApi(db)

    organisation = api.organisation_service.create_organisation(
        code="PROD-WP2-MULTI",
        name="Production WP2 Multi Stage",
    )
    user = api.user_service.create_user(
        username="prod-wp2-multi-user",
        display_name="Production WP2 Multi Stage User",
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
            "MO-WP2-MULTI-001",
            "WP2 multi-stage test",
            "PROD-MULTI-001",
            "Multi-stage test product",
            10,
            str(user.identity_id),
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00",
        ),
    ).lastrowid

    first_stage_id = db.execute(
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

    second_stage_id = db.execute(
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
            "ASM",
            "Assembly",
            2,
            "Assembly Floor",
            "Waiting",
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
        stage_id=first_stage_id,
    )

    record_stage_quantities(
        db,
        organisation_id=str(organisation.id),
        production_order_id=order_id,
        stage_id=first_stage_id,
        accepted_quantity=Decimal("10"),
        recorded_by=str(user.identity_id),
        accepted_idempotency_key="WP2-MULTI-ACCEPTED-001",
    )
    db.commit()

    result = complete_order(
        db,
        organisation_id=str(organisation.id),
        production_order_id=order_id,
        recorded_by=str(user.identity_id),
        stage_id=first_stage_id,
    )

    order = db.execute(
        """
        SELECT status, current_stage_id, current_location
        FROM production_orders
        WHERE production_order_id=?
          AND organisation_id=?
        """,
        (order_id, str(organisation.id)),
    ).fetchone()

    stages = db.execute(
        """
        SELECT stage_id, status
        FROM production_stages
        WHERE production_order_id=?
        ORDER BY stage_sequence
        """,
        (order_id,),
    ).fetchall()

    events = db.execute(
        """
        SELECT event_type, stage_id
        FROM production_events
        WHERE production_order_id=?
        ORDER BY production_event_id DESC
        LIMIT 2
        """,
        (order_id,),
    ).fetchall()

    assert result["stage_completed"] is True
    assert result["order_completed"] is False
    assert result["next_stage_id"] == second_stage_id
    assert result["next_stage_status"] == "Ready"
    assert order["status"] == "In Production"
    assert order["current_stage_id"] == second_stage_id
    assert order["current_location"] == "Assembly Floor"
    assert stages[0]["stage_id"] == first_stage_id
    assert stages[0]["status"] == "Complete"
    assert stages[1]["stage_id"] == second_stage_id
    assert stages[1]["status"] == "Ready"

    event_types = {row["event_type"] for row in events}
    assert "STAGE_COMPLETE" in event_types
    assert "STAGE_READY" in event_types

    db.close()
