from dataclasses import dataclass
from uuid import uuid4

import pytest

from phoenix_framework.context import FrameworkContext
from phoenix_framework.contracts import (
    ModuleContract,
    NavigationContract,
    PlatformCapability,
    PlatformCapabilityContract,
)
from phoenix_framework.modules import ModuleRegistry
from phoenix_framework.navigation import NavigationRegistry
from phoenix_framework.platform import CapabilityRegistry, FrameworkService


@dataclass(frozen=True)
class CapabilityStub(PlatformCapabilityContract):

    @property
    def capability(self) -> PlatformCapability:
        return PlatformCapability(
            code="search",
            name="Search",
            description="Global search.",
        )

    def is_available(self, context):
        return context.has_permission("search.use")

    def required_permissions(self):
        return ("search.use",)

    def required_entitlements(self):
        return ("platform.search",)


def make_service():
    return FrameworkService(
        ModuleRegistry(),
        NavigationRegistry(),
        CapabilityRegistry(),
    )


def make_context(
    permissions=(),
    entitlements=(),
):
    return FrameworkContext(
        request_id="req-001",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        session_id=None,
        permissions=frozenset(permissions),
        entitlements=frozenset(entitlements),
    )


def test_framework_service_returns_authorized_modules():
    service = make_service()

    service.module_registry.register(
        ModuleContract(
            code="crm",
            name="CRM",
            version="1.0.0",
            lifecycle="enabled",
            required_permissions=("crm.view",),
            required_entitlements=("crm",),
        )
    )

    context = make_context(
        permissions=("crm.view",),
        entitlements=("crm",),
    )

    modules = service.get_modules(context)

    assert [module.code for module in modules] == ["crm"]


def test_framework_service_filters_unauthorized_modules():
    service = make_service()

    service.module_registry.register(
        ModuleContract(
            code="crm",
            name="CRM",
            version="1.0.0",
            lifecycle="enabled",
            required_permissions=("crm.view",),
            required_entitlements=("crm",),
        )
    )

    context = make_context()

    assert service.get_modules(context) == []


def test_framework_service_filters_navigation_by_core_context():
    service = make_service()

    service.navigation_registry.register(
        NavigationContract(
            key="crm.customers",
            label="Customers",
            route="/crm/customers",
            permission="crm.customers.view",
            entitlement="crm",
        )
    )

    authorized = make_context(
        permissions=("crm.customers.view",),
        entitlements=("crm",),
    )

    unauthorized = make_context()

    assert len(service.get_navigation(authorized)) == 1
    assert service.get_navigation(unauthorized) == []


def test_framework_service_returns_available_capabilities():
    service = make_service()
    service.capability_registry.register(CapabilityStub())

    context = make_context(
        permissions=("search.use",),
    )

    capabilities = service.get_capabilities(context)

    assert [item.capability.code for item in capabilities] == ["search"]


def test_framework_service_filters_unavailable_capabilities():
    service = make_service()
    service.capability_registry.register(CapabilityStub())

    context = make_context()

    assert service.get_capabilities(context) == []


def test_framework_service_requires_authentication():
    service = make_service()

    context = FrameworkContext(
        request_id="req-002",
        identity_id=None,
        organisation_id=None,
        session_id=None,
        permissions=frozenset(),
        entitlements=frozenset(),
    )

    with pytest.raises(PermissionError):
        service.get_modules(context)


def test_framework_service_requires_tenant_context():
    service = make_service()

    context = FrameworkContext(
        request_id="req-003",
        identity_id=uuid4(),
        organisation_id=None,
        session_id=None,
        permissions=frozenset(),
        entitlements=frozenset(),
    )

    with pytest.raises(PermissionError):
        service.get_navigation(context)
