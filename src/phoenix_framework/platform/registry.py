from typing import Dict, List

from phoenix_framework.contracts import PlatformCapability
from phoenix_framework.contracts.capability import PlatformCapabilityContract


class CapabilityRegistry:
    """
    Runtime registry for generic Phoenix platform capabilities.

    The registry does not own the underlying capability authority.
    """

    def __init__(self) -> None:
        self._capabilities: Dict[str, PlatformCapabilityContract] = {}

    def register(self, capability: PlatformCapabilityContract) -> None:
        code = capability.capability.code

        if code in self._capabilities:
            raise ValueError(f"Capability already registered: {code}")

        self._capabilities[code] = capability

    def get(self, code: str) -> PlatformCapabilityContract:
        try:
            return self._capabilities[code]
        except KeyError:
            raise ValueError(f"Capability not registered: {code}") from None

    def has(self, code: str) -> bool:
        return code in self._capabilities

    def list(self) -> List[PlatformCapabilityContract]:
        return list(self._capabilities.values())

    def clear(self) -> None:
        self._capabilities.clear()
