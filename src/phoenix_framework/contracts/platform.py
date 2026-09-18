from dataclasses import dataclass, field
from typing import FrozenSet, Mapping, Optional
from uuid import UUID


@dataclass(frozen=True)
class CompanyContext:
    """Authoritative company/tenant context supplied by Phoenix Core."""

    organisation_id: UUID
    name: str
    active: bool = True


@dataclass(frozen=True)
class UserContext:
    """Authenticated user context supplied by Phoenix Core."""

    identity_id: UUID
    username: str
    display_name: str
    organisation_id: UUID
    permissions: FrozenSet[str] = frozenset()
    entitlements: FrozenSet[str] = frozenset()

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def has_entitlement(self, entitlement: str) -> bool:
        return entitlement in self.entitlements


@dataclass(frozen=True)
class ModuleDescriptor:
    """Generic presentation metadata for a registered Phoenix module."""

    code: str
    name: str
    version: str
    enabled: bool = True
    navigation_label: Optional[str] = None
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class NavigationItem:
    """Generic navigation registration supplied by a module or platform feature."""

    key: str
    label: str
    route: str
    icon: Optional[str] = None
    module_code: Optional[str] = None
    permission: Optional[str] = None
    entitlement: Optional[str] = None
    order: int = 0


@dataclass(frozen=True)
class PlatformCapability:
    """Generic capability exposed by the Phoenix platform."""

    code: str
    name: str
    description: str
    enabled: bool = True
    metadata: Mapping[str, str] = field(default_factory=dict)
