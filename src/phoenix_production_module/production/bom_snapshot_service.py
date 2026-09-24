from uuid import UUID

from phoenix_core.errors import NotFoundError, ValidationError


class BOMSnapshotService:
    def __init__(self, db):
        self.db = db

    def validate_releasable_version(
        self,
        *,
        organisation_id: UUID,
        bom_version_id: UUID,
        product_ref: str,
    ) -> None:
        row = self.db.execute(
            """
            SELECT
                bv.id,
                bv.status,
                b.organisation_id,
                p.code AS product_code
            FROM production_bom_versions bv
            JOIN production_boms b
              ON b.id = bv.bom_id
            JOIN production_products p
              ON p.id = b.product_id
            WHERE bv.id=?
              AND b.organisation_id=?
            """,
            (str(bom_version_id), str(organisation_id)),
        ).fetchone()

        if row is None:
            raise NotFoundError("BOM version not found")

        if row["status"] != "PUBLISHED":
            raise ValidationError(
                "Only a PUBLISHED BOM version can be released"
            )

        if row["product_code"] != product_ref:
            raise ValidationError(
                "BOM product does not match production order product"
            )

    def get_components(
        self,
        *,
        organisation_id: UUID,
        bom_version_id: UUID,
    ) -> list[dict]:
        rows = self.db.execute(
            """
            SELECT
                bc.component_product_id,
                p.code AS component_product_code,
                bc.quantity,
                bc.uom,
                bc.sequence
            FROM production_bom_components bc
            JOIN production_bom_versions bv
              ON bv.id = bc.bom_version_id
            JOIN production_boms b
              ON b.id = bv.bom_id
            JOIN production_products p
              ON p.id = bc.component_product_id
            WHERE bv.id=?
              AND b.organisation_id=?
            ORDER BY bc.sequence
            """,
            (str(bom_version_id), str(organisation_id)),
        ).fetchall()

        return [dict(row) for row in rows]
