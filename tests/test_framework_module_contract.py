from dataclasses import FrozenInstanceError

import pytest

from phoenix_framework.contracts import ModuleContract, ModuleLifecycle


def test_module_contract_contains_generic_identity():
    module = ModuleContract(
        code="crm",
        name="CRM",
        version="1.0.0",
        description="Customer relationship management.",
    )

    assert module.code == "crm"
    assert module.name == "CRM"
    assert module.version == "1.0.0"
    assert module.lifecycle == ModuleLifecycle.REGISTERED
    assert not module.enabled


def test_enabled_module_is_reported_as_enabled():
    module = ModuleContract(
        code="example",
        name="Example",
        version="1.0.0",
        lifecycle=ModuleLifecycle.ENABLED,
    )

    assert module.enabled


def test_module_contract_supports_authorization_requirements():
    module = ModuleContract(
        code="example",
        name="Example",
        version="1.0.0",
        required_permissions=("example.view", "example.edit"),
        required_entitlements=("example",),
    )

    assert module.requires_permission("example.view")
    assert module.requires_permission("example.edit")
    assert not module.requires_permission("example.delete")
    assert module.requires_entitlement("example")
    assert not module.requires_entitlement("other")


def test_module_contract_supports_navigation_and_capabilities():
    module = ModuleContract(
        code="example",
        name="Example",
        version="1.0.0",
        navigation_keys=("example.home", "example.settings"),
        capabilities=("search", "reporting"),
    )

    assert module.exposes_navigation("example.home")
    assert not module.exposes_navigation("example.admin")
    assert module.exposes_capability("search")
    assert not module.exposes_capability("billing")


def test_module_contract_is_immutable():
    module = ModuleContract(
        code="example",
        name="Example",
        version="1.0.0",
    )

    with pytest.raises(FrozenInstanceError):
        module.name = "Changed"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"code": "", "name": "Example", "version": "1.0.0"},
        {"code": "example", "name": "", "version": "1.0.0"},
        {"code": "example", "name": "Example", "version": ""},
    ],
)
def test_module_contract_rejects_missing_identity_fields(kwargs):
    with pytest.raises(ValueError):
        ModuleContract(**kwargs)


def test_module_contract_supports_metadata():
    module = ModuleContract(
        code="example",
        name="Example",
        version="1.0.0",
        metadata={"vendor": "Phoenix", "category": "business"},
    )

    assert module.metadata["vendor"] == "Phoenix"
    assert module.metadata["category"] == "business"
