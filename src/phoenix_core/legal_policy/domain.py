from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class PolicyStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class PolicyScope(str, Enum):
    PLATFORM = "PLATFORM"
    ORGANISATION = "ORGANISATION"


@dataclass(frozen=True)
class Policy:
    id: UUID
    organisation_id: UUID
    policy_code: str
    policy_type: str
    status: PolicyStatus
    required_acceptance: bool
    applicable_scope: PolicyScope
    created_at: datetime
    updated_at: datetime

    @property
    def active(self) -> bool:
        return self.status == PolicyStatus.ACTIVE

    @property
    def acceptance_required(self) -> bool:
        return self.required_acceptance


@dataclass(frozen=True)
class PolicyVersion:
    id: UUID
    policy_id: UUID
    version_number: int
    version_label: str
    document_id: UUID
    effective_at: datetime
    acceptance_required: bool
    status: PolicyStatus
    created_at: datetime

    @property
    def active(self) -> bool:
        return self.status == PolicyStatus.ACTIVE

    @property
    def immutable(self) -> bool:
        return True


@dataclass(frozen=True)
class PolicyAcceptance:
    id: UUID
    policy_id: UUID
    policy_version_id: UUID
    organisation_id: UUID
    identity_id: UUID
    session_id: UUID | None
    request_id: str | None
    accepted_at: datetime
    audit_event_id: UUID | None

    @property
    def historical(self) -> bool:
        return True
