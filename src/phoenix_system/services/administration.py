from dataclasses import dataclass

from phoenix_system.context.system import SystemContext


@dataclass(frozen=True)
class SystemAdministrationService:
    context: SystemContext

    def require_administration_access(self) -> None:
        if self.context.identity_id is None:
            raise PermissionError("Authenticated identity is required")

        if self.context.organisation_id is None:
            raise PermissionError("Organisation context is required")

    def can_manage_company(self) -> bool:
        return self.context.has_permission("system.company.manage")

    def can_manage_users(self) -> bool:
        return self.context.has_permission("system.users.manage")

    def can_manage_memberships(self) -> bool:
        return self.context.has_permission("system.memberships.manage")

    def can_manage_roles(self) -> bool:
        return self.context.has_permission("system.roles.manage")

    def can_manage_modules(self) -> bool:
        return self.context.has_permission("system.modules.manage")

    def can_manage_entitlements(self) -> bool:
        return self.context.has_permission("system.entitlements.manage")

    def can_manage_configuration(self) -> bool:
        return self.context.has_permission("system.configuration.manage")

    def can_manage_platform(self) -> bool:
        return self.context.has_permission("system.platform.manage")
