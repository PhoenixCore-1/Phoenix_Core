from uuid import uuid4

from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.bom_service import BOMService


def _setup_db(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = str(uuid4())
    product_id = str(uuid4())
    identity_id = str(uuid4())

    db.execute(
        """
        INSERT INTO organisations(id, code, name, status, created_at)
        VALUES (?,?,?,?,?)
        """,
        (
            organisation_id,
            "TEST-ORG",
            "Test Organisation",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
    )

    db.execute(
        """
        INSERT INTO identities(id, identity_type, status, created_at)
        VALUES (?,?,?,?)
        """,
        (
            identity_id,
            "HUMAN",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
    )

    db.execute(
        """
        INSERT INTO production_products(
            id, organisation_id, code, name, description,
            uom, status, created_at, updated_at,
            created_by, updated_by
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            product_id,
            organisation_id,
            "PROD-001",
            "Test Product",
            None,
            "EA",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00",
            identity_id,
            identity_id,
        ),
    )

    db.commit()

    return db, organisation_id, product_id, identity_id


def test_create_and_get_bom(tmp_path):
    db, organisation_id, product_id, identity_id = _setup_db(tmp_path)

    service = BOMService(db)

    bom = service.create_bom(
        organisation_id=__import__("uuid").UUID(organisation_id),
        product_id=__import__("uuid").UUID(product_id),
        code="BOM-001",
        name="Test BOM",
        created_by=__import__("uuid").UUID(identity_id),
    )

    loaded = service.get_bom(
        organisation_id=__import__("uuid").UUID(organisation_id),
        bom_id=bom.id,
    )

    assert loaded.id == bom.id
    assert loaded.organisation_id == __import__("uuid").UUID(organisation_id)
    assert loaded.product_id == __import__("uuid").UUID(product_id)
    assert loaded.code == "BOM-001"
    assert loaded.name == "Test BOM"
    assert loaded.status == "DRAFT"
