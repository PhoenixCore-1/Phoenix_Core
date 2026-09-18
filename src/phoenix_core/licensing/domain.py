"""Technical module entitlement domain model."""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from phoenix_core.errors import ValidationError

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(frozen=True)
class Entitlement:
    id: UUID
    organisation_id: UUID
    module_id: UUID
    status: str
    created_at: datetime

    @classmethod
    def grant(cls, organisation_id: UUID, module_id: UUID) -> "Entitlement":
        if not organisation_id or not module_id:
            raise ValidationError("Organisation and module are required.")
        return cls(uuid4(), organisation_id, module_id, "ACTIVE", utcnow())
