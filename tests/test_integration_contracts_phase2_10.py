from uuid import uuid4

from phoenix_core.api.integration.contracts import (
    CoreIntegrationContract,
    IntegrationRequest,
    IntegrationResponse,
)


def test_integration_request_is_immutable():
    request = IntegrationRequest(
        request_id="req-int-001",
        operation="example.operation",
        session_id=uuid4(),
        organisation_id=uuid4(),
        payload={"value": 123},
    )

    assert request.request_id == "req-int-001"
    assert request.operation == "example.operation"
    assert request.payload == {"value": 123}

    try:
        request.operation = "changed"
        assert False, "Expected frozen IntegrationRequest"
    except AttributeError:
        pass


def test_integration_response_is_immutable():
    response = IntegrationResponse(
        request_id="req-int-002",
        success=True,
        data={"status": "accepted"},
    )

    assert response.request_id == "req-int-002"
    assert response.success is True
    assert response.data["status"] == "accepted"

    try:
        response.success = False
        assert False, "Expected frozen IntegrationResponse"
    except AttributeError:
        pass


def test_core_integration_contract_is_runtime_protocol():
    class ExampleIntegration(CoreIntegrationContract):
        def handle(self, request):
            return IntegrationResponse(
                request_id=request.request_id,
                success=True,
                data={"operation": request.operation},
            )

    integration = ExampleIntegration()

    request = IntegrationRequest(
        request_id="req-int-003",
        operation="example.operation",
    )

    response = integration.handle(request)

    assert isinstance(response, IntegrationResponse)
    assert response.request_id == "req-int-003"
    assert response.success is True
    assert response.data["operation"] == "example.operation"
