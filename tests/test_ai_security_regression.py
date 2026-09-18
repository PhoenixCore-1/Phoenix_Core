from uuid import uuid4

import pytest

from phoenix_core.ai.action_service import AIActionService
from phoenix_core.ai.contracts import AICapability, AIActionRequest, AIRequest, AIResponse
from phoenix_core.ai.providers.adapter import AIProviderAdapter
from phoenix_core.ai.providers.registry import AIProviderRegistry
from phoenix_core.ai.quota import AIQuotaService
from phoenix_core.ai.rate_limit import AIRateLimitPolicy, AIRateLimitService
from phoenix_core.ai.security import AISecurityService
from phoenix_core.ai.service import AIService
from phoenix_core.ai.usage import AIUsagePolicy
from phoenix_core.ai.usage_tracker import AIUsageTracker
from phoenix_core.security.context import RequestContext


class SecurityProvider(AIProviderAdapter):
    def __init__(self):
        self.calls = 0

    @property
    def provider_name(self):
        return "security-test"

    def execute(self, request):
        self.calls += 1
        return AIResponse(
            capability=request.capability,
            content="success",
            provider=self.provider_name,
            model="test-model",
        )

    def health_check(self):
        return True


def context(
    *,
    identity=True,
    organisation=True,
    permission=True,
    entitlement=True,
):
    return RequestContext(
        request_id="security-regression",
        identity_id=uuid4() if identity else None,
        organisation_id=uuid4() if organisation else None,
        permissions=frozenset({"ai.ask"}) if permission else frozenset(),
        entitlements=frozenset({"ai"}) if entitlement else frozenset(),
    )


def build():
    provider = SecurityProvider()
    registry = AIProviderRegistry()
    registry.register(provider)

    tracker = AIUsageTracker()

    service = AIService(
        registry,
        AISecurityService(),
        quota_service=AIQuotaService(tracker),
        usage_tracker=tracker,
        rate_limit_service=AIRateLimitService(),
    )

    return service, provider


def request():
    return AIRequest(
        capability=AICapability.ASK,
        prompt="security test",
    )


def execute(service, ctx, **kwargs):
    return service.execute(
        ctx,
        request(),
        provider_name="security-test",
        required_permission="ai.ask",
        required_entitlement="ai",
        **kwargs,
    )


def test_missing_identity_blocks_provider():
    service, provider = build()

    with pytest.raises(PermissionError, match="Authenticated identity"):
        execute(
            service,
            context(identity=False),
        )

    assert provider.calls == 0


def test_missing_tenant_blocks_provider():
    service, provider = build()

    with pytest.raises(PermissionError, match="Organisation context"):
        execute(
            service,
            context(organisation=False),
        )

    assert provider.calls == 0


def test_missing_permission_blocks_provider():
    service, provider = build()

    with pytest.raises(PermissionError, match="AI permission"):
        execute(
            service,
            context(permission=False),
        )

    assert provider.calls == 0


def test_missing_entitlement_blocks_provider():
    service, provider = build()

    with pytest.raises(PermissionError, match="AI entitlement"):
        execute(
            service,
            context(entitlement=False),
        )

    assert provider.calls == 0


def test_rate_limit_blocks_provider():
    service, provider = build()
    ctx = context()

    policy = AIRateLimitPolicy(
        max_requests=1,
        window_seconds=60,
    )

    execute(
        service,
        ctx,
        rate_limit_policy=policy,
    )

    with pytest.raises(PermissionError, match="rate limit"):
        execute(
            service,
            ctx,
            rate_limit_policy=policy,
        )

    assert provider.calls == 1


def test_quota_blocks_provider():
    service, provider = build()
    ctx = context()

    policy = AIUsagePolicy(
        max_requests=0,
    )

    with pytest.raises(PermissionError, match="request quota"):
        execute(
            service,
            ctx,
            usage_policy=policy,
        )

    assert provider.calls == 0


def test_action_authorization_does_not_execute_business_action():
    service = AIActionService()

    action = AIActionRequest(
        action_type="create_production_order",
        parameters={"quantity": 10},
    )

    result = service.authorize_proposal(
        context(),
        action,
        required_permission="ai.ask",
        required_entitlement="ai",
    )

    assert result is action
    assert not hasattr(service, "execute_action")
    assert not hasattr(service, "execute_business_action")
