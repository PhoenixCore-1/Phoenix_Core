from abc import ABC, abstractmethod
from typing import Optional

from phoenix_core.ai.contracts import AIRequest, AIResponse
from phoenix_core.ai.providers.contract import AIProvider


class AIProviderAdapter(AIProvider, ABC):
    """
    Base adapter for connecting Phoenix Core AI to an external or
    self-hosted AI provider.

    Provider-specific API details must remain inside concrete adapters.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the stable Phoenix provider identifier."""
        raise NotImplementedError

    @abstractmethod
    def execute(self, request: AIRequest) -> AIResponse:
        """
        Translate and execute a Phoenix AI request using the provider API.
        """
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check provider availability without exposing provider details
        to consuming modules.
        """
        raise NotImplementedError

    def supports_model(self, model: Optional[str]) -> bool:
        """
        Determine whether this adapter supports a requested model.

        Concrete adapters may override this for provider-specific model
        validation.
        """
        return model is None
