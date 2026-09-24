from uuid import UUID, uuid4

import pytest

from phoenix_core.errors import ConflictError, NotFoundError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.spc_service import SPCDefinitionService


def test_spc_definition_isolation(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_a = UUID(uuid4().__str__())
    organisation_b = UUID(uuid4().__str__())

    for oid, code, name in (
        (organisation_a, "ORG-A", "Organisation A"),
        (organisation_b, "ORG-B", "Organisation B"),
    ):
        db.execute(
            "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
            (
                str(oid), code, name, "ACTIVE",
                "2026-01-01T00:00:00+00:00",
            ),
        )
    db.commit()

    service = SPCDefinitionService(db)

    definition = service.create_definition(
        organisation_id=organisation_a,
        code="SPC-ISO",
        name="Isolated SPC",
    )

    with pytest.raises(NotFoundError):
        service.get_definition(
            organisation_id=organisation_b,
            definition_id=definition.id,
        )


def test_duplicate_spc_code_raises_conflict(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (
            str(organisation_id),
            "ORG-D",
            "Duplicate Organisation",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
    )
    db.commit()

    service = SPCDefinitionService(db)

    service.create_definition(
        organisation_id=organisation_id,
        code="SPC-DUP",
        name="First Definition",
    )

    with pytest.raises(ConflictError):
        service.create_definition(
            organisation_id=organisation_id,
            code="SPC-DUP",
            name="Duplicate Definition",
        )
