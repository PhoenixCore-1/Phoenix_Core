from abc import ABC, abstractmethod
from typing import Optional

from phoenix_core.ai.contracts import AIRequest, AIResponse, AIError


class AIProvider(ABC):
    """
    Provider-neutral contract for AI execution.

    Concrete providers must implement this contract without exposing
    provider-specific behaviour to Phoenix modules.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the stable provider identifier."""
        raise NotImplementedError

    @abstractmethod
    def execute(self, request: AIRequest) -> AIResponse:
        """
        Execute a synchronous AI request.

        Provider adapters are responsible for translating the Phoenix
        request contract into the provider-specific API format and
        translating the provider response back into AIResponse.
        """
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> bool:
        """
        Determine whether the provider is currently available.
        """
        raise NotImplementedError

    def supports_model(self, model: Optional[str]) -> bool:
        """
        Determine whether this provider supports the requested model.

        Providers may override this when model-level capability discovery
        is required.
        """
        return model is None
