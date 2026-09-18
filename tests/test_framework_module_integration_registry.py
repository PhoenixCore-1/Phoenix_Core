from phoenix_framework.contracts.integration import ModuleIntegrationContract
from phoenix_framework.integration.registry import IntegrationRegistry
import pytest


def make_contract():
    return ModuleIntegrationContract(
        module_code="crm",
        version="1.0.0",
        provided_contracts=("customer.lookup",),
        provided_capabilities=("customer.read",),
    )


def test_register_accepts_integration_contract_metadata():
    registry = IntegrationRegistry()

    registry.register(
        "crm",
        "customer.lookup",
        lambda **kwargs: {"ok": True},
        make_contract(),
    )

    metadata = registry.get_integration_contract("customer.lookup")

    assert metadata.module_code == "crm"
    assert metadata.version == "1.0.0"
    assert metadata.provides_contract("customer.lookup")


def test_register_rejects_metadata_from_wrong_module():
    registry = IntegrationRegistry()

    wrong_contract = ModuleIntegrationContract(
        module_code="sales",
        version="1.0.0",
        provided_contracts=("customer.lookup",),
    )

    with pytest.raises(
        ValueError,
        match="module code must match",
    ):
        registry.register(
            "crm",
            "customer.lookup",
            lambda **kwargs: {"ok": True},
            wrong_contract,
        )


def test_register_rejects_metadata_that_does_not_declare_contract():
    registry = IntegrationRegistry()

    metadata = ModuleIntegrationContract(
        module_code="crm",
        version="1.0.0",
        provided_contracts=("customer.search",),
    )

    with pytest.raises(
        ValueError,
        match="must declare",
    ):
        registry.register(
            "crm",
            "customer.lookup",
            lambda **kwargs: {"ok": True},
            metadata,
        )


def test_get_integration_contract_rejects_missing_metadata():
    registry = IntegrationRegistry()

    registry.register(
        "crm",
        "customer.lookup",
        lambda **kwargs: {"ok": True},
    )

    with pytest.raises(
        ValueError,
        match="metadata not registered",
    ):
        registry.get_integration_contract("customer.lookup")


def test_existing_registration_without_metadata_remains_supported():
    registry = IntegrationRegistry()

    registry.register(
        "crm",
        "customer.lookup",
        lambda **kwargs: {"ok": True},
    )

    assert registry.has("customer.lookup")
    assert registry.owned_by("customer.lookup", "crm")
