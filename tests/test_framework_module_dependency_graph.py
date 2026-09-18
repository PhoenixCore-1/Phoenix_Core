import pytest

from phoenix_framework.contracts.integration import (
    ModuleDependency,
    ModuleIntegrationContract,
)
from phoenix_framework.integration.graph import ModuleDependencyGraph


def contract(code, dependencies=()):
    return ModuleIntegrationContract(
        module_code=code,
        version="1.0.0",
        dependencies=dependencies,
    )


def test_valid_dependency_graph():
    graph = ModuleDependencyGraph(
        (
            contract(
                "sales",
                dependencies=(ModuleDependency("crm"),),
            ),
            contract("crm"),
        )
    )

    result = graph.validate()

    assert result.valid is True
    assert result.errors == ()


def test_unknown_required_dependency_is_rejected():
    graph = ModuleDependencyGraph(
        (
            contract(
                "sales",
                dependencies=(ModuleDependency("crm"),),
            ),
        )
    )

    result = graph.validate()

    assert result.valid is False
    assert "unknown module 'crm'" in result.errors[0]
    assert "required" in result.errors[0]


def test_unknown_optional_dependency_is_reported():
    graph = ModuleDependencyGraph(
        (
            contract(
                "sales",
                dependencies=(
                    ModuleDependency(
                        "crm",
                        required=False,
                    ),
                ),
            ),
        )
    )

    result = graph.validate()

    assert result.valid is False
    assert "unknown module 'crm'" in result.errors[0]
    assert "optional" in result.errors[0]


def test_direct_circular_dependency_is_rejected():
    graph = ModuleDependencyGraph(
        (
            contract(
                "sales",
                dependencies=(ModuleDependency("crm"),),
            ),
            contract(
                "crm",
                dependencies=(ModuleDependency("sales"),),
            ),
        )
    )

    result = graph.validate()

    assert result.valid is False
    assert any(
        "sales -> crm -> sales" in error
        for error in result.errors
    )


def test_indirect_circular_dependency_is_rejected():
    graph = ModuleDependencyGraph(
        (
            contract(
                "sales",
                dependencies=(ModuleDependency("crm"),),
            ),
            contract(
                "crm",
                dependencies=(ModuleDependency("inventory"),),
            ),
            contract(
                "inventory",
                dependencies=(ModuleDependency("sales"),),
            ),
        )
    )

    result = graph.validate()

    assert result.valid is False
    assert any(
        "sales -> crm -> inventory -> sales" in error
        for error in result.errors
    )


def test_non_circular_dependency_chain_is_valid():
    graph = ModuleDependencyGraph(
        (
            contract(
                "sales",
                dependencies=(ModuleDependency("crm"),),
            ),
            contract(
                "crm",
                dependencies=(ModuleDependency("customer"),),
            ),
            contract("customer"),
        )
    )

    result = graph.validate()

    assert result.valid is True


def test_dependencies_returns_declared_targets():
    graph = ModuleDependencyGraph(
        (
            contract(
                "sales",
                dependencies=(
                    ModuleDependency("crm"),
                    ModuleDependency("inventory"),
                ),
            ),
            contract("crm"),
            contract("inventory"),
        )
    )

    assert graph.dependencies("sales") == (
        "crm",
        "inventory",
    )


def test_missing_module_lookup_is_rejected():
    graph = ModuleDependencyGraph((contract("sales"),))

    with pytest.raises(
        ValueError,
        match="Module contract 'crm' is not registered",
    ):
        graph.get("crm")


def test_duplicate_module_contracts_are_rejected():
    with pytest.raises(
        ValueError,
        match="Duplicate module contract",
    ):
        ModuleDependencyGraph(
            (
                contract("sales"),
                contract("sales"),
            )
        )


def test_require_valid_raises_for_invalid_graph():
    graph = ModuleDependencyGraph(
        (
            contract(
                "sales",
                dependencies=(ModuleDependency("crm"),),
            ),
            contract(
                "crm",
                dependencies=(ModuleDependency("sales"),),
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="Invalid module dependency graph",
    ):
        graph.require_valid()
