"""Organisation/tenant domain model."""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from phoenix_core.errors import ValidationError

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(frozen=True)
class Organisation:
    id: UUID
    code: str
    name: str
    status: str
    created_at: datetime

    @classmethod
    def create(cls, code: str, name: str) -> "Organisation":
        code = code.strip().upper()
        name = name.strip()
        if not code:
            raise ValidationError("Organisation code is required.")
        if not name:
            raise ValidationError("Organisation name is required.")
        return cls(uuid4(), code, name, "ACTIVE", utcnow())

    def with_status(self, status: str) -> "Organisation":
        if status not in {"ACTIVE", "SUSPENDED", "CLOSED"}:
            raise ValidationError("Invalid organisation status.")
        if self.status == "CLOSED" and status != "CLOSED":
            raise ValidationError("A closed organisation cannot be reactivated.")
        if self.status == status:
            return self
        return Organisation(self.id, self.code, self.name, status, self.created_at)
