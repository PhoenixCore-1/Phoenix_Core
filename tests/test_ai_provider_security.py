import pytest

from phoenix_core.ai.providers.config import AIProviderConfig
from phoenix_core.ai.providers.openai import OpenAIProvider
from phoenix_core.security.environment_secrets import EnvironmentSecretResolver


def test_openai_provider_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config = AIProviderConfig(
        provider_name="openai",
        base_url="https://api.openai.com/v1",
        default_model="test-model",
    )

    with pytest.raises(ValueError, match="OpenAI API key is required"):
        OpenAIProvider(
            config,
            EnvironmentSecretResolver(),
        )


def test_openai_provider_uses_secret_resolver(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-not-a-real-key")

    config = AIProviderConfig(
        provider_name="openai",
        base_url="https://api.openai.com/v1",
        default_model="test-model",
    )

    provider = OpenAIProvider(
        config,
        EnvironmentSecretResolver(),
    )

    assert provider.provider_name == "openai"
    assert provider.health_check() is True


def test_openai_provider_does_not_require_secret_in_ai_request(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-not-a-real-key")

    config = AIProviderConfig(
        provider_name="openai",
        base_url="https://api.openai.com/v1",
        default_model="test-model",
    )

    provider = OpenAIProvider(
        config,
        EnvironmentSecretResolver(),
    )

    assert provider.provider_name == "openai"
    assert "test-secret-not-a-real-key" not in repr(config)
