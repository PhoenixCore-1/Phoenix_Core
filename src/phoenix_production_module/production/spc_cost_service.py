from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from phoenix_core.errors import ConflictError, NotFoundError, ValidationError

from .spc_cost import SPCCostComponent


class SPCCostComponentService:
    def __init__(self, db):
        self.db = db

    def add_component(
        self,
        *,
        organisation_id: UUID,
        spc_definition_id: UUID,
        code: str,
        name: str,
        cost,
        currency: str,
        sequence: int,
    ) -> SPCCostComponent:
        definition = self.db.execute(
            """
            SELECT id, status
            FROM production_spc_definitions
            WHERE id=? AND organisation_id=?
            """,
            (str(spc_definition_id), str(organisation_id)),
        ).fetchone()

        if definition is None:
            raise NotFoundError("SPC definition not found")

        if definition["status"] != "DRAFT":
            raise ValidationError(
                "Cannot add cost components to an active or inactive SPC definition"
            )

        component = SPCCostComponent.create(
            spc_definition_id=spc_definition_id,
            code=code,
            name=name,
            cost=cost,
            currency=currency,
            sequence=sequence,
        )

        try:
            self.db.execute(
                """
                INSERT INTO production_spc_cost_components(
                    id, spc_definition_id, code, name,
                    cost, currency, sequence, created_at
                )
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    str(component.id),
                    str(component.spc_definition_id),
                    component.code,
                    component.name,
                    float(component.cost),
                    component.currency,
                    component.sequence,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            message = str(exc)
            if (
                "UNIQUE constraint failed: "
                "production_spc_cost_components.spc_definition_id, "
                "production_spc_cost_components.code"
            ) in message or (
                "UNIQUE constraint failed: "
                "production_spc_cost_components.spc_definition_id, "
                "production_spc_cost_components.sequence"
            ) in message:
                raise ConflictError(
                    "SPC cost component code or sequence already exists"
                ) from exc
            raise

        return component
