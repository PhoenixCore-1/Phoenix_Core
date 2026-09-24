from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from phoenix_core.errors import ValidationError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class BOMComponent:
    id: UUID
    bom_version_id: UUID
    component_product_id: UUID
    quantity: Decimal
    uom: str
    sequence: int

    @classmethod
    def create(
        cls,
        *,
        bom_version_id: UUID,
        component_product_id: UUID,
        quantity: Decimal,
        uom: str,
        sequence: int,
    ) -> "BOMComponent":
        quantity = Decimal(str(quantity))
        uom = uom.strip()

        if quantity <= 0:
            raise ValidationError(
                "BOM component quantity must be greater than zero."
            )

        if not uom:
            raise ValidationError(
                "BOM component UOM is required."
            )

        if sequence < 1:
            raise ValidationError(
                "BOM component sequence must be greater than zero."
            )

        return cls(
            id=uuid4(),
            bom_version_id=bom_version_id,
            component_product_id=component_product_id,
            quantity=quantity,
            uom=uom,
            sequence=sequence,
        )


@dataclass(frozen=True)
class BOMVersion:
    id: UUID
    bom_id: UUID
    version_number: int
    status: str
    created_at: datetime
    published_at: datetime | None = None
    spc_definition_id: UUID | None = None

    @classmethod
    def create(
        cls,
        *,
        bom_id: UUID,
        version_number: int,
        spc_definition_id: UUID | None = None,
    ) -> "BOMVersion":
        if version_number < 1:
            raise ValidationError(
                "BOM version number must be greater than zero."
            )

        return cls(
            id=uuid4(),
            bom_id=bom_id,
            version_number=version_number,
            status="DRAFT",
            created_at=utcnow(),
        )

    def publish(self, published_at: datetime | None = None) -> "BOMVersion":
        if self.status != "DRAFT":
            raise ValidationError(
                "Only a draft BOM version can be published."
            )

        return BOMVersion(
            id=self.id,
            bom_id=self.bom_id,
            version_number=self.version_number,
            status="PUBLISHED",
            created_at=self.created_at,
            published_at=published_at or utcnow(),
        )


@dataclass(frozen=True)
class BOM:
    id: UUID
    organisation_id: UUID
    product_id: UUID
    code: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    updated_by: UUID | None = None

    @classmethod
    def create(
        cls,
        *,
        organisation_id: UUID,
        product_id: UUID,
        code: str,
        name: str,
        created_by: UUID | None = None,
    ) -> "BOM":
        code = code.strip().upper()
        name = name.strip()

        if not code:
            raise ValidationError("BOM code is required.")

        if not name:
            raise ValidationError("BOM name is required.")

        now = utcnow()

        return cls(
            id=uuid4(),
            organisation_id=organisation_id,
            product_id=product_id,
            code=code,
            name=name,
            status="DRAFT",
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by,
        )





