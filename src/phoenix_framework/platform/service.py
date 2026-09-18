from typing import List

from phoenix_framework.context import FrameworkContext
from phoenix_framework.contracts import ModuleContract, NavigationContract
from phoenix_framework.contracts.capability import PlatformCapabilityContract
from phoenix_framework.modules import ModuleRegistry
from phoenix_framework.navigation import NavigationRegistry
from phoenix_framework.platform import CapabilityRegistry


class FrameworkService:
    """
    Generic Phoenix Framework orchestration boundary.

    Core remains authoritative for identity, tenant context, permissions,
    entitlements, licensing, and security. This service only consumes the
    Core-derived FrameworkContext and registered Framework contracts.
    """

    def __init__(
        self,
        module_registry: ModuleRegistry,
        navigation_registry: NavigationRegistry,
        capability_registry: CapabilityRegistry,
    ) -> None:
        self.module_registry = module_registry
        self.navigation_registry = navigation_registry
        self.capability_registry = capability_registry

    def get_modules(self, context: FrameworkContext) -> List[ModuleContract]:
        """Return modules visible to the current Framework context."""
        context.require_authenticated()
        context.require_tenant()

        return [
            module
            for module in self.module_registry.list()
            if module.enabled
            and self._module_authorized(module, context)
        ]

    def get_navigation(
        self,
        context: FrameworkContext,
    ) -> List[NavigationContract]:
        """Return navigation items visible to the current context."""
        context.require_authenticated()
        context.require_tenant()

        return [
            item
            for item in self.navigation_registry.list()
            if item.enabled
            and self._navigation_authorized(item, context)
        ]

    def get_capabilities(
        self,
        context: FrameworkContext,
    ) -> List[PlatformCapabilityContract]:
        """Return platform capabilities available to the current context."""
        context.require_authenticated()
        context.require_tenant()

        return [
            capability
            for capability in self.capability_registry.list()
            if capability.capability.enabled
            and capability.is_available(context)
        ]

    @staticmethod
    def _module_authorized(
        module: ModuleContract,
        context: FrameworkContext,
    ) -> bool:
        if any(
            not context.has_permission(permission)
            for permission in module.required_permissions
        ):
            return False

        if any(
            not context.has_entitlement(entitlement)
            for entitlement in module.required_entitlements
        ):
            return False

        return True

    @staticmethod
    def _navigation_authorized(
        item: NavigationContract,
        context: FrameworkContext,
    ) -> bool:
        if item.permission is not None and not context.has_permission(
            item.permission
        ):
            return False

        if item.entitlement is not None and not context.has_entitlement(
            item.entitlement
        ):
            return False

        return True
