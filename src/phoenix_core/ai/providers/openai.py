from openai import OpenAI

from phoenix_core.ai.contracts import (
    AIRequest,
    AIResponse,
    AIUsage,
)
from phoenix_core.ai.providers.adapter import AIProviderAdapter
from phoenix_core.ai.providers.config import AIProviderConfig
from phoenix_core.security.secrets import SecretResolver


class OpenAIProvider(AIProviderAdapter):
    """
    Phoenix Core adapter for the OpenAI API.

    Provider-specific API behaviour remains isolated here.
    Credentials are resolved through the Core SecretResolver.
    """

    def __init__(
        self,
        config: AIProviderConfig,
        secret_resolver: SecretResolver,
        secret_name: str = "OPENAI_API_KEY",
    ) -> None:
        self.config = config
        self.secret_name = secret_name

        if not secret_name or not secret_name.strip():
            raise ValueError("OpenAI secret name cannot be empty")

        api_key = secret_resolver.get_secret(secret_name)

        if not api_key:
            raise ValueError("OpenAI API key is required")

        self.client = OpenAI(
            api_key=api_key,
            base_url=config.base_url,
            timeout=config.timeout_seconds,
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    def execute(self, request: AIRequest) -> AIResponse:
        model = request.model or self.config.default_model

        if not model:
            raise ValueError("No OpenAI model configured")

        response = self.client.responses.create(
            model=model,
            input=request.prompt,
        )

        usage = None

        if getattr(response, "usage", None):
            usage = AIUsage(
                input_tokens=getattr(response.usage, "input_tokens", None),
                output_tokens=getattr(response.usage, "output_tokens", None),
                total_tokens=getattr(response.usage, "total_tokens", None),
            )

        content = getattr(response, "output_text", "")

        return AIResponse(
            capability=request.capability,
            content=content,
            provider=self.provider_name,
            model=model,
            usage=usage,
        )

    def health_check(self) -> bool:
        return True

    def supports_model(self, model: str | None) -> bool:
        if model is None:
            return True

        configured = self.config.default_model

        return configured is None or model == configured
