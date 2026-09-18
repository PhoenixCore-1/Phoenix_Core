from dataclasses import FrozenInstanceError

import pytest

from phoenix_framework.contracts.integration import (
    ModuleDependency,
    ModuleIntegrationContract,
)


def test_module_dependency_contains_identity_and_version_range():
    dependency = ModuleDependency(
        module_code="crm",
        minimum_version="1.0.0",
        maximum_version="2.0.0",
    )

    assert dependency.module_code == "crm"
    assert dependency.minimum_version == "1.0.0"
    assert dependency.maximum_version == "2.0.0"
    assert dependency.required


def test_optional_dependency_is_supported():
    dependency = ModuleDependency(
        module_code="accounts",
        required=False,
    )

    assert not dependency.required


def test_dependency_supports_capabilities():
    dependency = ModuleDependency(
        module_code="inventory",
        capabilities=("item.lookup", "stock.reserve"),
    )

    assert dependency.requires_capability("item.lookup")
    assert dependency.requires_capability("stock.reserve")
    assert not dependency.requires_capability("item.delete")


def test_module_integration_contract_contains_identity():
    contract = ModuleIntegrationContract(
        module_code="sales",
        version="1.0.0",
    )

    assert contract.module_code == "sales"
    assert contract.version == "1.0.0"


def test_module_integration_contract_exposes_contracts_and_capabilities():
    contract = ModuleIntegrationContract(
        module_code="crm",
        version="1.0.0",
        provided_contracts=("customer.lookup",),
        provided_capabilities=("customer.search",),
    )

    assert contract.provides_contract("customer.lookup")
    assert not contract.provides_contract("customer.delete")
    assert contract.provides_capability("customer.search")
    assert not contract.provides_capability("customer.export")


def test_module_integration_contract_supports_dependencies():
    dependency = ModuleDependency(module_code="inventory")

    contract = ModuleIntegrationContract(
        module_code="sales",
        version="1.0.0",
        dependencies=(dependency,),
    )

    assert contract.depends_on("inventory")
    assert not contract.depends_on("crm")


def test_module_integration_contract_is_immutable():
    contract = ModuleIntegrationContract(
        module_code="crm",
        version="1.0.0",
    )

    with pytest.raises(FrozenInstanceError):
        contract.version = "2.0.0"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"module_code": "", "version": "1.0.0"},
        {"module_code": "crm", "version": ""},
    ],
)
def test_module_integration_contract_rejects_missing_identity(kwargs):
    with pytest.raises(ValueError):
        ModuleIntegrationContract(**kwargs)


def test_module_dependency_rejects_missing_module_code():
    with pytest.raises(ValueError):
        ModuleDependency(module_code="")
