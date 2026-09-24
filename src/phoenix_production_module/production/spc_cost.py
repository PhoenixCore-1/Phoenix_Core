from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

from phoenix_core.errors import ValidationError


@dataclass(frozen=True)
class SPCCostComponent:
    id: UUID
    spc_definition_id: UUID
    code: str
    name: str
    cost: Decimal
    currency: str
    sequence: int

    @classmethod
    def create(
        cls,
        *,
        spc_definition_id: UUID,
        code: str,
        name: str,
        cost,
        currency: str,
        sequence: int,
    ) -> "SPCCostComponent":
        code = code.strip().upper()
        name = name.strip()
        currency = currency.strip().upper()
        cost = Decimal(str(cost))

        if not code:
            raise ValidationError("SPC cost component code is required")
        if not name:
            raise ValidationError("SPC cost component name is required")
        if cost < 0:
            raise ValidationError("SPC cost cannot be negative")
        if not currency:
            raise ValidationError("Currency is required")
        if sequence < 1:
            raise ValidationError("Sequence must be >= 1")

        return cls(
            id=uuid4(),
            spc_definition_id=spc_definition_id,
            code=code,
            name=name,
            cost=cost,
            currency=currency,
            sequence=sequence,
        )
