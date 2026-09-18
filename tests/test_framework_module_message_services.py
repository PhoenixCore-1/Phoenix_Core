from phoenix_framework.contracts.command import ModuleCommand
from phoenix_framework.contracts.invocation import ModuleInvocationResponse
from phoenix_framework.contracts.query import ModuleQuery
from phoenix_framework.integration.messages import (
    ModuleCommandService,
    ModuleQueryService,
)


class FakeInvocationService:
    def __init__(self):
        self.requests = []

    def invoke(self, request):
        self.requests.append(request)
        return ModuleInvocationResponse(
            request_id=request.request_id,
            success=True,
            data={"ok": True},
        )


def test_command_service_maps_command_to_invocation_request():
    invocation = FakeInvocationService()
    service = ModuleCommandService(invocation)

    context = object()

    command = ModuleCommand(
        request_id="cmd-001",
        source_module="sales",
        target_module="inventory",
        name="stock.reserve",
        context=context,
        payload={"item_id": "123"},
    )

    response = service.execute(command)

    assert response.success
    assert response.request_id == "cmd-001"
    assert len(invocation.requests) == 1

    request = invocation.requests[0]

    assert request.source_module == "sales"
    assert request.target_module == "inventory"
    assert request.contract == "stock.reserve"
    assert request.operation == "stock.reserve"
    assert request.context is context
    assert request.payload == {"item_id": "123"}


def test_query_service_maps_query_to_invocation_request():
    invocation = FakeInvocationService()
    service = ModuleQueryService(invocation)

    context = object()

    query = ModuleQuery(
        request_id="qry-001",
        source_module="sales",
        target_module="crm",
        name="customer.lookup",
        context=context,
        parameters={"customer_id": "123"},
    )

    response = service.execute(query)

    assert response.success
    assert response.request_id == "qry-001"
    assert len(invocation.requests) == 1

    request = invocation.requests[0]

    assert request.source_module == "sales"
    assert request.target_module == "crm"
    assert request.contract == "customer.lookup"
    assert request.operation == "customer.lookup"
    assert request.context is context
    assert request.payload == {"customer_id": "123"}


def test_command_service_returns_invocation_response_unchanged():
    invocation = FakeInvocationService()
    service = ModuleCommandService(invocation)

    command = ModuleCommand(
        request_id="cmd-002",
        source_module="sales",
        target_module="inventory",
        name="stock.reserve",
        context=object(),
    )

    response = service.execute(command)

    assert response.data == {"ok": True}


def test_query_service_returns_invocation_response_unchanged():
    invocation = FakeInvocationService()
    service = ModuleQueryService(invocation)

    query = ModuleQuery(
        request_id="qry-002",
        source_module="sales",
        target_module="crm",
        name="customer.lookup",
        context=object(),
    )

    response = service.execute(query)

    assert response.data == {"ok": True}
