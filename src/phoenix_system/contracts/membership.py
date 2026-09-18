from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping
from uuid import UUID


class MembershipStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


@dataclass(frozen=True)
class MembershipAdministration:
    membership_id: UUID
    identity_id: UUID
    organisation_id: UUID
    status: MembershipStatus
    can_manage_membership: bool = False
    can_assign_roles: bool = False
    can_manage_module_access: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    @property
    def active(self) -> bool:
        return self.status == MembershipStatus.ACTIVE

    @property
    def administrable(self) -> bool:
        return self.active

    def can_administer_membership(self) -> bool:
        return (
            self.can_manage_membership
            or self.can_assign_roles
            or self.can_manage_module_access
        )
