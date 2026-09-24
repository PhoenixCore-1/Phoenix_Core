from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from phoenix_core.errors import ConflictError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.spc_service import SPCDefinitionService
from phoenix_production_module.production.spc_cost_service import SPCCostComponentService


def test_duplicate_spc_component_code_raises_conflict(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (
            str(organisation_id), "ORG-DUP", "Duplicate Organisation",
            "ACTIVE", "2026-01-01T00:00:00+00:00",
        ),
    )
    db.commit()

    definition = SPCDefinitionService(db).create_definition(
        organisation_id=organisation_id,
        code="SPC-DUP",
        name="Duplicate Standard",
    )

    service = SPCCostComponentService(db)

    service.add_component(
        organisation_id=organisation_id,
        spc_definition_id=definition.id,
        code="LABOUR",
        name="Labour",
        cost=Decimal("100"),
        currency="ZAR",
        sequence=1,
    )

    with pytest.raises(ConflictError):
        service.add_component(
            organisation_id=organisation_id,
            spc_definition_id=definition.id,
            code="LABOUR",
            name="Duplicate Labour",
            cost=Decimal("200"),
            currency="ZAR",
            sequence=2,
        )


def test_duplicate_spc_component_sequence_raises_conflict(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (
            str(organisation_id), "ORG-SEQ", "Sequence Organisation",
            "ACTIVE", "2026-01-01T00:00:00+00:00",
        ),
    )
    db.commit()

    definition = SPCDefinitionService(db).create_definition(
        organisation_id=organisation_id,
        code="SPC-SEQ",
        name="Sequence Standard",
    )

    service = SPCCostComponentService(db)

    service.add_component(
        organisation_id=organisation_id,
        spc_definition_id=definition.id,
        code="LABOUR",
        name="Labour",
        cost=Decimal("100"),
        currency="ZAR",
        sequence=1,
    )

    with pytest.raises(ConflictError):
        service.add_component(
            organisation_id=organisation_id,
            spc_definition_id=definition.id,
            code="MATERIAL",
            name="Material",
            cost=Decimal("200"),
            currency="ZAR",
            sequence=1,
        )
