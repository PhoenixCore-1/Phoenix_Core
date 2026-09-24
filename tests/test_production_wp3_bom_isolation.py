from uuid import UUID, uuid4

import pytest

from phoenix_core.errors import NotFoundError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.bom_service import BOMService


def test_bom_cannot_be_read_from_another_organisation(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    org_a = UUID(uuid4().__str__())
    org_b = UUID(uuid4().__str__())
    product_a = UUID(uuid4().__str__())
    identity_a = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (str(org_a), "ORG-A", "Organisation A", "ACTIVE", "2026-01-01T00:00:00+00:00"),
    )
    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (str(org_b), "ORG-B", "Organisation B", "ACTIVE", "2026-01-01T00:00:00+00:00"),
    )
    db.execute(
        "INSERT INTO identities(id,identity_type,status,created_at) VALUES (?,?,?,?)",
        (str(identity_a), "HUMAN", "ACTIVE", "2026-01-01T00:00:00+00:00"),
    )
    db.execute(
        """
        INSERT INTO production_products(
            id,organisation_id,code,name,description,uom,status,
            created_at,updated_at,created_by,updated_by
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            str(product_a),
            str(org_a),
            "PROD-A",
            "Product A",
            None,
            "EA",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00",
            str(identity_a),
            str(identity_a),
        ),
    )
    db.commit()

    service = BOMService(db)

    bom = service.create_bom(
        organisation_id=org_a,
        product_id=product_a,
        code="BOM-A",
        name="BOM A",
        created_by=identity_a,
    )

    with pytest.raises(NotFoundError):
        service.get_bom(
            organisation_id=org_b,
            bom_id=bom.id,
        )
