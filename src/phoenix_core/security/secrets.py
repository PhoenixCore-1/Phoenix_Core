from abc import ABC, abstractmethod
from typing import Optional


class SecretResolver(ABC):
    """
    Core contract for resolving server-side secrets.

    Implementations may resolve secrets from environment variables,
    deployment secret stores, enterprise vaults, or other secure
    infrastructure.

    Secrets must never be exposed through client-facing APIs, AI
    contracts, module contracts, audit payloads, or normal logging.
    """

    @abstractmethod
    def get_secret(self, name: str) -> Optional[str]:
        """Resolve a secret by its stable name."""
        raise NotImplementedError
