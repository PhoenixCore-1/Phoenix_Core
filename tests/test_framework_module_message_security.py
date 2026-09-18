from uuid import uuid4

import pytest

from phoenix_framework.context import FrameworkContext
from phoenix_framework.contracts import (
    ModuleCommand,
    ModuleContract,
    ModuleLifecycle,
    ModuleQuery,
)
from phoenix_framework.integration.messages import (
    ModuleCommandService,
    ModuleQueryService,
)
from phoenix_framework.integration.registry import IntegrationRegistry
from phoenix_framework.integration.service import ModuleInvocationService
from phoenix_framework.modules import ModuleRegistry


def make_registry():
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
            required_permissions=("crm.view",),
            required_entitlements=("crm",),
        )
    )

    return registry


def make_context(
    permissions=frozenset({"crm.view"}),
    entitlements=frozenset({"crm"}),
):
    return FrameworkContext(
        request_id="req-001",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        session_id=uuid4(),
        permissions=permissions,
        entitlements=entitlements,
    )


def make_invocation_service():
    registry = make_registry()
    integrations = IntegrationRegistry()

    integrations.register(
        "crm",
        "customer.lookup",
        lambda **kwargs: {"customer_id": "123"},
    )

    return ModuleInvocationService(registry, integrations)


def test_command_inherits_permission_enforcement():
    invocation = make_invocation_service()
    service = ModuleCommandService(invocation)

    command = ModuleCommand(
        request_id="cmd-001",
        source_module="sales",
        target_module="crm",
        name="customer.lookup",
        context=make_context(permissions=frozenset()),
    )

    with pytest.raises(
        PermissionError,
        match="Required permission is missing",
    ):
        service.execute(command)


def test_command_inherits_entitlement_enforcement():
    invocation = make_invocation_service()
    service = ModuleCommandService(invocation)

    command = ModuleCommand(
        request_id="cmd-002",
        source_module="sales",
        target_module="crm",
        name="customer.lookup",
        context=make_context(entitlements=frozenset()),
    )

    with pytest.raises(
        PermissionError,
        match="Required entitlement is missing",
    ):
        service.execute(command)


def test_query_inherits_permission_enforcement():
    invocation = make_invocation_service()
    service = ModuleQueryService(invocation)

    query = ModuleQuery(
        request_id="qry-001",
        source_module="sales",
        target_module="crm",
        name="customer.lookup",
        context=make_context(permissions=frozenset()),
    )

    with pytest.raises(
        PermissionError,
        match="Required permission is missing",
    ):
        service.execute(query)


def test_query_inherits_entitlement_enforcement():
    invocation = make_invocation_service()
    service = ModuleQueryService(invocation)

    query = ModuleQuery(
        request_id="qry-002",
        source_module="sales",
        target_module="crm",
        name="customer.lookup",
        context=make_context(entitlements=frozenset()),
    )

    with pytest.raises(
        PermissionError,
        match="Required entitlement is missing",
    ):
        service.execute(query)


def test_command_inherits_tenant_enforcement():
    invocation = make_invocation_service()
    service = ModuleCommandService(invocation)

    context = FrameworkContext(
        request_id="cmd-no-tenant",
        identity_id=uuid4(),
        organisation_id=None,
        session_id=uuid4(),
        permissions=frozenset({"crm.view"}),
        entitlements=frozenset({"crm"}),
    )

    command = ModuleCommand(
        request_id="cmd-no-tenant",
        source_module="sales",
        target_module="crm",
        name="customer.lookup",
        context=context,
    )

    with pytest.raises(PermissionError):
        service.execute(command)


def test_query_inherits_authentication_enforcement():
    invocation = make_invocation_service()
    service = ModuleQueryService(invocation)

    context = FrameworkContext(
        request_id="qry-unauthenticated",
        identity_id=None,
        organisation_id=uuid4(),
        session_id=None,
        permissions=frozenset({"crm.view"}),
        entitlements=frozenset({"crm"}),
    )

    query = ModuleQuery(
        request_id="qry-unauthenticated",
        source_module="sales",
        target_module="crm",
        name="customer.lookup",
        context=context,
    )

    with pytest.raises(PermissionError):
        service.execute(query)
