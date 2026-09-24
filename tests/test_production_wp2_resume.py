from decimal import Decimal
from pathlib import Path

from phoenix_core.api.application import CoreApi
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.integration import (
    hold_order,
    release_order,
    resume_order,
    start_order,
)


def test_resume_order_resolves_hold_and_restores_stage(tmp_path: Path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()
    api = CoreApi(db)

    organisation = api.organisation_service.create_organisation(
        code="PROD-WP2-RESUME",
        name="Production WP2 Resume",
    )
    user = api.user_service.create_user(
        username="prod-wp2-resume-user",
        display_name="Production WP2 Resume User",
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
            "MO-WP2-RESUME-001",
            "WP2 resume test",
            "PROD-RESUME-001",
            "Resume test product",
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

    start_order(
        db,
        organisation_id=str(organisation.id),
        production_order_id=order_id,
        recorded_by=str(user.identity_id),
    )

    hold_result = hold_order(
        db,
        organisation_id=str(organisation.id),
        production_order_id=order_id,
        recorded_by=str(user.identity_id),
        reason="Material quality issue",
        problem_type="Material Problem",
        affected_quantity=Decimal("3"),
    )

    result = resume_order(
        db,
        organisation_id=str(organisation.id),
        production_order_id=order_id,
        recorded_by=str(user.identity_id),
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
        SELECT status
        FROM production_stages
        WHERE production_order_id=?
        LIMIT 1
        """,
        (order_id,),
    ).fetchone()

    hold = db.execute(
        """
        SELECT status, resolution, resolved_by
        FROM production_holds
        WHERE hold_id=?
        """,
        (hold_result["hold_id"],),
    ).fetchone()

    events = db.execute(
        """
        SELECT event_type
        FROM production_events
        WHERE production_order_id=?
        ORDER BY production_event_id
        """,
        (order_id,),
    ).fetchall()

    event_types = [row["event_type"] for row in events]

    assert result["from_state"] == "HOLD"
    assert result["to_state"] == "STARTED"
    assert result["status"] == "In Production"
    assert result["stage_status"] == "In Progress"
    assert order["status"] == "In Production"
    assert stage["status"] == "In Progress"
    assert hold["status"] == "Resolved"
    assert hold["resolution"] == "Production resumed"
    assert hold["resolved_by"] == str(user.identity_id)
    assert "RELEASE" in event_types
    assert "START" in event_types
    assert "HOLD" in event_types
    assert "RESUME" in event_types
    assert "ETA_HOLD_IMPACT" in event_types

    db.close()
