"""Authenticated session domain model."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(frozen=True)
class Session:
    id: UUID
    identity_id: UUID
    token_hash: str
    expires_at: datetime
    status: str
    created_at: datetime

    @classmethod
    def create(cls, identity_id: UUID, token_hash: str, lifetime_minutes: int = 60) -> "Session":
        now = utcnow()
        return cls(uuid4(), identity_id, token_hash, now + timedelta(minutes=lifetime_minutes), "ACTIVE", now)
