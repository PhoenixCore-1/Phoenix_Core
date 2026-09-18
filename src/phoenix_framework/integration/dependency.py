"""Phoenix Generic Framework module dependency resolution."""

from dataclasses import dataclass
from typing import Optional, Tuple

from phoenix_framework.contracts.integration import (
    ModuleDependency,
    ModuleIntegrationContract,
)


@dataclass(frozen=True)
class DependencyResolution:
    """Result of resolving one module dependency."""

    source_module: str
    target_module: str
    compatible: bool
    required: bool = True
    reason: str = ""


class ModuleDependencyResolver:
    """
    Resolves declared module dependencies.

    This component evaluates Framework integration metadata only.
    Phoenix Core remains authoritative for module identity, lifecycle,
    licensing, permissions and access.
    """

    @staticmethod
    def _parse_version(version: str) -> Tuple[int, ...]:
        value = (version or "").strip()

        if not value:
            raise ValueError("Module version cannot be empty.")

        parts = value.split(".")

        try:
            parsed = tuple(int(part) for part in parts)
        except ValueError as exc:
            raise ValueError(
                f"Invalid module version: {version}"
            ) from exc

        if any(part < 0 for part in parsed):
            raise ValueError(
                f"Invalid module version: {version}"
            )

        return parsed

    @staticmethod
    def _find_dependency(
        source: ModuleIntegrationContract,
        target: ModuleIntegrationContract,
    ) -> Optional[ModuleDependency]:
        return next(
            (
                item
                for item in source.dependencies
                if item.module_code == target.module_code
            ),
            None,
        )

    def resolve(
        self,
        source: ModuleIntegrationContract,
        target: ModuleIntegrationContract,
    ) -> DependencyResolution:
        if not source.module_code:
            raise ValueError("Source module code is required.")

        if not target.module_code:
            raise ValueError("Target module code is required.")

        dependency = self._find_dependency(source, target)

        if dependency is None:
            return DependencyResolution(
                source.module_code,
                target.module_code,
                False,
                True,
                "Dependency is not declared by the source module.",
            )

        target_version = self._parse_version(target.version)

        if dependency.minimum_version:
            minimum_version = self._parse_version(
                dependency.minimum_version
            )

            if target_version < minimum_version:
                return DependencyResolution(
                    source.module_code,
                    target.module_code,
                    False,
                    dependency.required,
                    "Target module version is below the minimum required version.",
                )

        if dependency.maximum_version:
            maximum_version = self._parse_version(
                dependency.maximum_version
            )

            if target_version > maximum_version:
                return DependencyResolution(
                    source.module_code,
                    target.module_code,
                    False,
                    dependency.required,
                    "Target module version exceeds the maximum supported version.",
                )

        missing_capabilities = [
            capability
            for capability in dependency.capabilities
            if capability not in target.provided_capabilities
        ]

        if missing_capabilities:
            return DependencyResolution(
                source.module_code,
                target.module_code,
                False,
                dependency.required,
                "Target module does not provide all required capabilities.",
            )

        return DependencyResolution(
            source.module_code,
            target.module_code,
            True,
            dependency.required,
            "Dependency is compatible.",
        )
