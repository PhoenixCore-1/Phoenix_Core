from dataclasses import dataclass, field
from typing import Mapping
from uuid import UUID


@dataclass(frozen=True)
class PlatformAdministration:
    administration_id: UUID
    organisation_id: UUID
    capability: str
    enabled: bool = False
    available: bool = True
    can_manage_platform: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    @property
    def active(self) -> bool:
        return self.enabled and self.available

    @property
    def administrable(self) -> bool:
        return self.can_manage_platform

    def can_administer_platform(self) -> bool:
        return self.can_manage_platform
