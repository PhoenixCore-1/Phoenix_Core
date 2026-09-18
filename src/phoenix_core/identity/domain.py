"""Identity domain model."""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from phoenix_core.errors import ValidationError

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(frozen=True)
class Identity:
    id: UUID
    identity_type: str
    status: str
    created_at: datetime

    @classmethod
    def create(cls, identity_type: str = "HUMAN") -> "Identity":
        if identity_type not in {"HUMAN", "SERVICE", "INTEGRATION"}:
            raise ValidationError("Unsupported identity type.")
        return cls(uuid4(), identity_type, "ACTIVE", utcnow())
