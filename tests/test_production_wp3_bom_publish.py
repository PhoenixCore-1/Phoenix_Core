from uuid import UUID, uuid4

from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.bom_service import BOMService
from phoenix_production_module.production.bom_version_service import BOMVersionService


def test_publish_bom_version(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())
    product_id = UUID(uuid4().__str__())
    identity_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (str(organisation_id), "ORG-P", "Publish Organisation", "ACTIVE",
         "2026-01-01T00:00:00+00:00"),
    )
    db.execute(
        "INSERT INTO identities(id,identity_type,status,created_at) VALUES (?,?,?,?)",
        (str(identity_id), "HUMAN", "ACTIVE",
         "2026-01-01T00:00:00+00:00"),
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
            str(product_id), str(organisation_id), "PROD-P",
            "Publish Product", None, "EA", "ACTIVE",
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00",
            str(identity_id), str(identity_id),
        ),
    )
    db.commit()

    bom = BOMService(db).create_bom(
        organisation_id=organisation_id,
        product_id=product_id,
        code="BOM-P",
        name="Publish BOM",
        created_by=identity_id,
    )

    versions = BOMVersionService(db)

    version = versions.create_version(
        organisation_id=organisation_id,
        bom_id=bom.id,
        version_number=1,
    )

    published = versions.publish_version(
        organisation_id=organisation_id,
        version_id=version.id,
        published_by=identity_id,
    )

    assert published.id == version.id
    assert published.status == "PUBLISHED"
    assert published.published_at is not None
