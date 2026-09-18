"""Generic external-module registration boundary for Phoenix Framework."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from phoenix_framework.contracts import (
    ModuleContract,
    ModuleIntegrationContract,
    NavigationContract,
)
from phoenix_framework.modules.registry import ModuleRegistry
from phoenix_framework.navigation.registry import NavigationRegistry


@dataclass(frozen=True)
class ModuleRegistrationBundle:
    """Contracts supplied by an external business module."""

    module: ModuleContract
    integration: ModuleIntegrationContract
    navigation: Tuple[NavigationContract, ...] = ()


def register_module(
    bundle: ModuleRegistrationBundle,
    module_registry: ModuleRegistry,
    navigation_registry: NavigationRegistry,
) -> None:
    """Register an external module without creating a Core-to-module dependency."""
    if bundle.module.code != bundle.integration.module_code:
        raise ValueError("Module and integration contract codes must match")
    if bundle.module.version != bundle.integration.version:
        raise ValueError("Module and integration contract versions must match")

    module_registry.register(bundle.module)
    try:
        for navigation in bundle.navigation:
            if navigation.module_code != bundle.module.code:
                raise ValueError("Navigation contract belongs to a different module")
            navigation_registry.register(navigation)
    except Exception:
        # Keep registration atomic when navigation registration fails.
        module_registry.clear()
        raise
