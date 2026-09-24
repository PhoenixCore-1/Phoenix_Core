from pathlib import Path
from uuid import uuid4

from phoenix_core.api.application import CoreApi
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.integration import release_order


def test_release_order_persists_state_and_event(tmp_path: Path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()
    api = CoreApi(db)

    organisation = api.organisation_service.create_organisation(
        code="PROD-WP2",
        name="Production WP2",
    )
    user = api.user_service.create_user(
        username="prod-wp2-user",
        display_name="Production WP2 User",
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
            "MO-WP2-001",
            "WP2 execution test",
            "PROD-001",
            "Test product",
            10,
            str(user.identity_id),
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00",
        ),
    ).lastrowid
    db.commit()

    result = release_order(
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

    event = db.execute(
        """
        SELECT event_type, organisation_id, production_order_id, user_id
        FROM production_events
        WHERE production_order_id=?
        ORDER BY production_event_id DESC
        LIMIT 1
        """,
        (order_id,),
    ).fetchone()

    assert result["from_state"] == "PLANNED"
    assert result["to_state"] == "RELEASED"
    assert order["status"] == "Released to Production"
    assert event["event_type"] == "RELEASE"
    assert event["organisation_id"] == str(organisation.id)
    assert event["production_order_id"] == order_id
    assert event["user_id"] == str(user.identity_id)

    db.close()
