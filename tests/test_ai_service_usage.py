from phoenix_core.ai.contracts import AIRequest, AIResponse, AIUsage
from phoenix_core.ai.providers.adapter import AIProviderAdapter
from phoenix_core.ai.providers.registry import AIProviderRegistry
from phoenix_core.ai.quota import AIQuotaService
from phoenix_core.ai.security import AISecurityService
from phoenix_core.ai.service import AIService
from phoenix_core.ai.usage import AIUsagePolicy
from phoenix_core.ai.usage_tracker import AIUsageTracker
from phoenix_core.security.context import RequestContext


class UsageProvider(AIProviderAdapter):
    def __init__(self):
        self.called = False

    @property
    def provider_name(self):
        return "usage-test"

    def execute(self, request):
        self.called = True
        return AIResponse(
            capability=request.capability,
            content="usage-success",
            provider=self.provider_name,
            model="test-model",
            usage=AIUsage(
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                estimated_cost=0.25,
                currency="USD",
            ),
        )

    def health_check(self):
        return True


def context():
    return RequestContext(
        request_id="usage-test",
        identity_id=__import__("uuid").uuid4(),
        organisation_id=__import__("uuid").uuid4(),
        permissions=frozenset({"ai.ask"}),
        entitlements=frozenset({"ai"}),
    )


def request():
    return AIRequest(
        capability=__import__(
            "phoenix_core.ai.contracts",
            fromlist=["AICapability"],
        ).AICapability.ASK,
        prompt="usage test",
    )


def build():
    provider = UsageProvider()
    registry = AIProviderRegistry()
    registry.register(provider)

    tracker = AIUsageTracker()
    quota = AIQuotaService(tracker)

    service = AIService(
        registry,
        AISecurityService(),
        quota_service=quota,
        usage_tracker=tracker,
    )

    return service, provider, tracker


def test_quota_is_checked_before_provider_execution():
    service, provider, tracker = build()

    org_id = str(context().organisation_id)

    tracker.record(
        org_id,
        AIUsage(
            total_tokens=150,
        ),
    )

    ctx = RequestContext(
        request_id="quota-test",
        identity_id=__import__("uuid").uuid4(),
        organisation_id=__import__("uuid").UUID(org_id),
        permissions=frozenset({"ai.ask"}),
        entitlements=frozenset({"ai"}),
    )

    with __import__("pytest").raises(
        PermissionError,
        match="total token quota",
    ):
        service.execute(
            ctx,
            request(),
            provider_name="usage-test",
            required_permission="ai.ask",
            required_entitlement="ai",
            usage_policy=AIUsagePolicy(max_total_tokens=150),
        )

    assert provider.called is False


def test_successful_execution_records_usage():
    service, provider, tracker = build()

    ctx = context()

    response = service.execute(
        ctx,
        request(),
        provider_name="usage-test",
        required_permission="ai.ask",
        required_entitlement="ai",
        usage_policy=AIUsagePolicy(max_total_tokens=1000),
    )

    usage = tracker.get(str(ctx.organisation_id))

    assert provider.called is True
    assert response.content == "usage-success"
    assert usage.requests == 1
    assert usage.input_tokens == 100
    assert usage.output_tokens == 50
    assert usage.total_tokens == 150
    assert usage.estimated_cost == 0.25


def test_usage_is_not_recorded_when_provider_fails():
    class FailingProvider(UsageProvider):
        def execute(self, request):
            self.called = True
            raise RuntimeError("provider failure")

    provider = FailingProvider()
    registry = AIProviderRegistry()
    registry.register(provider)

    tracker = AIUsageTracker()
    quota = AIQuotaService(tracker)

    service = AIService(
        registry,
        AISecurityService(),
        quota_service=quota,
        usage_tracker=tracker,
    )

    ctx = context()

    with __import__("pytest").raises(RuntimeError, match="provider failure"):
        service.execute(
            ctx,
            request(),
            provider_name="usage-test",
            required_permission="ai.ask",
            required_entitlement="ai",
            usage_policy=AIUsagePolicy(max_requests=10),
        )

    usage = tracker.get(str(ctx.organisation_id))

    assert provider.called is True
    assert usage.requests == 0
    assert usage.total_tokens == 0
