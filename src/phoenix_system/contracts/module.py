from dataclasses import dataclass, field
from typing import Mapping
from uuid import UUID


@dataclass(frozen=True)
class ModuleAdministration:
    module_code: str
    name: str
    version: str
    organisation_id: UUID
    enabled: bool = False
    entitled: bool = False
    can_manage_module: bool = False
    can_manage_configuration: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    @property
    def active(self) -> bool:
        return self.enabled and self.entitled

    @property
    def administrable(self) -> bool:
        return self.can_manage_module

    @property
    def configurable(self) -> bool:
        return self.can_manage_configuration

    def can_administer_module(self) -> bool:
        return self.can_manage_module or self.can_manage_configuration
