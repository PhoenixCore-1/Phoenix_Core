from abc import ABC, abstractmethod
from typing import Optional, Sequence

from phoenix_framework.context import FrameworkContext
from phoenix_framework.contracts.platform import PlatformCapability


class PlatformCapabilityContract(ABC):
    """
    Contract for a reusable Phoenix platform capability.

    The implementation may delegate to Phoenix Core services, but Core
    remains the authoritative owner of the underlying capability.
    """

    @property
    @abstractmethod
    def capability(self) -> PlatformCapability:
        """Return the capability metadata."""
        raise NotImplementedError

    @abstractmethod
    def is_available(self, context: FrameworkContext) -> bool:
        """Determine whether the capability is available in the context."""
        raise NotImplementedError

    @abstractmethod
    def required_permissions(self) -> Sequence[str]:
        """Return permissions required to use the capability."""
        raise NotImplementedError

    @abstractmethod
    def required_entitlements(self) -> Sequence[str]:
        """Return entitlements required to use the capability."""
        raise NotImplementedError
