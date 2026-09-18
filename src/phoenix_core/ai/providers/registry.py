from typing import Dict

from phoenix_core.ai.providers.contract import AIProvider


class AIProviderRegistry:
    """
    Authoritative registry for Phoenix Core AI providers.

    Provider registration and lookup remain inside Core AI infrastructure.
    Business modules must not manage provider instances directly.
    """

    def __init__(self) -> None:
        self._providers: Dict[str, AIProvider] = {}

    def register(self, provider: AIProvider) -> None:
        name = provider.provider_name

        if not name:
            raise ValueError("AI provider name cannot be empty")

        if name in self._providers:
            raise ValueError(f"AI provider already registered: {name}")

        self._providers[name] = provider

    def get(self, provider_name: str) -> AIProvider:
        try:
            return self._providers[provider_name]
        except KeyError as exc:
            raise ValueError(
                f"AI provider not registered: {provider_name}"
            ) from exc

    def has(self, provider_name: str) -> bool:
        return provider_name in self._providers

    def list_providers(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers.keys()))

    def clear(self) -> None:
        self._providers.clear()
