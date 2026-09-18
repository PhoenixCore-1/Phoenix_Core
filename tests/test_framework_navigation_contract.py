from dataclasses import FrozenInstanceError

import pytest

from phoenix_framework.contracts import NavigationContract


def test_navigation_contract_contains_required_metadata():
    item = NavigationContract(
        key="crm.customers",
        label="Customers",
        route="/crm/customers",
        module_code="crm",
        icon="customers",
        order=10,
    )

    assert item.key == "crm.customers"
    assert item.label == "Customers"
    assert item.route == "/crm/customers"
    assert item.module_code == "crm"
    assert item.icon == "customers"
    assert item.order == 10
    assert item.enabled is True


def test_navigation_contract_supports_permission_and_entitlement():
    item = NavigationContract(
        key="sales.quotes",
        label="Quotes",
        route="/sales/quotes",
        module_code="sales",
        permission="sales.quotes.view",
        entitlement="sales",
    )

    assert item.requires_authorization
    assert item.requires_permission("sales.quotes.view")
    assert not item.requires_permission("sales.quotes.edit")
    assert item.requires_entitlement("sales")
    assert not item.requires_entitlement("crm")


def test_navigation_without_authorization_metadata():
    item = NavigationContract(
        key="platform.home",
        label="Home",
        route="/",
    )

    assert not item.requires_authorization


def test_navigation_can_be_disabled():
    item = NavigationContract(
        key="example.disabled",
        label="Disabled",
        route="/disabled",
        enabled=False,
    )

    assert not item.enabled


def test_navigation_contract_is_immutable():
    item = NavigationContract(
        key="example.home",
        label="Home",
        route="/",
    )

    with pytest.raises(FrozenInstanceError):
        item.label = "Changed"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"key": "", "label": "Home", "route": "/"},
        {"key": "home", "label": "", "route": "/"},
        {"key": "home", "label": "Home", "route": ""},
    ],
)
def test_navigation_rejects_missing_required_fields(kwargs):
    with pytest.raises(ValueError):
        NavigationContract(**kwargs)


def test_navigation_supports_generic_metadata():
    item = NavigationContract(
        key="platform.search",
        label="Search",
        route="/search",
        metadata={"category": "platform", "scope": "global"},
    )

    assert item.metadata["category"] == "platform"
    assert item.metadata["scope"] == "global"
