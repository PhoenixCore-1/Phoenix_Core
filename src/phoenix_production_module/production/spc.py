from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from phoenix_core.errors import ValidationError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class SPCDefinition:
    id: UUID
    organisation_id: UUID
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
        code: str,
        name: str,
        created_by: UUID | None = None,
    ) -> "SPCDefinition":
        code = code.strip().upper()
        name = name.strip()

        if not code:
            raise ValidationError("SPC definition code is required")

        if not name:
            raise ValidationError("SPC definition name is required")

        now = utcnow()

        return cls(
            id=uuid4(),
            organisation_id=organisation_id,
            code=code,
            name=name,
            status="DRAFT",
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by,
        )
