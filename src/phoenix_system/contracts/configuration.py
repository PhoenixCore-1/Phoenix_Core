from dataclasses import dataclass, field
from typing import Mapping
from uuid import UUID


@dataclass(frozen=True)
class ConfigurationAdministration:
    configuration_id: UUID
    organisation_id: UUID
    key: str
    value: object
    enabled: bool = True
    can_manage_configuration: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    @property
    def active(self) -> bool:
        return self.enabled

    @property
    def administrable(self) -> bool:
        return self.can_manage_configuration

    def can_administer_configuration(self) -> bool:
        return self.can_manage_configuration
