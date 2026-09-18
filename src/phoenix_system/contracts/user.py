from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping
from uuid import UUID


class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISABLED = "disabled"


@dataclass(frozen=True)
class UserAdministration:
    identity_id: UUID
    organisation_id: UUID
    status: UserStatus
    can_manage_profile: bool = False
    can_manage_memberships: bool = False
    can_manage_roles: bool = False
    can_manage_module_access: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    @property
    def active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    @property
    def administrable(self) -> bool:
        return self.active

    def can_administer_users(self) -> bool:
        return (
            self.can_manage_profile
            or self.can_manage_memberships
            or self.can_manage_roles
            or self.can_manage_module_access
        )
