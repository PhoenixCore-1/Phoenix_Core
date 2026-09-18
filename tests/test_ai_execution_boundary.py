import pytest

from phoenix_core.ai import AICapability, AIRequest, AIResponse
from phoenix_core.ai.providers.adapter import AIProviderAdapter
from phoenix_core.ai.providers.registry import AIProviderRegistry
from phoenix_core.ai.security import AISecurityService
from phoenix_core.ai.service import AIService
from phoenix_core.security.context import RequestContext


class ExecutionProvider(AIProviderAdapter):
    def __init__(self):
        self.received_request = None

    @property
    def provider_name(self):
        return "execution-test"

    def execute(self, request):
        self.received_request = request
        return AIResponse(
            capability=request.capability,
            content="execution-success",
            provider=self.provider_name,
            model=request.model or "default-model",
        )

    def health_check(self):
        return True

    def supports_model(self, model):
        return model in (None, "supported-model")


def authorized_context():
    return RequestContext(
        request_id="execution-test",
        identity_id=__import__("uuid").uuid4(),
        organisation_id=__import__("uuid").uuid4(),
        permissions=frozenset({"ai.ask"}),
        entitlements=frozenset({"ai"}),
    )


def build_service():
    provider = ExecutionProvider()
    registry = AIProviderRegistry()
    registry.register(provider)

    return AIService(
        registry,
        AISecurityService(),
    ), provider


def test_ai_service_resolves_and_executes_provider():
    service, provider = build_service()

    request = AIRequest(
        capability=AICapability.ASK,
        prompt="test execution",
        model="supported-model",
    )

    response = service.execute(
        authorized_context(),
        request,
        provider_name="execution-test",
        required_permission="ai.ask",
        required_entitlement="ai",
    )

    assert response.content == "execution-success"
    assert response.provider == "execution-test"
    assert provider.received_request is request


def test_unsupported_model_is_rejected_before_provider_execution():
    service, provider = build_service()

    request = AIRequest(
        capability=AICapability.ASK,
        prompt="test model",
        model="unsupported-model",
    )

    with pytest.raises(
        ValueError,
        match="does not support requested model",
    ):
        service.execute(
            authorized_context(),
            request,
            provider_name="execution-test",
            required_permission="ai.ask",
            required_entitlement="ai",
        )

    assert provider.received_request is None


def test_unknown_provider_is_rejected():
    service, _ = build_service()

    request = AIRequest(
        capability=AICapability.ASK,
        prompt="test provider",
    )

    with pytest.raises(ValueError, match="AI provider not registered"):
        service.execute(
            authorized_context(),
            request,
            provider_name="does-not-exist",
            required_permission="ai.ask",
            required_entitlement="ai",
        )


def test_ai_service_does_not_execute_business_actions():
    service, provider = build_service()

    request = AIRequest(
        capability=AICapability.PROPOSE_ACTION,
        prompt="propose a business action",
    )

    response = service.execute(
        authorized_context(),
        request,
        provider_name="execution-test",
        required_permission="ai.ask",
        required_entitlement="ai",
    )

    assert provider.received_request is request
    assert response.content == "execution-success"
    assert not hasattr(service, "execute_business_action")
