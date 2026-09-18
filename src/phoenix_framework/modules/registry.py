from typing import Dict, List

from phoenix_framework.contracts import ModuleContract


class ModuleRegistry:
    """
    Runtime registry for Generic Framework module contracts.

    This is a discovery/registration mechanism only. Phoenix Core remains
    authoritative for module identity, lifecycle, licensing and access.
    """

    def __init__(self) -> None:
        self._modules: Dict[str, ModuleContract] = {}

    def register(self, module: ModuleContract) -> None:
        if module.code in self._modules:
            raise ValueError(f"Module already registered: {module.code}")

        self._modules[module.code] = module

    def get(self, code: str) -> ModuleContract:
        try:
            return self._modules[code]
        except KeyError:
            raise ValueError(f"Module not registered: {code}") from None

    def has(self, code: str) -> bool:
        return code in self._modules

    def list(self) -> List[ModuleContract]:
        return list(self._modules.values())

    def clear(self) -> None:
        self._modules.clear()
