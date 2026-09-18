from dataclasses import dataclass

import pytest

from phoenix_framework.contracts import (
    ModuleContract,
    NavigationContract,
    PlatformCapability,
    PlatformCapabilityContract,
)
from phoenix_framework.modules import ModuleRegistry
from phoenix_framework.navigation import NavigationRegistry
from phoenix_framework.platform import CapabilityRegistry


def test_module_registry_registers_and_retrieves_modules():
    registry = ModuleRegistry()

    module = ModuleContract(
        code="crm",
        name="CRM",
        version="1.0.0",
    )

    registry.register(module)

    assert registry.has("crm")
    assert registry.get("crm") is module
    assert registry.list() == [module]


def test_module_registry_rejects_duplicates_and_unknown_modules():
    registry = ModuleRegistry()

    module = ModuleContract(
        code="crm",
        name="CRM",
        version="1.0.0",
    )

    registry.register(module)

    with pytest.raises(ValueError):
        registry.register(module)

    with pytest.raises(ValueError):
        registry.get("missing")


def test_navigation_registry_orders_navigation_items():
    registry = NavigationRegistry()

    second = NavigationContract(
        key="second",
        label="Second",
        route="/second",
        order=20,
    )

    first = NavigationContract(
        key="first",
        label="First",
        route="/first",
        order=10,
    )

    registry.register(second)
    registry.register(first)

    assert [item.key for item in registry.list()] == ["first", "second"]


def test_navigation_registry_rejects_duplicates():
    registry = NavigationRegistry()

    item = NavigationContract(
        key="home",
        label="Home",
        route="/",
    )

    registry.register(item)

    with pytest.raises(ValueError):
        registry.register(item)

    with pytest.raises(ValueError):
        registry.get("missing")


@dataclass(frozen=True)
class SearchCapability(PlatformCapabilityContract):

    @property
    def capability(self) -> PlatformCapability:
        return PlatformCapability(
            code="search",
            name="Search",
            description="Global search.",
        )

    def is_available(self, context):
        return True

    def required_permissions(self):
        return ()

    def required_entitlements(self):
        return ()


def test_capability_registry_registers_and_retrieves_capabilities():
    registry = CapabilityRegistry()
    capability = SearchCapability()

    registry.register(capability)

    assert registry.has("search")
    assert registry.get("search") is capability
    assert registry.list() == [capability]


def test_capability_registry_rejects_duplicates_and_unknown_capabilities():
    registry = CapabilityRegistry()
    capability = SearchCapability()

    registry.register(capability)

    with pytest.raises(ValueError):
        registry.register(capability)

    with pytest.raises(ValueError):
        registry.get("missing")
