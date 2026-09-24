from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from phoenix_core.errors import ValidationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.spc_service import SPCDefinitionService
from phoenix_production_module.production.spc_cost_service import SPCCostComponentService


def test_active_spc_definition_cannot_add_cost_component(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (
            str(organisation_id),
            "ORG-FROZEN",
            "Frozen Organisation",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
    )
    db.commit()

    definition_service = SPCDefinitionService(db)
    component_service = SPCCostComponentService(db)

    definition = definition_service.create_definition(
        organisation_id=organisation_id,
        code="SPC-FROZEN",
        name="Frozen Standard",
    )

    component_service.add_component(
        organisation_id=organisation_id,
        spc_definition_id=definition.id,
        code="LABOUR",
        name="Labour",
        cost=Decimal("100"),
        currency="ZAR",
        sequence=1,
    )

    definition_service.activate_definition(
        organisation_id=organisation_id,
        definition_id=definition.id,
    )

    with pytest.raises(ValidationError):
        component_service.add_component(
            organisation_id=organisation_id,
            spc_definition_id=definition.id,
            code="MATERIAL",
            name="Material",
            cost=Decimal("200"),
            currency="ZAR",
            sequence=2,
        )

    count = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM production_spc_cost_components
        WHERE spc_definition_id=?
        """,
        (str(definition.id),),
    ).fetchone()["count"]

    assert count == 1
