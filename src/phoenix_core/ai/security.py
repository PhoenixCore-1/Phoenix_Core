from phoenix_core.ai.contracts import AIRequest
from phoenix_core.security.context import RequestContext


class AISecurityService:
    """
    Core-owned security boundary for AI requests.

    Uses the authoritative Phoenix RequestContext for identity,
    organisation, permissions, and entitlements.
    """

    def authorize(
        self,
        context: RequestContext,
        request: AIRequest,
        *,
        required_permission: str,
        required_entitlement: str | None = None,
    ) -> None:
        if context.identity_id is None:
            raise PermissionError("Authenticated identity is required for AI access")

        if context.organisation_id is None:
            raise PermissionError("Organisation context is required for tenant AI access")

        if not context.has_permission(required_permission):
            raise PermissionError(
                f"AI permission required: {required_permission}"
            )

        if (
            required_entitlement is not None
            and not context.has_entitlement(required_entitlement)
        ):
            raise PermissionError(
                f"AI entitlement required: {required_entitlement}"
            )
