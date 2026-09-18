from dataclasses import dataclass, field
from typing import Mapping
from uuid import UUID


@dataclass(frozen=True)
class EntitlementAdministration:
    entitlement_id: UUID
    organisation_id: UUID
    key: str
    enabled: bool = False
    can_manage_entitlement: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    @property
    def active(self) -> bool:
        return self.enabled

    @property
    def administrable(self) -> bool:
        return self.can_manage_entitlement

    def can_administer_entitlement(self) -> bool:
        return self.can_manage_entitlement
