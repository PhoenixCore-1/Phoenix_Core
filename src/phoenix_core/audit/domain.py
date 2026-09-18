"""Audit event domain model."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

@dataclass(frozen=True)
class AuditEvent:
    id: UUID
    organisation_id: Optional[UUID]
    identity_id: Optional[UUID]
    action: str
    target_type: Optional[str]
    target_id: Optional[UUID]
    request_id: Optional[str]
    created_at: datetime

    @classmethod
    def create(cls, action: str, organisation_id=None, identity_id=None,
               target_type=None, target_id=None, request_id=None) -> "AuditEvent":
        return cls(uuid4(), organisation_id, identity_id, action, target_type, target_id, request_id, utcnow())
