from phoenix_core.ai.providers.config import AIProviderConfig
from phoenix_core.ai.providers.openai import OpenAIProvider
from phoenix_core.ai.providers.registry import AIProviderRegistry
from phoenix_core.ai.providers.factory import AIProviderFactory
from phoenix_core.security.secrets import SecretResolver


def register_openai_provider(
    factory: AIProviderFactory,
    registry: AIProviderRegistry,
    config: AIProviderConfig,
    secret_resolver: SecretResolver,
) -> None:
    """
    Register the OpenAI provider through the Core AI provider boundary.

    Provider construction remains a Core concern. Business modules must
    not construct OpenAIProvider instances directly.
    """

    factory.register(
        "openai",
        lambda provider_config: OpenAIProvider(
            provider_config,
            secret_resolver,
        ),
    )

    provider = factory.create(config)
    registry.register(provider)
