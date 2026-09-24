from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from phoenix_core.errors import ValidationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.spc_service import SPCDefinitionService
from phoenix_production_module.production.spc_cost_service import SPCCostComponentService


def test_spc_without_cost_components_cannot_be_activated(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (
            str(organisation_id),
            "ORG-NOCOST",
            "No Cost Organisation",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
    )
    db.commit()

    service = SPCDefinitionService(db)

    definition = service.create_definition(
        organisation_id=organisation_id,
        code="SPC-NOCOST",
        name="Incomplete Standard",
    )

    with pytest.raises(ValidationError):
        service.activate_definition(
            organisation_id=organisation_id,
            definition_id=definition.id,
        )


def test_spc_with_cost_component_can_be_activated(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (
            str(organisation_id),
            "ORG-WCOST",
            "With Cost Organisation",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
    )
    db.commit()

    service = SPCDefinitionService(db)

    definition = service.create_definition(
        organisation_id=organisation_id,
        code="SPC-WCOST",
        name="Complete Standard",
    )

    SPCCostComponentService(db).add_component(
        organisation_id=organisation_id,
        spc_definition_id=definition.id,
        code="LABOUR",
        name="Labour",
        cost=Decimal("100"),
        currency="ZAR",
        sequence=1,
    )

    activated = service.activate_definition(
        organisation_id=organisation_id,
        definition_id=definition.id,
    )

    assert activated.status == "ACTIVE"
