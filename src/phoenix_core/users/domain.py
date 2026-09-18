"""User domain model."""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from phoenix_core.errors import ValidationError

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(frozen=True)
class User:
    id: UUID
    identity_id: UUID
    username: str
    display_name: str
    password_hash: str
    status: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        identity_id: UUID,
        username: str,
        display_name: str,
        password_hash: str,
    ) -> "User":
        username = username.strip()
        display_name = display_name.strip()
        if not username:
            raise ValidationError("Username is required.")
        if not display_name:
            raise ValidationError("Display name is required.")
        return cls(uuid4(), identity_id, username, display_name, password_hash, "ACTIVE", utcnow())
