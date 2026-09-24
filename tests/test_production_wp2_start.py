from pathlib import Path

from phoenix_core.api.application import CoreApi
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.integration import release_order, start_order


def test_start_order_persists_active_stage(tmp_path: Path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()
    api = CoreApi(db)

    organisation = api.organisation_service.create_organisation(
        code="PROD-WP2-START",
        name="Production WP2 Start",
    )
    user = api.user_service.create_user(
        username="prod-wp2-start-user",
        display_name="Production WP2 Start User",
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
            "MO-WP2-START-001",
            "WP2 start test",
            "PROD-START-001",
            "Start test product",
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

    result = start_order(
        db,
        organisation_id=str(organisation.id),
        production_order_id=order_id,
        recorded_by=str(user.identity_id),
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

    stage = db.execute(
        """
        SELECT status, start_datetime
        FROM production_stages
        WHERE production_order_id=?
        ORDER BY stage_sequence
        LIMIT 1
        """,
        (order_id,),
    ).fetchone()

    assert result["from_state"] == "RELEASED"
    assert result["to_state"] == "STARTED"
    assert order["status"] == "In Production"
    assert order["current_stage_id"] is not None
    assert order["current_location"] == "Factory Floor"
    assert stage["status"] == "In Progress"
    assert stage["start_datetime"] is not None

    db.close()
