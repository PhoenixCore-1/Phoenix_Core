from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from phoenix_core.errors import ConflictError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.bom_service import BOMService
from phoenix_production_module.production.bom_version_service import BOMVersionService
from phoenix_production_module.production.bom_component_service import BOMComponentService


def test_duplicate_bom_code_raises_conflict(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())
    product_id = UUID(uuid4().__str__())
    identity_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (str(organisation_id), "ORG-C", "Conflict Organisation", "ACTIVE",
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
            str(product_id), str(organisation_id), "PROD-C",
            "Conflict Product", None, "EA", "ACTIVE",
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00",
            str(identity_id), str(identity_id),
        ),
    )
    db.commit()

    service = BOMService(db)
    service.create_bom(
        organisation_id=organisation_id,
        product_id=product_id,
        code="BOM-C",
        name="Conflict BOM",
        created_by=identity_id,
    )

    with pytest.raises(ConflictError):
        service.create_bom(
            organisation_id=organisation_id,
            product_id=product_id,
            code="BOM-C",
            name="Duplicate BOM",
            created_by=identity_id,
        )


def test_duplicate_bom_version_raises_conflict(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())
    product_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (str(organisation_id), "ORG-V", "Version Organisation", "ACTIVE",
         "2026-01-01T00:00:00+00:00"),
    )
    db.execute(
        """
        INSERT INTO production_products(
            id,organisation_id,code,name,description,uom,status,
            created_at,updated_at
        )
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (
            str(product_id), str(organisation_id), "PROD-V",
            "Version Product", None, "EA", "ACTIVE",
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00",
        ),
    )
    db.commit()

    bom = BOMService(db).create_bom(
        organisation_id=organisation_id,
        product_id=product_id,
        code="BOM-V",
        name="Version BOM",
    )

    service = BOMVersionService(db)
    service.create_version(
        organisation_id=organisation_id,
        bom_id=bom.id,
        version_number=1,
    )

    with pytest.raises(ConflictError):
        service.create_version(
            organisation_id=organisation_id,
            bom_id=bom.id,
            version_number=1,
        )


def test_duplicate_component_sequence_raises_conflict(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())
    product_id = UUID(uuid4().__str__())
    component_product_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (str(organisation_id), "ORG-S", "Sequence Organisation", "ACTIVE",
         "2026-01-01T00:00:00+00:00"),
    )

    for pid, code, name in (
        (product_id, "PROD-S", "Sequence Product"),
        (component_product_id, "COMP-S", "Sequence Component"),
    ):
        db.execute(
            """
            INSERT INTO production_products(
                id,organisation_id,code,name,description,uom,status,
                created_at,updated_at
            )
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                str(pid), str(organisation_id), code, name, None,
                "EA", "ACTIVE",
                "2026-01-01T00:00:00+00:00",
                "2026-01-01T00:00:00+00:00",
            ),
        )

    db.commit()

    bom = BOMService(db).create_bom(
        organisation_id=organisation_id,
        product_id=product_id,
        code="BOM-S",
        name="Sequence BOM",
    )

    version = BOMVersionService(db).create_version(
        organisation_id=organisation_id,
        bom_id=bom.id,
        version_number=1,
    )

    service = BOMComponentService(db)
    service.add_component(
        organisation_id=organisation_id,
        bom_version_id=version.id,
        component_product_id=component_product_id,
        quantity=Decimal("1"),
        uom="EA",
        sequence=1,
    )

    with pytest.raises(ConflictError):
        service.add_component(
            organisation_id=organisation_id,
            bom_version_id=version.id,
            component_product_id=component_product_id,
            quantity=Decimal("2"),
            uom="EA",
            sequence=1,
        )
