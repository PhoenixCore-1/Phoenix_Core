from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from phoenix_core.errors import ValidationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.spc_service import SPCDefinitionService
from phoenix_production_module.production.spc_cost_service import SPCCostComponentService


def test_activate_spc_definition(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())
    identity_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (
            str(organisation_id), "ORG-ACT", "Activation Organisation",
            "ACTIVE", "2026-01-01T00:00:00+00:00",
        ),
    )
    db.execute(
        "INSERT INTO identities(id,identity_type,status,created_at) VALUES (?,?,?,?)",
        (
            str(identity_id), "HUMAN", "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
    )
    db.commit()

    service = SPCDefinitionService(db)

    definition = service.create_definition(
        organisation_id=organisation_id,
        code="SPC-ACT",
        name="Activatable Standard",
        created_by=identity_id,
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
        updated_by=identity_id,
    )

    assert activated.status == "ACTIVE"
    assert activated.updated_by == identity_id


def test_active_spc_definition_cannot_be_activated_again(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (
            str(organisation_id), "ORG-REACT", "Reactivation Organisation",
            "ACTIVE", "2026-01-01T00:00:00+00:00",
        ),
    )
    db.commit()

    service = SPCDefinitionService(db)

    definition = service.create_definition(
        organisation_id=organisation_id,
        code="SPC-REACT",
        name="Reactivation Standard",
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

    with pytest.raises(ValidationError):
        service.activate_definition(
            organisation_id=organisation_id,
            definition_id=definition.id,
        )
