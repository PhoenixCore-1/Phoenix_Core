from decimal import Decimal
from uuid import UUID

from phoenix_core.errors import ConflictError, NotFoundError, ValidationError

from .bom import BOMComponent


class BOMComponentService:
    """Production BOM component persistence service."""

    def __init__(self, db):
        self.db = db

    def add_component(
        self,
        *,
        organisation_id: UUID,
        bom_version_id: UUID,
        component_product_id: UUID,
        quantity: Decimal,
        uom: str,
        sequence: int,
    ) -> BOMComponent:
        version = self.db.execute(
            """
            SELECT v.id, v.status
            FROM production_bom_versions v
            JOIN production_boms b ON b.id=v.bom_id
            WHERE v.id=?
              AND b.organisation_id=?
            """,
            (
                str(bom_version_id),
                str(organisation_id),
            ),
        ).fetchone()

        if version is None:
            raise NotFoundError("BOM version not found.")

        if version["status"] != "DRAFT":
            raise ValidationError(
                "Published or retired BOM versions cannot be modified."
            )

        product = self.db.execute(
            """
            SELECT id
            FROM production_products
            WHERE id=?
              AND organisation_id=?
              AND status='ACTIVE'
            """,
            (
                str(component_product_id),
                str(organisation_id),
            ),
        ).fetchone()

        if product is None:
            raise NotFoundError(
                "Active component product not found."
            )

        component = BOMComponent.create(
            bom_version_id=bom_version_id,
            component_product_id=component_product_id,
            quantity=quantity,
            uom=uom,
            sequence=sequence,
        )

        try:
            self.db.execute(
                """
                INSERT INTO production_bom_components(
                    id,
                    bom_version_id,
                    component_product_id,
                    quantity,
                    uom,
                    sequence,
                    created_at
                )
                VALUES (?,?,?,?,?,?,?)
                """,
                (
                    str(component.id),
                    str(component.bom_version_id),
                    str(component.component_product_id),
                    float(component.quantity),
                    component.uom,
                    component.sequence,
                    __import__("datetime").datetime.now(
                        __import__("datetime").timezone.utc
                    ).isoformat(),
                ),
            )
            self.db.commit()

        except Exception as exc:
            self.db.rollback()

            if "UNIQUE" in str(exc).upper():
                raise ConflictError(
                    "A BOM component already exists at this sequence."
                ) from exc

            raise

        return component
