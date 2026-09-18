"""Role domain model."""
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4
from phoenix_core.errors import ValidationError

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(frozen=True)
class Role:
    id: UUID
    organisation_id: UUID
    code: str
    name: str
    scope: str
    status: str
    created_at: datetime

    @classmethod
    def create(cls, organisation_id: UUID, code: str, name: str, scope: str = "ORGANISATION") -> "Role":
        code = code.strip().upper()
        name = name.strip()
        if not code or not name:
            raise ValidationError("Role code and name are required.")
        if scope not in {"SYSTEM", "ORGANISATION"}:
            raise ValidationError("Invalid role scope.")
        if scope == "SYSTEM":
            raise ValidationError("System roles are reserved for Phoenix System administration.")
        return cls(uuid4(), organisation_id, code, name, scope, "ACTIVE", utcnow())

    def with_status(self, status: str) -> "Role":
        if status not in {"ACTIVE", "DISABLED"}:
            raise ValidationError("Invalid role status.")
        if self.status == status:
            return self
        return Role(self.id, self.organisation_id, self.code, self.name, self.scope, status, self.created_at)

    def with_details(self, *, code: str | None = None, name: str | None = None) -> "Role":
        new_code = self.code if code is None else code.strip().upper()
        new_name = self.name if name is None else name.strip()
        if not new_code or not new_name:
            raise ValidationError("Role code and name are required.")
        return Role(self.id, self.organisation_id, new_code, new_name, self.scope, self.status, self.created_at)
