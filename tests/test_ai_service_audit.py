from uuid import uuid4

import pytest

from phoenix_core.ai.audit import AIAuditService
from phoenix_core.ai.contracts import AICapability, AIRequest, AIResponse
from phoenix_core.ai.providers.adapter import AIProviderAdapter
from phoenix_core.ai.providers.registry import AIProviderRegistry
from phoenix_core.ai.quota import AIQuotaService
from phoenix_core.ai.rate_limit import AIRateLimitPolicy, AIRateLimitService
from phoenix_core.ai.security import AISecurityService
from phoenix_core.ai.service import AIService
from phoenix_core.ai.usage import AIUsagePolicy
from phoenix_core.ai.usage_tracker import AIUsageTracker
from phoenix_core.audit.service import AuditService
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.security.context import RequestContext


class AuditProvider(AIProviderAdapter):
    def __init__(self, fail=False):
        self.fail = fail

    @property
    def provider_name(self):
        return "audit-test"

    def execute(self, request):
        if self.fail:
            raise RuntimeError("provider failure")

        return AIResponse(
            capability=request.capability,
            content="audit-success",
            provider=self.provider_name,
            model="test-model",
        )

    def health_check(self):
        return True


def setup(fail=False):
    db = SQLiteDatabase(":memory:")

    db.execute(
        "CREATE TABLE organisations (id TEXT PRIMARY KEY)"
    )
    db.execute(
        "CREATE TABLE identities (id TEXT PRIMARY KEY)"
    )
    db.execute(
        """
        CREATE TABLE audit_events (
            id TEXT PRIMARY KEY,
            organisation_id TEXT,
            identity_id TEXT,
            action TEXT NOT NULL,
            target_type TEXT,
            target_id TEXT,
            request_id TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    organisation_id = uuid4()
    identity_id = uuid4()

    db.execute(
        "INSERT INTO organisations (id) VALUES (?)",
        (str(organisation_id),),
    )
    db.execute(
        "INSERT INTO identities (id) VALUES (?)",
        (str(identity_id),),
    )
    db.commit()

    context = RequestContext(
        request_id="ai-service-audit-test",
        identity_id=identity_id,
        organisation_id=organisation_id,
        permissions=frozenset({"ai.ask"}),
        entitlements=frozenset({"ai"}),
    )

    provider = AuditProvider(fail=fail)
    registry = AIProviderRegistry()
    registry.register(provider)

    tracker = AIUsageTracker()
    core_audit = AuditService(db)

    service = AIService(
        registry,
        AISecurityService(),
        quota_service=AIQuotaService(tracker),
        usage_tracker=tracker,
        rate_limit_service=AIRateLimitService(),
        audit_service=AIAuditService(core_audit),
    )

    request = AIRequest(
        capability=AICapability.ASK,
        prompt="audit test",
    )

    return service, context, request, core_audit


def actions(audit, organisation_id):
    return [
        event.action
        for event in audit.list(
            organisation_id=organisation_id
        )
    ]


def test_successful_ai_execution_is_audited():
    service, context, request, audit = setup()

    response = service.execute(
        context,
        request,
        provider_name="audit-test",
        required_permission="ai.ask",
        required_entitlement="ai",
    )

    assert response.content == "audit-success"

    recorded = actions(audit, context.organisation_id)

    assert "AI_REQUESTED" in recorded
    assert "AI_COMPLETED" in recorded
    assert "AI_FAILED" not in recorded


def test_provider_failure_is_audited_as_failure():
    service, context, request, audit = setup(fail=True)

    with pytest.raises(RuntimeError, match="provider failure"):
        service.execute(
            context,
            request,
            provider_name="audit-test",
            required_permission="ai.ask",
            required_entitlement="ai",
        )

    recorded = actions(audit, context.organisation_id)

    assert "AI_REQUESTED" in recorded
    assert "AI_FAILED" in recorded
    assert "AI_COMPLETED" not in recorded


def test_rate_limit_is_audited_without_generic_failure():
    service, context, request, audit = setup()

    policy = AIRateLimitPolicy(
        max_requests=1,
        window_seconds=60,
    )

    service.execute(
        context,
        request,
        provider_name="audit-test",
        required_permission="ai.ask",
        required_entitlement="ai",
        rate_limit_policy=policy,
    )

    with pytest.raises(PermissionError, match="rate limit"):
        service.execute(
            context,
            request,
            provider_name="audit-test",
            required_permission="ai.ask",
            required_entitlement="ai",
            rate_limit_policy=policy,
        )

    recorded = actions(audit, context.organisation_id)

    assert recorded.count("AI_RATE_LIMITED") == 1
    assert recorded.count("AI_COMPLETED") == 1
    assert recorded.count("AI_FAILED") == 0


def test_quota_exceeded_is_audited_without_generic_failure():
    service, context, request, audit = setup()

    policy = AIUsagePolicy(
        max_requests=0,
    )

    with pytest.raises(PermissionError, match="request quota"):
        service.execute(
            context,
            request,
            provider_name="audit-test",
            required_permission="ai.ask",
            required_entitlement="ai",
            usage_policy=policy,
        )

    recorded = actions(audit, context.organisation_id)

    assert "AI_REQUESTED" in recorded
    assert "AI_QUOTA_EXCEEDED" in recorded
    assert "AI_FAILED" not in recorded
