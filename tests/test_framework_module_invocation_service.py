from uuid import uuid4

import pytest

from phoenix_framework.context import FrameworkContext
from phoenix_framework.contracts import (
    ModuleContract,
    ModuleDependency,
    ModuleIntegrationContract,
    ModuleLifecycle,
)
from phoenix_framework.contracts.invocation import (
    ModuleInvocationRequest,
    ModuleInvocationResponse,
)
from phoenix_framework.integration.registry import IntegrationRegistry
from phoenix_framework.integration.service import ModuleInvocationService
from phoenix_framework.modules import ModuleRegistry


def make_context():
    return FrameworkContext(
        request_id="req-001",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        session_id=uuid4(),
        permissions=frozenset({"crm.view"}),
        entitlements=frozenset({"crm"}),
    )


def make_module_registry():
    registry = ModuleRegistry()

    registry.register(
        ModuleContract(
            code="sales",
            name="Sales",
            version="1.0.0",
            lifecycle=ModuleLifecycle.ENABLED,
        )
    )

    registry.register(
        ModuleContract(
            code="crm",
            name="CRM",
            version="1.0.0",
            lifecycle=ModuleLifecycle.ENABLED,
        )
    )

    return registry


def make_request():
    return ModuleInvocationRequest(
        request_id="req-001",
        source_module="sales",
        target_module="crm",
        contract="customer.lookup",
        operation="get_customer",
        context=make_context(),
        payload={"customer_id": "123"},
    )


def register_customer_lookup(registry, handler):
    registry.register(
        "crm",
        "customer.lookup",
        handler,
    )


def test_invoke_successfully_calls_target_module():
    registry = make_module_registry()
    integrations = IntegrationRegistry()

    calls = []

    def handler(*, operation, context, payload):
        calls.append((operation, context, payload))
        return {"customer_id": payload["customer_id"]}

    register_customer_lookup(integrations, handler)

    service = ModuleInvocationService(registry, integrations)

    response = service.invoke(make_request())

    assert response.success is True
    assert response.request_id == "req-001"
    assert response.data == {"customer_id": "123"}
    assert len(calls) == 1


def test_invoke_preserves_module_invocation_response():
    registry = make_module_registry()
    integrations = IntegrationRegistry()

    expected = ModuleInvocationResponse(
        request_id="req-001",
        success=True,
        data={"ok": True},
    )

    register_customer_lookup(
        integrations,
        lambda **kwargs: expected,
    )

    service = ModuleInvocationService(registry, integrations)

    response = service.invoke(make_request())

    assert response is expected


def test_invoke_rejects_missing_contract():
    registry = make_module_registry()
    service = ModuleInvocationService(
        registry,
        IntegrationRegistry(),
    )

    with pytest.raises(
        ValueError,
        match="Integration contract not registered",
    ):
        service.invoke(make_request())


def test_invoke_rejects_wrong_contract_owner():
    registry = make_module_registry()
    integrations = IntegrationRegistry()

    integrations.register(
        "sales",
        "customer.lookup",
        lambda **kwargs: {"unexpected": True},
    )

    service = ModuleInvocationService(registry, integrations)

    with pytest.raises(ValueError, match="is owned by module"):
        service.invoke(make_request())


def test_invoke_requires_authenticated_context():
    registry = make_module_registry()
    integrations = IntegrationRegistry()

    register_customer_lookup(
        integrations,
        lambda **kwargs: {"ok": True},
    )

    context = FrameworkContext(
        request_id="req-unauthenticated",
        identity_id=None,
        organisation_id=uuid4(),
        session_id=None,
        permissions=frozenset({"crm.view"}),
        entitlements=frozenset({"crm"}),
    )

    request = ModuleInvocationRequest(
        request_id="req-unauthenticated",
        source_module="sales",
        target_module="crm",
        contract="customer.lookup",
        operation="get_customer",
        context=context,
        payload={"customer_id": "123"},
    )

    service = ModuleInvocationService(registry, integrations)

    with pytest.raises(PermissionError):
        service.invoke(request)


def test_invoke_requires_tenant_context():
    registry = make_module_registry()
    integrations = IntegrationRegistry()

    register_customer_lookup(
        integrations,
        lambda **kwargs: {"ok": True},
    )

    context = FrameworkContext(
        request_id="req-no-tenant",
        identity_id=uuid4(),
        organisation_id=None,
        session_id=uuid4(),
        permissions=frozenset({"crm.view"}),
        entitlements=frozenset({"crm"}),
    )

    request = ModuleInvocationRequest(
        request_id="req-no-tenant",
        source_module="sales",
        target_module="crm",
        contract="customer.lookup",
        operation="get_customer",
        context=context,
        payload={"customer_id": "123"},
    )

    service = ModuleInvocationService(registry, integrations)

    with pytest.raises(PermissionError):
        service.invoke(request)


def test_invoke_requires_target_permission():
    registry = ModuleRegistry()

    registry.register(
        ModuleContract(
            code="sales",
            name="Sales",
            version="1.0.0",
            lifecycle=ModuleLifecycle.ENABLED,
        )
    )

    registry.register(
        ModuleContract(
            code="crm",
            name="CRM",
            version="1.0.0",
            lifecycle=ModuleLifecycle.ENABLED,
            required_permissions=("crm.admin",),
        )
    )

    integrations = IntegrationRegistry()
    register_customer_lookup(
        integrations,
        lambda **kwargs: {"ok": True},
    )

    service = ModuleInvocationService(registry, integrations)

    with pytest.raises(
        PermissionError,
        match="Required permission is missing",
    ):
        service.invoke(make_request())


def test_invoke_requires_target_entitlement():
    registry = ModuleRegistry()

    registry.register(
        ModuleContract(
            code="sales",
            name="Sales",
            version="1.0.0",
            lifecycle=ModuleLifecycle.ENABLED,
        )
    )

    registry.register(
        ModuleContract(
            code="crm",
            name="CRM",
            version="1.0.0",
            lifecycle=ModuleLifecycle.ENABLED,
            required_entitlements=("crm.pro",),
        )
    )

    integrations = IntegrationRegistry()
    register_customer_lookup(
        integrations,
        lambda **kwargs: {"ok": True},
    )

    service = ModuleInvocationService(registry, integrations)

    with pytest.raises(
        PermissionError,
        match="Required entitlement is missing",
    ):
        service.invoke(make_request())


def test_invoke_rejects_disabled_target_module():
    registry = make_module_registry()

    registry.register(
        ModuleContract(
            code="inventory",
            name="Inventory",
            version="1.0.0",
            lifecycle=ModuleLifecycle.DISABLED,
        )
    )

    integrations = IntegrationRegistry()
    integrations.register(
        "inventory",
        "inventory.lookup",
        lambda **kwargs: {"ok": True},
    )

    service = ModuleInvocationService(registry, integrations)

    request = ModuleInvocationRequest(
        request_id="req-disabled-target",
        source_module="sales",
        target_module="inventory",
        contract="inventory.lookup",
        operation="get_item",
        context=make_context(),
        payload={"item_id": "123"},
    )

    with pytest.raises(
        ValueError,
        match="Target module is not enabled",
    ):
        service.invoke(request)


def test_invoke_rejects_disabled_source_module():
    registry = ModuleRegistry()

    registry.register(
        ModuleContract(
            code="sales",
            name="Sales",
            version="1.0.0",
            lifecycle=ModuleLifecycle.DISABLED,
        )
    )

    registry.register(
        ModuleContract(
            code="crm",
            name="CRM",
            version="1.0.0",
            lifecycle=ModuleLifecycle.ENABLED,
        )
    )

    integrations = IntegrationRegistry()
    integrations.register(
        "crm",
        "customer.lookup",
        lambda **kwargs: {"ok": True},
    )

    service = ModuleInvocationService(registry, integrations)

    request = make_request()

    with pytest.raises(
        ValueError,
        match="Source module is not enabled",
    ):
        service.invoke(request)


def test_invoke_rejects_deprecated_target_module():
    registry = ModuleRegistry()

    registry.register(
        ModuleContract(
            code="sales",
            name="Sales",
            version="1.0.0",
            lifecycle=ModuleLifecycle.ENABLED,
        )
    )

    registry.register(
        ModuleContract(
            code="crm",
            name="CRM",
            version="1.0.0",
            lifecycle=ModuleLifecycle.DEPRECATED,
        )
    )

    integrations = IntegrationRegistry()
    integrations.register(
        "crm",
        "customer.lookup",
        lambda **kwargs: {"ok": True},
    )

    service = ModuleInvocationService(registry, integrations)

    request = make_request()

    with pytest.raises(
        ValueError,
        match="Target module is not enabled",
    ):
        service.invoke(request)


def test_invoke_allows_compatible_required_dependency():
    registry = make_module_registry()
    integrations = IntegrationRegistry()

    source_contract = ModuleIntegrationContract(
        module_code="sales",
        version="1.0.0",
        dependencies=(
            ModuleDependency(
                module_code="crm",
                minimum_version="1.0.0",
                maximum_version="2.0.0",
                required=True,
                capabilities=("customer.lookup",),
            ),
        ),
    )

    target_contract = ModuleIntegrationContract(
        module_code="crm",
        version="1.5.0",
        provided_contracts=("customer.lookup",),
        provided_capabilities=("customer.lookup",),
    )

    integrations.register_module_contract(source_contract)
    integrations.register(
        "crm",
        "customer.lookup",
        lambda **kwargs: {"ok": True},
        target_contract,
    )

    service = ModuleInvocationService(registry, integrations)

    response = service.invoke(make_request())

    assert response.success is True
    assert response.data == {"ok": True}


def test_invoke_rejects_incompatible_required_dependency():
    registry = make_module_registry()
    integrations = IntegrationRegistry()

    source_contract = ModuleIntegrationContract(
        module_code="sales",
        version="1.0.0",
        dependencies=(
            ModuleDependency(
                module_code="crm",
                minimum_version="2.0.0",
                required=True,
            ),
        ),
    )

    target_contract = ModuleIntegrationContract(
        module_code="crm",
        version="1.5.0",
        provided_contracts=("customer.lookup",),
    )

    integrations.register_module_contract(source_contract)
    integrations.register(
        "crm",
        "customer.lookup",
        lambda **kwargs: {"ok": True},
        target_contract,
    )

    service = ModuleInvocationService(registry, integrations)

    with pytest.raises(
        ValueError,
        match="Module dependency is not satisfied",
    ):
        service.invoke(make_request())


def test_invoke_allows_incompatible_optional_dependency():
    registry = make_module_registry()
    integrations = IntegrationRegistry()

    source_contract = ModuleIntegrationContract(
        module_code="sales",
        version="1.0.0",
        dependencies=(
            ModuleDependency(
                module_code="crm",
                minimum_version="2.0.0",
                required=False,
            ),
        ),
    )

    target_contract = ModuleIntegrationContract(
        module_code="crm",
        version="1.5.0",
        provided_contracts=("customer.lookup",),
    )

    integrations.register_module_contract(source_contract)
    integrations.register(
        "crm",
        "customer.lookup",
        lambda **kwargs: {"ok": True},
        target_contract,
    )

    service = ModuleInvocationService(registry, integrations)

    response = service.invoke(make_request())

    assert response.success is True
    assert response.data == {"ok": True}


def test_invoke_rejects_undeclared_required_dependency():
    registry = make_module_registry()
    integrations = IntegrationRegistry()

    source_contract = ModuleIntegrationContract(
        module_code="sales",
        version="1.0.0",
        dependencies=(),
    )

    target_contract = ModuleIntegrationContract(
        module_code="crm",
        version="1.0.0",
        provided_contracts=("customer.lookup",),
    )

    integrations.register_module_contract(source_contract)
    integrations.register(
        "crm",
        "customer.lookup",
        lambda **kwargs: {"ok": True},
        target_contract,
    )

    service = ModuleInvocationService(registry, integrations)

    with pytest.raises(
        ValueError,
        match="Module dependency is not satisfied",
    ):
        service.invoke(make_request())
