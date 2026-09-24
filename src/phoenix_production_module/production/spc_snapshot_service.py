from datetime import datetime, timezone
from uuid import UUID, uuid4

from phoenix_core.errors import ConflictError, NotFoundError, ValidationError


class SPCSnapshotService:
    def __init__(self, db):
        self.db = db

    def create_snapshot(
        self,
        *,
        organisation_id: UUID,
        production_order_id: int,
        spc_definition_id: UUID,
    ) -> UUID:
        definition = self.db.execute(
            """
            SELECT id, code, name, status
            FROM production_spc_definitions
            WHERE id=? AND organisation_id=?
            """,
            (str(spc_definition_id), str(organisation_id)),
        ).fetchone()

        if definition is None:
            raise NotFoundError("SPC definition not found")

        if definition["status"] != "ACTIVE":
            raise ValidationError(
                "Only an ACTIVE SPC definition can be snapshotted"
            )

        order = self.db.execute(
            """
            SELECT production_order_id
            FROM production_orders
            WHERE production_order_id=? AND organisation_id=?
            """,
            (production_order_id, str(organisation_id)),
        ).fetchone()

        if order is None:
            raise NotFoundError("Production order not found")

        existing = self.db.execute(
            """
            SELECT id
            FROM production_order_spc_snapshots
            WHERE production_order_id=?
            """,
            (production_order_id,),
        ).fetchone()

        if existing is not None:
            raise ConflictError(
                "Production order already has an SPC snapshot"
            )

        components = self.db.execute(
            """
            SELECT code, name, cost, currency, sequence
            FROM production_spc_cost_components
            WHERE spc_definition_id=?
            ORDER BY sequence
            """,
            (str(spc_definition_id),),
        ).fetchall()

        if not components:
            raise ValidationError(
                "ACTIVE SPC definition has no cost components"
            )

        snapshot_id = uuid4()
        created_at = datetime.now(timezone.utc).isoformat()

        try:
            self.db.execute(
                """
                INSERT INTO production_order_spc_snapshots(
                    id,
                    production_order_id,
                    organisation_id,
                    spc_definition_id,
                    code,
                    name,
                    created_at
                )
                VALUES (?,?,?,?,?,?,?)
                """,
                (
                    str(snapshot_id),
                    production_order_id,
                    str(organisation_id),
                    str(spc_definition_id),
                    definition["code"],
                    definition["name"],
                    created_at,
                ),
            )

            for component in components:
                self.db.execute(
                    """
                    INSERT INTO production_order_spc_snapshot_components(
                        id,
                        snapshot_id,
                        code,
                        name,
                        cost,
                        currency,
                        sequence
                    )
                    VALUES (?,?,?,?,?,?,?)
                    """,
                    (
                        str(uuid4()),
                        str(snapshot_id),
                        component["code"],
                        component["name"],
                        component["cost"],
                        component["currency"],
                        component["sequence"],
                    ),
                )

            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return snapshot_id
