"""Phoenix Framework command and query integration adapters."""

from phoenix_framework.contracts.command import ModuleCommand
from phoenix_framework.contracts.invocation import ModuleInvocationRequest
from phoenix_framework.contracts.query import ModuleQuery
from phoenix_framework.integration.service import ModuleInvocationService


class ModuleCommandService:
    """
    Routes module commands through the authoritative invocation boundary.

    Commands represent requests to perform state-changing operations.
    Security, tenant isolation, lifecycle and dependency enforcement remain
    owned by ModuleInvocationService.
    """

    def __init__(self, invocation_service: ModuleInvocationService) -> None:
        self.invocation_service = invocation_service

    def execute(self, command: ModuleCommand):
        request = ModuleInvocationRequest(
            request_id=command.request_id,
            source_module=command.source_module,
            target_module=command.target_module,
            contract=command.name,
            operation=command.name,
            context=command.context,
            payload=command.payload,
        )

        return self.invocation_service.invoke(request)


class ModuleQueryService:
    """
    Routes module queries through the authoritative invocation boundary.

    Queries represent read-only information requests. Security, tenant
    isolation, lifecycle and dependency enforcement remain owned by
    ModuleInvocationService.
    """

    def __init__(self, invocation_service: ModuleInvocationService) -> None:
        self.invocation_service = invocation_service

    def execute(self, query: ModuleQuery):
        request = ModuleInvocationRequest(
            request_id=query.request_id,
            source_module=query.source_module,
            target_module=query.target_module,
            contract=query.name,
            operation=query.name,
            context=query.context,
            payload=query.parameters,
        )

        return self.invocation_service.invoke(request)
