from datetime import datetime
from uuid import UUID

from phoenix_core.errors import ConflictError, NotFoundError, ValidationError

from .spc import SPCDefinition


class SPCDefinitionService:
    def __init__(self, db):
        self.db = db

    def create_definition(
        self,
        *,
        organisation_id: UUID,
        code: str,
        name: str,
        created_by: UUID | None = None,
    ) -> SPCDefinition:
        definition = SPCDefinition.create(
            organisation_id=organisation_id,
            code=code,
            name=name,
            created_by=created_by,
        )

        try:
            self.db.execute(
                """
                INSERT INTO production_spc_definitions(
                    id, organisation_id, code, name, status,
                    created_at, updated_at, created_by, updated_by
                )
                VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (
                    str(definition.id),
                    str(definition.organisation_id),
                    definition.code,
                    definition.name,
                    definition.status,
                    definition.created_at.isoformat(),
                    definition.updated_at.isoformat(),
                    str(definition.created_by) if definition.created_by else None,
                    str(definition.updated_by) if definition.updated_by else None,
                ),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if "UNIQUE constraint failed: production_spc_definitions.organisation_id, production_spc_definitions.code" in str(exc):
                raise ConflictError(
                    "SPC definition code already exists"
                ) from exc
            raise

        return definition

    def get_definition(
        self,
        *,
        organisation_id: UUID,
        definition_id: UUID,
    ) -> SPCDefinition:
        row = self.db.execute(
            """
            SELECT
                id, organisation_id, code, name, status,
                created_at, updated_at, created_by, updated_by
            FROM production_spc_definitions
            WHERE id=? AND organisation_id=?
            """,
            (str(definition_id), str(organisation_id)),
        ).fetchone()

        if row is None:
            raise NotFoundError("SPC definition not found")

        return self._row_to_definition(row)

    def activate_definition(
        self,
        *,
        organisation_id: UUID,
        definition_id: UUID,
        updated_by: UUID | None = None,
    ) -> SPCDefinition:
        current = self.get_definition(
            organisation_id=organisation_id,
            definition_id=definition_id,
        )

        if current.status != "DRAFT":
            raise ValidationError(
                f"Cannot activate SPC definition from status {current.status}"
            )

        component_count = self.db.execute(
            """
            SELECT COUNT(*) AS count
            FROM production_spc_cost_components
            WHERE spc_definition_id=?
            """,
            (str(definition_id),),
        ).fetchone()["count"]

        if component_count == 0:
            raise ValidationError(
                "SPC definition must have at least one cost component before activation"
            )

        now = datetime.now(current.created_at.tzinfo)

        self.db.execute(
            """
            UPDATE production_spc_definitions
            SET status='ACTIVE',
                updated_at=?,
                updated_by=?
            WHERE id=? AND organisation_id=?
            """,
            (
                now.isoformat(),
                str(updated_by) if updated_by else None,
                str(definition_id),
                str(organisation_id),
            ),
        )
        self.db.commit()

        return self.get_definition(
            organisation_id=organisation_id,
            definition_id=definition_id,
        )

    def retire_definition(
        self,
        *,
        organisation_id: UUID,
        definition_id: UUID,
        updated_by: UUID | None = None,
    ) -> SPCDefinition:
        current = self.get_definition(
            organisation_id=organisation_id,
            definition_id=definition_id,
        )

        if current.status != "ACTIVE":
            raise ValidationError(
                f"Cannot retire SPC definition from status {current.status}"
            )

        now = datetime.now(current.created_at.tzinfo)

        self.db.execute(
            """
            UPDATE production_spc_definitions
            SET status='RETIRED',
                updated_at=?,
                updated_by=?
            WHERE id=? AND organisation_id=?
            """,
            (
                now.isoformat(),
                str(updated_by) if updated_by else None,
                str(definition_id),
                str(organisation_id),
            ),
        )
        self.db.commit()

        return self.get_definition(
            organisation_id=organisation_id,
            definition_id=definition_id,
        )

    @staticmethod
    def _row_to_definition(row) -> SPCDefinition:
        return SPCDefinition(
            id=UUID(row["id"]),
            organisation_id=UUID(row["organisation_id"]),
            code=row["code"],
            name=row["name"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            created_by=UUID(row["created_by"]) if row["created_by"] else None,
            updated_by=UUID(row["updated_by"]) if row["updated_by"] else None,
        )
