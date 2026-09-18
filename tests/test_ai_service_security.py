from uuid import uuid4

import pytest

from phoenix_core.ai import (
    AICapability,
    AIProviderRegistry,
    AIRequest,
    AIResponse,
)
from phoenix_core.ai.providers.adapter import AIProviderAdapter
from phoenix_core.ai.security import AISecurityService
from phoenix_core.ai.service import AIService
from phoenix_core.security.context import RequestContext


class RecordingProvider(AIProviderAdapter):
    def __init__(self):
        self.called = False

    @property
    def provider_name(self):
        return "recording"

    def execute(self, request):
        self.called = True
        return AIResponse(
            capability=request.capability,
            content="test",
            provider="recording",
            model="test-model",
        )

    def health_check(self):
        return True


def build_service():
    provider = RecordingProvider()
    registry = AIProviderRegistry()
    registry.register(provider)

    service = AIService(
        registry,
        AISecurityService(),
    )

    return service, provider


def test_unauthorized_request_never_reaches_provider():
    service, provider = build_service()

    context = RequestContext(
        request_id="test",
        identity_id=None,
        organisation_id=None,
    )

    request = AIRequest(
        capability=AICapability.ASK,
        prompt="test",
    )

    with pytest.raises(PermissionError):
        service.execute(
            context,
            request,
            provider_name="recording",
            required_permission="ai.ask",
            required_entitlement="ai",
        )

    assert provider.called is False


def test_authorized_request_reaches_provider():
    service, provider = build_service()

    context = RequestContext(
        request_id="test",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        permissions=frozenset({"ai.ask"}),
        entitlements=frozenset({"ai"}),
    )

    request = AIRequest(
        capability=AICapability.ASK,
        prompt="test",
    )

    response = service.execute(
        context,
        request,
        provider_name="recording",
        required_permission="ai.ask",
        required_entitlement="ai",
    )

    assert provider.called is True
    assert response.content == "test"
    assert response.provider == "recording"
