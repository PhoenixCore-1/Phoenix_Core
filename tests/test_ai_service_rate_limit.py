from uuid import uuid4

import pytest

from phoenix_core.ai.contracts import AICapability, AIRequest, AIResponse
from phoenix_core.ai.providers.adapter import AIProviderAdapter
from phoenix_core.ai.providers.registry import AIProviderRegistry
from phoenix_core.ai.quota import AIQuotaService
from phoenix_core.ai.rate_limit import AIRateLimitPolicy, AIRateLimitService
from phoenix_core.ai.security import AISecurityService
from phoenix_core.ai.service import AIService
from phoenix_core.ai.usage import AIUsagePolicy
from phoenix_core.ai.usage_tracker import AIUsageTracker
from phoenix_core.security.context import RequestContext


class RateLimitProvider(AIProviderAdapter):
    def __init__(self):
        self.calls = 0

    @property
    def provider_name(self):
        return "rate-limit-test"

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


def context():
    return RequestContext(
        request_id="rate-limit-test",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        permissions=frozenset({"ai.ask"}),
        entitlements=frozenset({"ai"}),
    )


def request():
    return AIRequest(
        capability=AICapability.ASK,
        prompt="rate limit test",
    )


def build():
    provider = RateLimitProvider()
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


def test_rate_limit_blocks_provider_execution():
    service, provider = build()
    ctx = context()

    policy = AIRateLimitPolicy(
        max_requests=1,
        window_seconds=60,
    )

    service.execute(
        ctx,
        request(),
        provider_name="rate-limit-test",
        required_permission="ai.ask",
        required_entitlement="ai",
        rate_limit_policy=policy,
    )

    with pytest.raises(PermissionError, match="rate limit"):
        service.execute(
            ctx,
            request(),
            provider_name="rate-limit-test",
            required_permission="ai.ask",
            required_entitlement="ai",
            rate_limit_policy=policy,
        )

    assert provider.calls == 1


def test_rate_limit_is_tenant_specific():
    service, provider = build()

    ctx1 = context()
    ctx2 = context()

    policy = AIRateLimitPolicy(
        max_requests=1,
        window_seconds=60,
    )

    service.execute(
        ctx1,
        request(),
        provider_name="rate-limit-test",
        required_permission="ai.ask",
        required_entitlement="ai",
        rate_limit_policy=policy,
    )

    service.execute(
        ctx2,
        request(),
        provider_name="rate-limit-test",
        required_permission="ai.ask",
        required_entitlement="ai",
        rate_limit_policy=policy,
    )

    assert provider.calls == 2


def test_rate_limit_is_checked_before_usage_quota():
    service, provider = build()
    ctx = context()

    rate_policy = AIRateLimitPolicy(
        max_requests=1,
        window_seconds=60,
    )

    quota_policy = AIUsagePolicy(
        max_requests=10,
    )

    service.execute(
        ctx,
        request(),
        provider_name="rate-limit-test",
        required_permission="ai.ask",
        required_entitlement="ai",
        rate_limit_policy=rate_policy,
        usage_policy=quota_policy,
    )

    with pytest.raises(PermissionError, match="rate limit"):
        service.execute(
            ctx,
            request(),
            provider_name="rate-limit-test",
            required_permission="ai.ask",
            required_entitlement="ai",
            rate_limit_policy=rate_policy,
            usage_policy=quota_policy,
        )

    assert provider.calls == 1
