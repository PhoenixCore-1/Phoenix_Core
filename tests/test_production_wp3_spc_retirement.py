from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from phoenix_core.errors import ValidationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.spc_service import SPCDefinitionService
from phoenix_production_module.production.spc_cost_service import SPCCostComponentService


def test_spc_can_be_retired_and_remains_available_for_audit(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (
            str(organisation_id),
            "ORG-RET",
            "Retirement Organisation",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
    )
    db.commit()

    service = SPCDefinitionService(db)

    definition = service.create_definition(
        organisation_id=organisation_id,
        code="SPC-RET",
        name="Retirable Standard",
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

    service.activate_definition(
        organisation_id=organisation_id,
        definition_id=definition.id,
    )

    retired = service.retire_definition(
        organisation_id=organisation_id,
        definition_id=definition.id,
    )

    assert retired.status == "RETIRED"

    audit_view = service.get_definition(
        organisation_id=organisation_id,
        definition_id=definition.id,
    )

    assert audit_view.status == "RETIRED"
    assert audit_view.code == "SPC-RET"
    assert audit_view.name == "Retirable Standard"


def test_retired_spc_cannot_be_activated_again(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (
            str(organisation_id),
            "ORG-RTA",
            "Retired Activation Organisation",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
    )
    db.commit()

    service = SPCDefinitionService(db)

    definition = service.create_definition(
        organisation_id=organisation_id,
        code="SPC-RTA",
        name="Retired Standard",
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

    service.activate_definition(
        organisation_id=organisation_id,
        definition_id=definition.id,
    )

    service.retire_definition(
        organisation_id=organisation_id,
        definition_id=definition.id,
    )

    with pytest.raises(ValidationError):
        service.activate_definition(
            organisation_id=organisation_id,
            definition_id=definition.id,
        )
