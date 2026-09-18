from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Optional, Sequence, Tuple


class ModuleLifecycle(str, Enum):
    """Generic module lifecycle state."""

    REGISTERED = "registered"
    ENABLED = "enabled"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"


@dataclass(frozen=True)
class ModuleContract:
    """
    Generic contract describing a Phoenix module.

    Module authority remains with Phoenix Core. This contract describes
    how a module integrates with the Generic Framework.
    """

    code: str
    name: str
    version: str
    lifecycle: ModuleLifecycle = ModuleLifecycle.REGISTERED
    description: str = ""
    required_permissions: Tuple[str, ...] = ()
    required_entitlements: Tuple[str, ...] = ()
    navigation_keys: Tuple[str, ...] = ()
    capabilities: Tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("Module code cannot be empty")

        if not self.name.strip():
            raise ValueError("Module name cannot be empty")

        if not self.version.strip():
            raise ValueError("Module version cannot be empty")

    @property
    def enabled(self) -> bool:
        return self.lifecycle == ModuleLifecycle.ENABLED

    def requires_permission(self, permission: str) -> bool:
        return permission in self.required_permissions

    def requires_entitlement(self, entitlement: str) -> bool:
        return entitlement in self.required_entitlements

    def exposes_navigation(self, navigation_key: str) -> bool:
        return navigation_key in self.navigation_keys

    def exposes_capability(self, capability: str) -> bool:
        return capability in self.capabilities
