"""Phoenix module invocation service."""

from phoenix_framework.contracts.invocation import (
    ModuleInvocationRequest,
    ModuleInvocationResponse,
)
from phoenix_framework.integration.dependency import ModuleDependencyResolver
from phoenix_framework.integration.registry import IntegrationRegistry
from phoenix_framework.modules import ModuleRegistry


class ModuleInvocationService:
    """
    Routes synchronous calls between registered Phoenix modules.

    This service provides integration infrastructure only. It does not
    own module business logic, persistence, security authority, or
    tenant authority.
    """

    def __init__(
        self,
        module_registry: ModuleRegistry,
        integration_registry: IntegrationRegistry,
        dependency_resolver: ModuleDependencyResolver | None = None,
    ) -> None:
        self.module_registry = module_registry
        self.integration_registry = integration_registry
        self.dependency_resolver = (
            dependency_resolver or ModuleDependencyResolver()
        )

    def invoke(
        self,
        request: ModuleInvocationRequest,
    ) -> ModuleInvocationResponse:
        """Invoke a contract within the authenticated tenant context."""

        request.context.require_authenticated()
        request.context.require_tenant()

        source_module = self.module_registry.get(request.source_module)
        target_module = self.module_registry.get(request.target_module)

        if not source_module.enabled:
            raise ValueError(
                f"Source module is not enabled: {source_module.code}"
            )

        if not target_module.enabled:
            raise ValueError(
                f"Target module is not enabled: {target_module.code}"
            )

        for permission in target_module.required_permissions:
            if not request.context.has_permission(permission):
                raise PermissionError(
                    f"Required permission is missing: {permission}"
                )

        for entitlement in target_module.required_entitlements:
            if not request.context.has_entitlement(entitlement):
                raise PermissionError(
                    f"Required entitlement is missing: {entitlement}"
                )

        if not self.integration_registry.has(request.contract):
            raise ValueError(
                f"Integration contract not registered: {request.contract}"
            )

        if not self.integration_registry.owned_by(
            request.contract,
            request.target_module,
        ):
            publication = self.integration_registry.get_publication(
                request.contract
            )
            raise ValueError(
                f"Integration contract '{request.contract}' is owned by "
                f"module '{publication.module_code}', not "
                f"'{request.target_module}'."
            )

        self._validate_dependency(
            request.source_module,
            request.target_module,
            request.contract,
        )

        handler = self.integration_registry.get(request.contract)

        result = handler(
            operation=request.operation,
            context=request.context,
            payload=request.payload,
        )

        if isinstance(result, ModuleInvocationResponse):
            return result

        return ModuleInvocationResponse(
            request_id=request.request_id,
            success=True,
            data=result,
        )

    def _validate_dependency(
        self,
        source_module: str,
        target_module: str,
        contract: str,
    ) -> None:
        """
        Validate the source module's declared dependency on the target.

        Modules without registered integration metadata remain compatible
        with the existing invocation model. Once a source module publishes
        integration metadata, its declared dependencies govern cross-module
        invocation.
        """

        if not self.integration_registry.has_module_contract(source_module):
            return

        source_contract = self.integration_registry.get_module_contract(
            source_module
        )

        target_contract = self.integration_registry.get_integration_contract(
            contract
        )

        resolution = self.dependency_resolver.resolve(
            source_contract,
            target_contract,
        )

        if resolution.compatible:
            return

        if not resolution.required:
            return

        raise ValueError(
            f"Module dependency is not satisfied: "
            f"{resolution.reason}"
        )
