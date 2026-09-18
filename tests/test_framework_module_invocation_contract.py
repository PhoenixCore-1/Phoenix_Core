from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from phoenix_framework.context import FrameworkContext
from phoenix_framework.contracts.invocation import (
    ModuleInvocationRequest,
    ModuleInvocationResponse,
)


def make_context():
    return FrameworkContext(
        request_id="req-001",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        session_id=uuid4(),
        permissions=frozenset({"sales.view"}),
        entitlements=frozenset({"sales"}),
    )


def test_invocation_request_contains_required_fields():
    context = make_context()

    request = ModuleInvocationRequest(
        request_id="req-001",
        source_module="sales",
        target_module="crm",
        contract="customer.lookup",
        operation="get_customer",
        context=context,
        payload={"customer_id": "123"},
    )

    assert request.source_module == "sales"
    assert request.target_module == "crm"
    assert request.contract == "customer.lookup"
    assert request.operation == "get_customer"
    assert request.payload["customer_id"] == "123"


def test_invocation_request_carries_framework_context():
    context = make_context()

    request = ModuleInvocationRequest(
        request_id="req-001",
        source_module="sales",
        target_module="crm",
        contract="customer.lookup",
        operation="get_customer",
        context=context,
    )

    assert request.context is context
    assert request.context.organisation_id == context.organisation_id
    assert request.context.identity_id == context.identity_id


def test_invocation_response_contains_result():
    response = ModuleInvocationResponse(
        request_id="req-001",
        success=True,
        data={"customer_id": "123"},
    )

    assert response.request_id == "req-001"
    assert response.success
    assert response.data["customer_id"] == "123"
    assert response.error is None


def test_invocation_response_supports_failure():
    response = ModuleInvocationResponse(
        request_id="req-001",
        success=False,
        error="Customer not found",
    )

    assert not response.success
    assert response.error == "Customer not found"


@pytest.mark.parametrize(
    "field,value",
    [
        ("request_id", ""),
        ("source_module", ""),
        ("target_module", ""),
        ("contract", ""),
        ("operation", ""),
    ],
)
def test_invocation_request_rejects_missing_required_fields(field, value):
    context = make_context()

    values = {
        "request_id": "req-001",
        "source_module": "sales",
        "target_module": "crm",
        "contract": "customer.lookup",
        "operation": "get_customer",
        "context": context,
    }
    values[field] = value

    with pytest.raises(ValueError):
        ModuleInvocationRequest(**values)


def test_invocation_request_rejects_self_invocation():
    context = make_context()

    with pytest.raises(ValueError):
        ModuleInvocationRequest(
            request_id="req-001",
            source_module="sales",
            target_module="sales",
            contract="sales.lookup",
            operation="get_order",
            context=context,
        )


def test_invocation_request_is_immutable():
    context = make_context()

    request = ModuleInvocationRequest(
        request_id="req-001",
        source_module="sales",
        target_module="crm",
        contract="customer.lookup",
        operation="get_customer",
        context=context,
    )

    with pytest.raises(FrozenInstanceError):
        request.operation = "delete_customer"


def test_invocation_response_is_immutable():
    response = ModuleInvocationResponse(
        request_id="req-001",
        success=True,
    )

    with pytest.raises(FrozenInstanceError):
        response.success = False


def test_invocation_request_supports_empty_payload():
    context = make_context()

    request = ModuleInvocationRequest(
        request_id="req-001",
        source_module="sales",
        target_module="crm",
        contract="customer.lookup",
        operation="get_customer",
        context=context,
    )

    assert request.payload is None
