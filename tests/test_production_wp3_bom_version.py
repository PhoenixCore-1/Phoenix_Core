from uuid import UUID, uuid4

import pytest

from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.bom_service import BOMService
from phoenix_production_module.production.bom_version_service import BOMVersionService
from phoenix_production_module.production.spc_service import SPCDefinitionService
from phoenix_core.errors import ValidationError


def test_create_bom_version(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())
    product_id = UUID(uuid4().__str__())
    identity_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (
            str(organisation_id),
            "ORG-V",
            "Version Organisation",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
    )

    db.execute(
        "INSERT INTO identities(id,identity_type,status,created_at) VALUES (?,?,?,?)",
        (
            str(identity_id),
            "HUMAN",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
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
            str(product_id),
            str(organisation_id),
            "PROD-V",
            "Version Product",
            None,
            "EA",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00",
            str(identity_id),
            str(identity_id),
        ),
    )

    db.commit()

    bom_service = BOMService(db)

    bom = bom_service.create_bom(
        organisation_id=organisation_id,
        product_id=product_id,
        code="BOM-V",
        name="Version BOM",
        created_by=identity_id,
    )

    version_service = BOMVersionService(db)

    version = version_service.create_version(
        organisation_id=organisation_id,
        bom_id=bom.id,
        version_number=1,
    )

    loaded = version_service.get_version(
        organisation_id=organisation_id,
        version_id=version.id,
    )

    assert loaded.id == version.id
    assert loaded.bom_id == bom.id
    assert loaded.version_number == 1
    assert loaded.status == "DRAFT"
    assert loaded.published_at is None

def test_reuse_active_spc_across_bom_versions(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())
    product_id = UUID(uuid4().__str__())
    identity_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (
            str(organisation_id),
            "ORG-SPC-REUSE",
            "SPC Reuse Organisation",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
    )

    db.execute(
        "INSERT INTO identities(id,identity_type,status,created_at) VALUES (?,?,?,?)",
        (
            str(identity_id),
            "HUMAN",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
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
            str(product_id),
            str(organisation_id),
            "PROD-SPC-REUSE",
            "SPC Reuse Product",
            None,
            "EA",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00",
            str(identity_id),
            str(identity_id),
        ),
    )
    db.commit()

    bom_service = BOMService(db)
    version_service = BOMVersionService(db)

    bom_one = bom_service.create_bom(
        organisation_id=organisation_id,
        product_id=product_id,
        code="BOM-SPC-001",
        name="Reusable SPC BOM One",
        created_by=identity_id,
    )

    bom_two = bom_service.create_bom(
        organisation_id=organisation_id,
        product_id=product_id,
        code="BOM-SPC-002",
        name="Reusable SPC BOM Two",
        created_by=identity_id,
    )

    from phoenix_production_module.production.spc_cost_service import (
        SPCCostComponentService,
    )
    from phoenix_production_module.production.spc_service import (
        SPCDefinitionService,
    )

    spc_service = SPCDefinitionService(db)
    cost_service = SPCCostComponentService(db)

    spc = spc_service.create_definition(
        organisation_id=organisation_id,
        code="SPC-REUSE-001",
        name="Reusable SPC",
        created_by=identity_id,
    )

    cost_service.add_component(
        organisation_id=organisation_id,
        spc_definition_id=spc.id,
        code="LABOUR",
        name="Labour",
        cost=100,
        currency="ZAR",
        sequence=1,
    )

    active_spc = spc_service.activate_definition(
        organisation_id=organisation_id,
        definition_id=spc.id,
        updated_by=identity_id,
    )

    version_one = version_service.create_version(
        organisation_id=organisation_id,
        bom_id=bom_one.id,
        version_number=1,
        spc_definition_id=active_spc.id,
    )

    version_two = version_service.create_version(
        organisation_id=organisation_id,
        bom_id=bom_two.id,
        version_number=1,
        spc_definition_id=active_spc.id,
    )

    loaded_one = version_service.get_version(
        organisation_id=organisation_id,
        version_id=version_one.id,
    )
    loaded_two = version_service.get_version(
        organisation_id=organisation_id,
        version_id=version_two.id,
    )

    assert loaded_one.spc_definition_id == active_spc.id
    assert loaded_two.spc_definition_id == active_spc.id

def test_draft_spc_cannot_be_assigned_to_bom_version(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())
    product_id = UUID(uuid4().__str__())
    identity_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (
            str(organisation_id),
            "ORG-SPC-DRAFT",
            "Draft SPC Organisation",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
    )
    db.execute(
        "INSERT INTO identities(id,identity_type,status,created_at) VALUES (?,?,?,?)",
        (
            str(identity_id),
            "HUMAN",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
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
            str(product_id),
            str(organisation_id),
            "PROD-DRAFT-SPC",
            "Draft SPC Product",
            None,
            "EA",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
            "2026-01-01T00:00:00+00:00",
            str(identity_id),
            str(identity_id),
        ),
    )
    db.commit()

    bom = BOMService(db).create_bom(
        organisation_id=organisation_id,
        product_id=product_id,
        code="BOM-DRAFT-SPC",
        name="Draft SPC BOM",
        created_by=identity_id,
    )

    spc = SPCDefinitionService(db).create_definition(
        organisation_id=organisation_id,
        code="SPC-DRAFT-001",
        name="Draft SPC",
        created_by=identity_id,
    )

    version_service = BOMVersionService(db)

    with pytest.raises(ValidationError):
        version_service.create_version(
            organisation_id=organisation_id,
            bom_id=bom.id,
            version_number=1,
            spc_definition_id=spc.id,
        )


