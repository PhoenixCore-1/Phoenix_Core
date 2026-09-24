from decimal import Decimal
from uuid import UUID, uuid4

from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.bom_service import BOMService
from phoenix_production_module.production.bom_version_service import BOMVersionService
from phoenix_production_module.production.bom_component_service import BOMComponentService


def test_add_bom_component(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())
    product_id = UUID(uuid4().__str__())
    component_product_id = UUID(uuid4().__str__())
    identity_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (str(organisation_id), "ORG-C", "Component Organisation", "ACTIVE",
         "2026-01-01T00:00:00+00:00"),
    )

    db.execute(
        "INSERT INTO identities(id,identity_type,status,created_at) VALUES (?,?,?,?)",
        (str(identity_id), "HUMAN", "ACTIVE",
         "2026-01-01T00:00:00+00:00"),
    )

    for pid, code, name in (
        (product_id, "PROD-FG", "Finished Good"),
        (component_product_id, "PROD-COMP", "Component"),
    ):
        db.execute(
            """
            INSERT INTO production_products(
                id,organisation_id,code,name,description,uom,status,
                created_at,updated_at,created_by,updated_by
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                str(pid), str(organisation_id), code, name, None, "EA",
                "ACTIVE",
                "2026-01-01T00:00:00+00:00",
                "2026-01-01T00:00:00+00:00",
                str(identity_id), str(identity_id),
            ),
        )

    db.commit()

    bom = BOMService(db).create_bom(
        organisation_id=organisation_id,
        product_id=product_id,
        code="BOM-C",
        name="Component BOM",
        created_by=identity_id,
    )

    version = BOMVersionService(db).create_version(
        organisation_id=organisation_id,
        bom_id=bom.id,
        version_number=1,
    )

    component = BOMComponentService(db).add_component(
        organisation_id=organisation_id,
        bom_version_id=version.id,
        component_product_id=component_product_id,
        quantity=Decimal("2.5"),
        uom="EA",
        sequence=1,
    )

    row = db.execute(
        """
        SELECT component_product_id, quantity, uom, sequence
        FROM production_bom_components
        WHERE id=?
        """,
        (str(component.id),),
    ).fetchone()

    assert row is not None
    assert row["component_product_id"] == str(component_product_id)
    assert row["quantity"] == 2.5
    assert row["uom"] == "EA"
    assert row["sequence"] == 1
