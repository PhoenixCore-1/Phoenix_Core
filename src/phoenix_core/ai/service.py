from phoenix_core.ai.audit import AIAuditService
from phoenix_core.ai.contracts import AIRequest, AIResponse
from phoenix_core.ai.providers.registry import AIProviderRegistry
from phoenix_core.ai.quota import AIQuotaService
from phoenix_core.ai.rate_limit import AIRateLimitPolicy, AIRateLimitService
from phoenix_core.ai.security import AISecurityService
from phoenix_core.ai.usage import AIUsagePolicy
from phoenix_core.ai.usage_tracker import AIUsageTracker
from phoenix_core.security.context import RequestContext


class AIService:
    """Authoritative Core AI execution boundary."""

    def __init__(
        self,
        provider_registry: AIProviderRegistry,
        security_service: AISecurityService,
        quota_service: AIQuotaService | None = None,
        usage_tracker: AIUsageTracker | None = None,
        rate_limit_service: AIRateLimitService | None = None,
        audit_service: AIAuditService | None = None,
    ):
        self.provider_registry = provider_registry
        self.security_service = security_service
        self.quota_service = quota_service
        self.usage_tracker = usage_tracker
        self.rate_limit_service = rate_limit_service
        self.audit_service = audit_service

    def execute(
        self,
        context: RequestContext,
        request: AIRequest,
        *,
        provider_name: str,
        required_permission: str,
        required_entitlement: str | None = None,
        usage_policy: AIUsagePolicy | None = None,
        rate_limit_policy: AIRateLimitPolicy | None = None,
    ) -> AIResponse:
        self.security_service.authorize(
            context,
            request,
            required_permission=required_permission,
            required_entitlement=required_entitlement,
        )

        if not provider_name or not provider_name.strip():
            raise ValueError("AI provider name is required")

        if context.organisation_id is None:
            raise PermissionError(
                "Organisation context is required for AI execution"
            )

        organisation_id = str(context.organisation_id)

        if self.audit_service is not None:
            self.audit_service.request_started(context)

        if (
            rate_limit_policy is not None
            and self.rate_limit_service is not None
        ):
            try:
                self.rate_limit_service.check_request(
                    organisation_id,
                    rate_limit_policy,
                )
            except PermissionError:
                if self.audit_service is not None:
                    self.audit_service.rate_limited(context)
                raise

        if (
            usage_policy is not None
            and self.quota_service is not None
        ):
            try:
                self.quota_service.check_request(
                    organisation_id,
                    usage_policy,
                )
            except PermissionError:
                if self.audit_service is not None:
                    self.audit_service.quota_exceeded(context)
                raise

        try:
            provider = self.provider_registry.get(provider_name.strip())

            if not provider.supports_model(request.model):
                raise ValueError(
                    "AI provider does not support requested model: "
                    f"{request.model}"
                )

            response = provider.execute(request)

            if self.usage_tracker is not None:
                self.usage_tracker.record(
                    organisation_id,
                    response.usage,
                )

            if self.audit_service is not None:
                self.audit_service.request_completed(context)

            return response

        except Exception:
            if self.audit_service is not None:
                self.audit_service.request_failed(context)
            raise
