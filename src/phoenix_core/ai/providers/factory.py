from typing import Callable, Dict

from phoenix_core.ai.providers.adapter import AIProviderAdapter
from phoenix_core.ai.providers.config import AIProviderConfig


class AIProviderFactory:
    """
    Core-controlled factory for constructing configured AI provider adapters.

    Modules must not construct provider adapters directly.
    """

    def __init__(self) -> None:
        self._builders: Dict[str, Callable[[AIProviderConfig], AIProviderAdapter]] = {}

    def register(
        self,
        provider_name: str,
        builder: Callable[[AIProviderConfig], AIProviderAdapter],
    ) -> None:
        if not provider_name:
            raise ValueError("Provider name cannot be empty")

        if provider_name in self._builders:
            raise ValueError(
                f"AI provider builder already registered: {provider_name}"
            )

        self._builders[provider_name] = builder

    def create(self, config: AIProviderConfig) -> AIProviderAdapter:
        try:
            builder = self._builders[config.provider_name]
        except KeyError as exc:
            raise ValueError(
                f"AI provider builder not registered: {config.provider_name}"
            ) from exc

        return builder(config)

    def has(self, provider_name: str) -> bool:
        return provider_name in self._builders

    def list_providers(self) -> tuple[str, ...]:
        return tuple(sorted(self._builders.keys()))
