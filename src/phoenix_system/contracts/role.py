from dataclasses import dataclass, field
from typing import FrozenSet, Mapping
from uuid import UUID


@dataclass(frozen=True)
class RoleAdministration:
    role_id: UUID
    organisation_id: UUID
    name: str
    permissions: FrozenSet[str] = frozenset()
    can_manage_role: bool = False
    can_assign_role: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    @property
    def administrable(self) -> bool:
        return self.can_manage_role

    @property
    def assignable(self) -> bool:
        return self.can_assign_role

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def can_administer_role(self) -> bool:
        return self.can_manage_role or self.can_assign_role
