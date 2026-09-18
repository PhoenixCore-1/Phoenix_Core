"""Phoenix module registry domain model."""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from phoenix_core.errors import ValidationError

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(frozen=True)
class Module:
    id: UUID
    code: str
    name: str
    version: str
    status: str
    created_at: datetime

    @classmethod
    def create(cls, code: str, name: str, version: str) -> "Module":
        code = code.strip().lower()
        name = name.strip()
        if not code or not name or not version:
            raise ValidationError("Module code, name and version are required.")
        return cls(uuid4(), code, name, version, "REGISTERED", utcnow())
