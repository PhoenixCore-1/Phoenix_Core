from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from phoenix_framework.contracts import (
    CompanyContext,
    ModuleDescriptor,
    NavigationItem,
    PlatformCapability,
    UserContext,
)


def test_company_context_is_immutable():
    context = CompanyContext(
        organisation_id=uuid4(),
        name="Test Company",
    )

    with pytest.raises(FrozenInstanceError):
        context.name = "Changed"


def test_user_context_permissions_and_entitlements():
    organisation_id = uuid4()

    context = UserContext(
        identity_id=uuid4(),
        username="test.user",
        display_name="Test User",
        organisation_id=organisation_id,
        permissions=frozenset({"crm.view", "sales.view"}),
        entitlements=frozenset({"crm", "sales"}),
    )

    assert context.has_permission("crm.view")
    assert not context.has_permission("production.view")
    assert context.has_entitlement("crm")
    assert not context.has_entitlement("inventory")


def test_module_descriptor_contains_generic_module_metadata():
    descriptor = ModuleDescriptor(
        code="crm",
        name="CRM",
        version="1.0.0",
        navigation_label="CRM",
    )

    assert descriptor.code == "crm"
    assert descriptor.name == "CRM"
    assert descriptor.version == "1.0.0"
    assert descriptor.enabled is True


def test_navigation_item_supports_authorization_metadata():
    item = NavigationItem(
        key="crm.customers",
        label="Customers",
        route="/crm/customers",
        icon="customers",
        module_code="crm",
        permission="crm.customers.view",
        entitlement="crm",
        order=10,
    )

    assert item.key == "crm.customers"
    assert item.route == "/crm/customers"
    assert item.module_code == "crm"
    assert item.permission == "crm.customers.view"
    assert item.entitlement == "crm"


def test_platform_capability_is_generic():
    capability = PlatformCapability(
        code="global_search",
        name="Global Search",
        description="Search authorised Phoenix data.",
    )

    assert capability.code == "global_search"
    assert capability.enabled is True


def test_contracts_do_not_import_business_modules():
    import phoenix_framework.contracts.platform as platform_contracts

    module_names = set(platform_contracts.__dict__.keys())

    assert not any(
        name.lower() in {"crm", "sales", "production", "inventory", "procurement", "accounts", "projects"}
        for name in module_names
    )
