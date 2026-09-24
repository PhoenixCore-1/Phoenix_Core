from decimal import Decimal
from uuid import UUID, uuid4

from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.spc_service import SPCDefinitionService
from phoenix_production_module.production.spc_cost_service import SPCCostComponentService


def test_add_spc_cost_component(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (
            str(organisation_id),
            "ORG-COST",
            "Cost Organisation",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
    )
    db.commit()

    definition = SPCDefinitionService(db).create_definition(
        organisation_id=organisation_id,
        code="SPC-COST",
        name="Cost Standard",
    )

    component = SPCCostComponentService(db).add_component(
        organisation_id=organisation_id,
        spc_definition_id=definition.id,
        code="LABOUR",
        name="Direct Labour",
        cost=Decimal("125.50"),
        currency="zar",
        sequence=1,
    )

    row = db.execute(
        """
        SELECT spc_definition_id, code, name, cost, currency, sequence
        FROM production_spc_cost_components
        WHERE id=?
        """,
        (str(component.id),),
    ).fetchone()

    assert row is not None
    assert row["spc_definition_id"] == str(definition.id)
    assert row["code"] == "LABOUR"
    assert row["name"] == "Direct Labour"
    assert row["cost"] == 125.50
    assert row["currency"] == "ZAR"
    assert row["sequence"] == 1
