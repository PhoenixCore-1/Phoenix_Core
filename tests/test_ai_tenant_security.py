from uuid import uuid4

import pytest

from phoenix_core.ai import AICapability, AIRequest
from phoenix_core.ai.providers.registry import AIProviderRegistry
from phoenix_core.ai.security import AISecurityService
from phoenix_core.ai.service import AIService
from phoenix_core.security.context import RequestContext


class TenantRecordingProvider:
    provider_name = "tenant-test"
    called = False

    def supports_model(self, model):
        return True

    def execute(self, request):
        self.called = True
        raise AssertionError("Provider must not be reached")


def test_ai_requires_tenant_context():
    provider = TenantRecordingProvider()
    registry = AIProviderRegistry()
    registry.register(provider)

    service = AIService(registry, AISecurityService())

    context = RequestContext(
        request_id="tenant-test",
        identity_id=uuid4(),
        organisation_id=None,
        permissions=frozenset({"ai.ask"}),
        entitlements=frozenset({"ai"}),
    )

    request = AIRequest(
        capability=AICapability.ASK,
        prompt="test",
    )

    with pytest.raises(PermissionError, match="Organisation context"):
        service.execute(
            context,
            request,
            provider_name="tenant-test",
            required_permission="ai.ask",
            required_entitlement="ai",
        )

    assert provider.called is False


def test_ai_requires_identity_and_tenant_together():
    provider = TenantRecordingProvider()
    registry = AIProviderRegistry()
    registry.register(provider)

    service = AIService(registry, AISecurityService())

    context = RequestContext(
        request_id="tenant-test",
        identity_id=None,
        organisation_id=uuid4(),
        permissions=frozenset({"ai.ask"}),
        entitlements=frozenset({"ai"}),
    )

    request = AIRequest(
        capability=AICapability.ASK,
        prompt="test",
    )

    with pytest.raises(PermissionError, match="Authenticated identity"):
        service.execute(
            context,
            request,
            provider_name="tenant-test",
            required_permission="ai.ask",
            required_entitlement="ai",
        )

    assert provider.called is False
