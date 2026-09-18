"""Organisation membership domain model."""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from phoenix_core.errors import ValidationError

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(frozen=True)
class Membership:
    id: UUID
    identity_id: UUID
    organisation_id: UUID
    status: str
    created_at: datetime

    @classmethod
    def create(cls, identity_id: UUID, organisation_id: UUID) -> "Membership":
        if not identity_id or not organisation_id:
            raise ValidationError("Identity and organisation are required.")
        return cls(uuid4(), identity_id, organisation_id, "ACTIVE", utcnow())

    def with_status(self, status: str) -> "Membership":
        if status not in {"ACTIVE", "SUSPENDED", "REMOVED"}:
            raise ValidationError("Invalid membership status.")
        if self.status == "REMOVED" and status != "REMOVED":
            raise ValidationError("A removed membership cannot be restored; create a new membership instead.")
        return Membership(self.id, self.identity_id, self.organisation_id, status, self.created_at)
