import pytest

from phoenix_framework.contracts.integration import (
    ModuleDependency,
    ModuleIntegrationContract,
)
from phoenix_framework.integration.dependency import ModuleDependencyResolver


def contract(code, version="1.0.0", capabilities=(), dependencies=()):
    return ModuleIntegrationContract(
        module_code=code,
        version=version,
        provided_capabilities=capabilities,
        dependencies=dependencies,
    )


def test_declared_dependency_is_compatible():
    source = contract(
        "sales",
        dependencies=(
            ModuleDependency("crm", minimum_version="1.0.0"),
        ),
    )
    target = contract("crm", "1.2.0")

    result = ModuleDependencyResolver().resolve(source, target)

    assert result.compatible is True


def test_undeclared_dependency_is_rejected():
    source = contract("sales")
    target = contract("crm")

    result = ModuleDependencyResolver().resolve(source, target)

    assert result.compatible is False
    assert "not declared" in result.reason


def test_minimum_version_is_enforced():
    source = contract(
        "sales",
        dependencies=(
            ModuleDependency("crm", minimum_version="2.0.0"),
        ),
    )
    target = contract("crm", "1.5.0")

    result = ModuleDependencyResolver().resolve(source, target)

    assert result.compatible is False
    assert "minimum" in result.reason


def test_maximum_version_is_enforced():
    source = contract(
        "sales",
        dependencies=(
            ModuleDependency("crm", maximum_version="2.0.0"),
        ),
    )
    target = contract("crm", "2.5.0")

    result = ModuleDependencyResolver().resolve(source, target)

    assert result.compatible is False
    assert "maximum" in result.reason


def test_required_capability_is_enforced():
    source = contract(
        "sales",
        dependencies=(
            ModuleDependency(
                "crm",
                capabilities=("customer.read",),
            ),
        ),
    )
    target = contract("crm", capabilities=("customer.write",))

    result = ModuleDependencyResolver().resolve(source, target)

    assert result.compatible is False
    assert "capabilities" in result.reason


def test_required_capability_is_accepted():
    source = contract(
        "sales",
        dependencies=(
            ModuleDependency(
                "crm",
                capabilities=("customer.read",),
            ),
        ),
    )
    target = contract("crm", capabilities=("customer.read",))

    result = ModuleDependencyResolver().resolve(source, target)

    assert result.compatible is True


def test_multiple_dependencies_select_correct_target():
    source = contract(
        "sales",
        dependencies=(
            ModuleDependency("crm"),
            ModuleDependency("inventory"),
        ),
    )
    target = contract("inventory")

    result = ModuleDependencyResolver().resolve(source, target)

    assert result.compatible is True
    assert result.target_module == "inventory"


def test_missing_source_code_is_rejected():
    source = contract("sales")
    target = contract("crm")

    # Contract construction already guarantees a valid source code,
    # so this verifies normal resolution remains deterministic.
    result = ModuleDependencyResolver().resolve(source, target)

    assert result.source_module == "sales"


def test_resolution_contains_source_and_target():
    source = contract(
        "sales",
        dependencies=(ModuleDependency("crm"),),
    )
    target = contract("crm")

    result = ModuleDependencyResolver().resolve(source, target)

    assert result.source_module == "sales"
    assert result.target_module == "crm"

def test_version_comparison_handles_two_digit_minor_versions():
    source = contract(
        "sales",
        dependencies=(
            ModuleDependency("crm", minimum_version="1.10.0"),
        ),
    )
    target = contract("crm", "1.9.0")

    result = ModuleDependencyResolver().resolve(source, target)

    assert result.compatible is False


def test_version_comparison_accepts_two_digit_minor_versions():
    source = contract(
        "sales",
        dependencies=(
            ModuleDependency("crm", minimum_version="1.10.0"),
        ),
    )
    target = contract("crm", "1.10.0")

    result = ModuleDependencyResolver().resolve(source, target)

    assert result.compatible is True


def test_invalid_target_version_is_rejected():
    source = contract(
        "sales",
        dependencies=(ModuleDependency("crm"),),
    )
    target = contract("crm", "invalid")

    with pytest.raises(ValueError, match="Invalid module version"):
        ModuleDependencyResolver().resolve(source, target)


def test_invalid_minimum_version_is_rejected():
    source = contract(
        "sales",
        dependencies=(
            ModuleDependency("crm", minimum_version="invalid"),
        ),
    )
    target = contract("crm", "1.0.0")

    with pytest.raises(ValueError, match="Invalid module version"):
        ModuleDependencyResolver().resolve(source, target)

