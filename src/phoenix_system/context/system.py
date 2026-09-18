from dataclasses import dataclass
from typing import FrozenSet
from uuid import UUID

from phoenix_framework.context import FrameworkContext


@dataclass(frozen=True)
class SystemContext:
    """
    Administrative context for Phoenix System.

    This is derived from the authoritative Core/Framework context.
    It does not create a separate identity, tenant, permission, or
    entitlement authority.
    """

    request_id: str
    identity_id: UUID
    organisation_id: UUID
    session_id: UUID | None
    permissions: FrozenSet[str]
    entitlements: FrozenSet[str]

    @classmethod
    def from_framework(
        cls,
        context: FrameworkContext,
    ) -> "SystemContext":
        context.require_authenticated()
        context.require_tenant()

        return cls(
            request_id=context.request_id,
            identity_id=context.identity_id,
            organisation_id=context.organisation_id,
            session_id=context.session_id,
            permissions=context.permissions,
            entitlements=context.entitlements,
        )

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def has_entitlement(self, entitlement: str) -> bool:
        return entitlement in self.entitlements

    def require_permission(self, permission: str) -> None:
        if not self.has_permission(permission):
            raise PermissionError(
                f"System permission required: {permission}"
            )

    def require_entitlement(self, entitlement: str) -> None:
        if not self.has_entitlement(entitlement):
            raise PermissionError(
                f"System entitlement required: {entitlement}"
            )
