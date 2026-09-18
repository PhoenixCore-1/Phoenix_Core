"""Permission domain model."""
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4
from phoenix_core.errors import ValidationError

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(frozen=True)
class Permission:
    id: UUID
    code: str
    name: str
    created_at: datetime

    @classmethod
    def create(cls, code: str, name: str) -> "Permission":
        code = code.strip().lower()
        name = name.strip()
        if not code or not name:
            raise ValidationError("Permission code and name are required.")
        if any(ch.isspace() for ch in code):
            raise ValidationError("Permission code cannot contain whitespace.")
        return cls(uuid4(), code, name, utcnow())

    def with_details(self, *, code: str | None = None, name: str | None = None) -> "Permission":
        new_code = self.code if code is None else code.strip().lower()
        new_name = self.name if name is None else name.strip()
        if not new_code or not new_name:
            raise ValidationError("Permission code and name are required.")
        if any(ch.isspace() for ch in new_code):
            raise ValidationError("Permission code cannot contain whitespace.")
        return Permission(self.id, new_code, new_name, self.created_at)
