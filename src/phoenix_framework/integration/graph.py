"""Phoenix Generic Framework module dependency graph validation."""

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from phoenix_framework.contracts.integration import ModuleIntegrationContract


@dataclass(frozen=True)
class DependencyGraphResult:
    """Result of validating the complete module dependency graph."""

    valid: bool
    errors: Tuple[str, ...] = ()


class ModuleDependencyGraph:
    """
    Validates the dependency graph declared by module integration contracts.

    This component evaluates Framework integration metadata only.
    Phoenix Core remains authoritative for module identity, lifecycle,
    licensing, permissions and access.
    """

    def __init__(
        self,
        contracts: Iterable[ModuleIntegrationContract],
    ):
        self._contracts: Dict[str, ModuleIntegrationContract] = {}

        for contract in contracts:
            if contract.module_code in self._contracts:
                raise ValueError(
                    f"Duplicate module contract: '{contract.module_code}'."
                )

            self._contracts[contract.module_code] = contract

    def get(self, module_code: str) -> ModuleIntegrationContract:
        key = (module_code or "").strip()

        if not key:
            raise ValueError("module_code is required.")

        try:
            return self._contracts[key]
        except KeyError as exc:
            raise ValueError(
                f"Module contract '{key}' is not registered."
            ) from exc

    def dependencies(
        self,
        module_code: str,
    ) -> Tuple[str, ...]:
        contract = self.get(module_code)

        return tuple(
            dependency.module_code
            for dependency in contract.dependencies
        )

    def validate(self) -> DependencyGraphResult:
        errors = []

        # Validate that every declared dependency points to a known
        # integration contract.
        for module_code in sorted(self._contracts):
            contract = self._contracts[module_code]

            for dependency in contract.dependencies:
                if dependency.module_code not in self._contracts:
                    qualifier = (
                        "required"
                        if dependency.required
                        else "optional"
                    )

                    errors.append(
                        f"Module '{module_code}' declares {qualifier} "
                        f"dependency on unknown module "
                        f"'{dependency.module_code}'."
                    )

        # Detect circular dependencies independently of the missing-target
        # validation so every graph problem is reported deterministically.
        for module_code in sorted(self._contracts):
            cycle = self._find_cycle(module_code)

            if cycle:
                errors.append(
                    "Circular module dependency detected: "
                    + " -> ".join(cycle)
                )

        return DependencyGraphResult(
            valid=not errors,
            errors=tuple(dict.fromkeys(errors)),
        )

    def require_valid(self) -> None:
        result = self.validate()

        if not result.valid:
            raise ValueError(
                "Invalid module dependency graph: "
                + " | ".join(result.errors)
            )

    def _find_cycle(self, start: str) -> Tuple[str, ...]:
        visiting = []
        visited = set()

        def visit(module_code: str) -> Tuple[str, ...]:
            if module_code in visiting:
                index = visiting.index(module_code)
                return tuple(
                    visiting[index:] + [module_code]
                )

            if module_code in visited:
                return ()

            visited.add(module_code)
            visiting.append(module_code)

            contract = self._contracts[module_code]

            for dependency in sorted(
                contract.dependencies,
                key=lambda item: item.module_code,
            ):
                target = dependency.module_code

                if target not in self._contracts:
                    continue

                cycle = visit(target)

                if cycle:
                    return cycle

            visiting.pop()
            return ()

        return visit(start)
