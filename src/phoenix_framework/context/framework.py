from dataclasses import dataclass
from typing import FrozenSet, Optional
from uuid import UUID

from phoenix_core.security.context import RequestContext


@dataclass(frozen=True)
class FrameworkContext:
    """
    Application-facing context for the Phoenix Generic Framework.

    Core RequestContext remains the authoritative security context.
    FrameworkContext is an immutable projection for Framework consumers.
    """

    request_id: str
    identity_id: Optional[UUID]
    organisation_id: Optional[UUID]
    session_id: Optional[UUID]
    permissions: FrozenSet[str]
    entitlements: FrozenSet[str]

    @classmethod
    def from_core(cls, context: RequestContext) -> "FrameworkContext":
        """Create a Framework context from the authoritative Core context."""
        return cls(
            request_id=context.request_id,
            identity_id=context.identity_id,
            organisation_id=context.organisation_id,
            session_id=context.session_id,
            permissions=context.permissions,
            entitlements=context.entitlements,
        )

    @property
    def authenticated(self) -> bool:
        return self.identity_id is not None

    @property
    def tenant_bound(self) -> bool:
        return self.organisation_id is not None

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def has_entitlement(self, entitlement: str) -> bool:
        return entitlement in self.entitlements

    def require_authenticated(self) -> None:
        if not self.authenticated:
            raise PermissionError("Authenticated identity is required")

    def require_tenant(self) -> None:
        if not self.tenant_bound:
            raise PermissionError("Organisation context is required")
