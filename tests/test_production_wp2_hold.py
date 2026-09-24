from pathlib import Path
from decimal import Decimal

from phoenix_core.api.application import CoreApi
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.integration import hold_order, release_order


def test_hold_order_persists_hold_and_event(tmp_path: Path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()
    api = CoreApi(db)

    organisation = api.organisation_service.create_organisation(
        code="PROD-WP2-HOLD",
        name="Production WP2 Hold",
    )
    user = api.user_service.create_user(
        username="prod-wp2-hold-user",
        display_name="Production WP2 Hold User",
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
            "MO-WP2-HOLD-001",
            "WP2 hold test",
            "PROD-HOLD-001",
            "Hold test product",
            10,
            str(user.identity_id),
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00",
        ),
    ).lastrowid

    db.execute(
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
    )
    db.commit()

    release_order(
        db,
        organisation_id=str(organisation.id),
        production_order_id=order_id,
        recorded_by=str(user.identity_id),
    )

    result = hold_order(
        db,
        organisation_id=str(organisation.id),
        production_order_id=order_id,
        recorded_by=str(user.identity_id),
        reason="Material quality issue",
        problem_type="Material Problem",
        affected_quantity=Decimal("3"),
    )

    order = db.execute(
        """
        SELECT status
        FROM production_orders
        WHERE production_order_id=?
          AND organisation_id=?
        """,
        (order_id, str(organisation.id)),
    ).fetchone()

    stage = db.execute(
        """
        SELECT status, notes
        FROM production_stages
        WHERE production_order_id=?
        LIMIT 1
        """,
        (order_id,),
    ).fetchone()

    hold = db.execute(
        """
        SELECT problem_type, description, affected_quantity, status
        FROM production_holds
        WHERE hold_id=?
        """,
        (result["hold_id"],),
    ).fetchone()

    event = db.execute(
        """
        SELECT event_type, organisation_id, production_order_id
        FROM production_events
        WHERE production_order_id=?
        ORDER BY production_event_id DESC
        LIMIT 1
        """,
        (order_id,),
    ).fetchone()

    assert result["from_state"] == "RELEASED"
    assert result["to_state"] == "RELEASED"
    assert result["stage_status"] == "On Hold"
    assert order["status"] == "Released to Production"
    assert stage["status"] == "On Hold"
    assert stage["notes"] == "Material quality issue"
    assert hold["problem_type"] == "Material Problem"
    assert hold["description"] == "Material quality issue"
    assert hold["affected_quantity"] == 3
    assert hold["status"] == "Open"
    assert event["event_type"] == "HOLD"
    assert event["organisation_id"] == str(organisation.id)
    assert event["production_order_id"] == order_id

    db.close()

