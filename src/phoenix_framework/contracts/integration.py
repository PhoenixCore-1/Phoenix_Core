"""Phoenix module integration contracts."""

from dataclasses import dataclass, field
from typing import Mapping, Tuple


@dataclass(frozen=True)
class ModuleDependency:
    """Declares a dependency on another Phoenix module."""

    module_code: str
    minimum_version: str = ""
    maximum_version: str = ""
    required: bool = True
    capabilities: Tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.module_code.strip():
            raise ValueError("Dependency module_code cannot be empty")

        if self.minimum_version and not self.minimum_version.strip():
            raise ValueError("Dependency minimum_version cannot be blank")

        if self.maximum_version and not self.maximum_version.strip():
            raise ValueError("Dependency maximum_version cannot be blank")

    def requires_capability(self, capability: str) -> bool:
        return capability in self.capabilities


@dataclass(frozen=True)
class ModuleIntegrationContract:
    """
    Declares the integration surface of a Phoenix module.

    This contract describes dependencies and published integration
    capabilities. It does not own module business data or Core authority.
    """

    module_code: str
    version: str
    provided_contracts: Tuple[str, ...] = ()
    provided_capabilities: Tuple[str, ...] = ()
    provided_events: Tuple[str, ...] = ()
    dependencies: Tuple[ModuleDependency, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.module_code.strip():
            raise ValueError("Integration module_code cannot be empty")

        if not self.version.strip():
            raise ValueError("Integration version cannot be empty")

    def provides_contract(self, contract: str) -> bool:
        return contract in self.provided_contracts

    def provides_capability(self, capability: str) -> bool:
        return capability in self.provided_capabilities

    def provides_event(self, event_type: str) -> bool:
        return event_type in self.provided_events

    def depends_on(self, module_code: str) -> bool:
        return any(
            dependency.module_code == module_code
            for dependency in self.dependencies
        )
