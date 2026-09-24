from pathlib import Path

import pytest

from phoenix_core.api.application import CoreApi
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.integration import release_order


def test_release_order_cannot_cross_organisation_boundary(tmp_path: Path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()
    api = CoreApi(db)

    organisation_a = api.organisation_service.create_organisation(
        code="PROD-WP2-ORG-A",
        name="Production WP2 Org A",
    )
    organisation_b = api.organisation_service.create_organisation(
        code="PROD-WP2-ORG-B",
        name="Production WP2 Org B",
    )

    user = api.user_service.create_user(
        username="prod-wp2-isolation-user",
        display_name="Production WP2 Isolation User",
        password="CorrectPassword123!",
    )
    api.company_membership_service.add_membership(
        user.identity_id,
        organisation_a.id,
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
            str(organisation_a.id),
            "MO-WP2-ISOLATION-001",
            "WP2 isolation test",
            "PROD-ISO-001",
            "Isolation test product",
            10,
            str(user.identity_id),
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00",
        ),
    ).lastrowid
    db.commit()

    with pytest.raises(ValueError):
        release_order(
            db,
            organisation_id=str(organisation_b.id),
            production_order_id=order_id,
            recorded_by=str(user.identity_id),
        )

    order = db.execute(
        """
        SELECT status, organisation_id
        FROM production_orders
        WHERE production_order_id=?
        """,
        (order_id,),
    ).fetchone()

    assert order["status"] == "Planned"
    assert order["organisation_id"] == str(organisation_a.id)

    db.close()
