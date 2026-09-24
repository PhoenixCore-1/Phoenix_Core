from uuid import UUID, uuid4

from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.spc_service import SPCDefinitionService


def test_create_and_get_spc_definition(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())
    identity_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (
            str(organisation_id),
            "ORG-SPC",
            "SPC Organisation",
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
    db.commit()

    service = SPCDefinitionService(db)

    definition = service.create_definition(
        organisation_id=organisation_id,
        code="SPC-001",
        name="Production Cost Standard",
        created_by=identity_id,
    )

    loaded = service.get_definition(
        organisation_id=organisation_id,
        definition_id=definition.id,
    )

    assert loaded.id == definition.id
    assert loaded.organisation_id == organisation_id
    assert loaded.code == "SPC-001"
    assert loaded.name == "Production Cost Standard"
    assert loaded.status == "DRAFT"
    assert loaded.created_by == identity_id
