from uuid import UUID, uuid4

import pytest

from phoenix_core.errors import ValidationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_production_module.production.spc_service import SPCDefinitionService
from phoenix_production_module.production.spc_cost_service import SPCCostComponentService


def test_negative_spc_cost_is_rejected(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (
            str(organisation_id),
            "ORG-VAL",
            "Validation Organisation",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
    )
    db.commit()

    definition = SPCDefinitionService(db).create_definition(
        organisation_id=organisation_id,
        code="SPC-VAL",
        name="Validation Standard",
    )

    with pytest.raises(ValidationError):
        SPCCostComponentService(db).add_component(
            organisation_id=organisation_id,
            spc_definition_id=definition.id,
            code="NEGATIVE",
            name="Invalid Cost",
            cost="-1",
            currency="ZAR",
            sequence=1,
        )

    count = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM production_spc_cost_components
        WHERE spc_definition_id=?
        """,
        (str(definition.id),),
    ).fetchone()["count"]

    assert count == 0


def test_invalid_spc_sequence_is_rejected(tmp_path):
    db = SQLiteDatabase(tmp_path / "production.db")
    db.initialise_schema()

    organisation_id = UUID(uuid4().__str__())

    db.execute(
        "INSERT INTO organisations(id,code,name,status,created_at) VALUES (?,?,?,?,?)",
        (
            str(organisation_id),
            "ORG-SEQ",
            "Sequence Organisation",
            "ACTIVE",
            "2026-01-01T00:00:00+00:00",
        ),
    )
    db.commit()

    definition = SPCDefinitionService(db).create_definition(
        organisation_id=organisation_id,
        code="SPC-SEQ",
        name="Sequence Standard",
    )

    with pytest.raises(ValidationError):
        SPCCostComponentService(db).add_component(
            organisation_id=organisation_id,
            spc_definition_id=definition.id,
            code="BADSEQ",
            name="Invalid Sequence",
            cost="10",
            currency="ZAR",
            sequence=0,
        )

    count = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM production_spc_cost_components
        WHERE spc_definition_id=?
        """,
        (str(definition.id),),
    ).fetchone()["count"]

    assert count == 0
