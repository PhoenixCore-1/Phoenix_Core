from pathlib import Path

import pytest

from phoenix_core.api.application import CoreApi
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.integration import start_order, start_stage


def test_start_stage_requires_preceding_stage_complete(tmp_path: Path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()
    api = CoreApi(db)

    organisation = api.organisation_service.create_organisation(
        code="PROD-WP2-SEQ",
        name="Production WP2 Sequence",
    )
    user = api.user_service.create_user(
        username="prod-wp2-seq-user",
        display_name="Production WP2 Sequence User",
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
            "MO-WP2-SEQ-001",
            "WP2 stage sequencing test",
            "PROD-SEQ-001",
            "Sequence test product",
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

    from phoenix_production_module.production.integration import release_order

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

    with pytest.raises(
        ValueError,
        match="preceding stage is not complete",
    ):
        start_stage(
            db,
            organisation_id=str(organisation.id),
            production_order_id=order_id,
            recorded_by=str(user.identity_id),
            stage_id=second_stage_id,
        )

    second_stage = db.execute(
        """
        SELECT status
        FROM production_stages
        WHERE stage_id=?
        """,
        (second_stage_id,),
    ).fetchone()

    assert second_stage["status"] == "Waiting"

    db.close()
