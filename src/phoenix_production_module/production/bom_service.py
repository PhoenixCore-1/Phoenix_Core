from datetime import datetime, timezone
from uuid import UUID

from phoenix_core.errors import ConflictError, NotFoundError

from .bom import BOM


class BOMService:
    """Production BOM application and persistence service."""

    def __init__(self, db):
        self.db = db

    def create_bom(
        self,
        *,
        organisation_id: UUID,
        product_id: UUID,
        code: str,
        name: str,
        created_by: UUID | None = None,
    ) -> BOM:
        product = self.db.execute(
            """
            SELECT id
            FROM production_products
            WHERE id=?
              AND organisation_id=?
              AND status='ACTIVE'
            """,
            (
                str(product_id),
                str(organisation_id),
            ),
        ).fetchone()

        if product is None:
            raise NotFoundError(
                "Active production product not found."
            )

        bom = BOM.create(
            organisation_id=organisation_id,
            product_id=product_id,
            code=code,
            name=name,
            created_by=created_by,
        )

        try:
            self.db.execute(
                """
                INSERT INTO production_boms(
                    id,
                    organisation_id,
                    product_id,
                    code,
                    name,
                    status,
                    created_at,
                    updated_at,
                    created_by,
                    updated_by
                )
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    str(bom.id),
                    str(bom.organisation_id),
                    str(bom.product_id),
                    bom.code,
                    bom.name,
                    bom.status,
                    bom.created_at.isoformat(),
                    bom.updated_at.isoformat(),
                    str(bom.created_by) if bom.created_by else None,
                    str(bom.updated_by) if bom.updated_by else None,
                ),
            )
            self.db.commit()

        except Exception as exc:
            self.db.rollback()

            if "UNIQUE" in str(exc).upper():
                raise ConflictError(
                    "A BOM with this code already exists for the organisation."
                ) from exc

            raise

        return bom

    def get_bom(
        self,
        *,
        organisation_id: UUID,
        bom_id: UUID,
    ) -> BOM:
        row = self.db.execute(
            """
            SELECT
                id,
                organisation_id,
                product_id,
                code,
                name,
                status,
                created_at,
                updated_at,
                created_by,
                updated_by
            FROM production_boms
            WHERE id=?
              AND organisation_id=?
            """,
            (
                str(bom_id),
                str(organisation_id),
            ),
        ).fetchone()

        if row is None:
            raise NotFoundError("BOM not found.")

        return BOM(
            id=UUID(row["id"]),
            organisation_id=UUID(row["organisation_id"]),
            product_id=UUID(row["product_id"]),
            code=row["code"],
            name=row["name"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            created_by=(
                UUID(row["created_by"])
                if row["created_by"]
                else None
            ),
            updated_by=(
                UUID(row["updated_by"])
                if row["updated_by"]
                else None
            ),
        )
