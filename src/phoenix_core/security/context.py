"""Authoritative request security context."""

from dataclasses import dataclass
from typing import FrozenSet, Optional
from uuid import UUID

@dataclass(frozen=True)
class RequestContext:
    request_id: str
    identity_id: Optional[UUID] = None
    organisation_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    permissions: FrozenSet[str] = frozenset()
    entitlements: FrozenSet[str] = frozenset()

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def has_entitlement(self, module_code: str) -> bool:
        return module_code in self.entitlements
