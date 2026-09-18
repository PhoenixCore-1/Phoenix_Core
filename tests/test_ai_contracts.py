from phoenix_core.ai import (
    AICapability,
    AIActionRequest,
    AIContext,
    AIError,
    AIProvider,
    AIProviderRegistry,
    AIRequest,
    AIRequestMode,
    AIResponse,
    AIUsage,
)


class TestProvider(AIProvider):
    @property
    def provider_name(self) -> str:
        return "test-provider"

    def execute(self, request: AIRequest) -> AIResponse:
        return AIResponse(
            capability=request.capability,
            content="test response",
            provider=self.provider_name,
            model=request.model or "test-model",
        )

    def health_check(self) -> bool:
        return True


def test_capabilities_are_provider_neutral():
    assert AICapability.ASK.value == "ask"
    assert AICapability.SUMMARIZE.value == "summarize"
    assert AICapability.GENERATE.value == "generate"
    assert AICapability.PROPOSE_ACTION.value == "propose_action"


def test_ai_request_contract():
    request = AIRequest(
        capability=AICapability.SUMMARIZE,
        prompt="Summarize this information",
        context=AIContext(
            items={"customer_id": "C001"}
        ),
        mode=AIRequestMode.SYNC,
    )

    assert request.capability == AICapability.SUMMARIZE
    assert request.prompt == "Summarize this information"
    assert request.context.items["customer_id"] == "C001"
    assert request.mode == AIRequestMode.SYNC


def test_ai_action_request_is_provider_neutral():
    action = AIActionRequest(
        action_type="create_quote",
        parameters={"amount": 1000},
        target_type="customer",
        target_id="C001",
    )

    assert action.action_type == "create_quote"
    assert action.parameters["amount"] == 1000
    assert action.target_id == "C001"


def test_ai_response_contract():
    response = AIResponse(
        capability=AICapability.ASK,
        content="Test response",
        provider="test-provider",
        model="test-model",
        usage=AIUsage(
            input_tokens=10,
            output_tokens=20,
            total_tokens=30,
        ),
    )

    assert response.content == "Test response"
    assert response.provider == "test-provider"
    assert response.usage.total_tokens == 30


def test_provider_registry():
    registry = AIProviderRegistry()
    provider = TestProvider()

    registry.register(provider)

    assert registry.has("test-provider")
    assert registry.get("test-provider") is provider
    assert registry.list_providers() == ("test-provider",)


def test_provider_execution_contract():
    provider = TestProvider()

    request = AIRequest(
        capability=AICapability.ASK,
        prompt="Hello Phoenix",
    )

    response = provider.execute(request)

    assert response.content == "test response"
    assert response.provider == "test-provider"
    assert provider.health_check() is True


def test_provider_registry_rejects_duplicates():
    registry = AIProviderRegistry()
    provider = TestProvider()

    registry.register(provider)

    try:
        registry.register(provider)
        assert False, "Duplicate provider registration should fail"
    except ValueError as exc:
        assert "already registered" in str(exc)


def test_provider_registry_rejects_unknown_provider():
    registry = AIProviderRegistry()

    try:
        registry.get("unknown-provider")
        assert False, "Unknown provider lookup should fail"
    except ValueError as exc:
        assert "not registered" in str(exc)
