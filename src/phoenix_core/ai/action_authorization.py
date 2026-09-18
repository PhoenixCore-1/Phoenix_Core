from phoenix_core.ai.contracts import AIActionRequest
from phoenix_core.security.context import RequestContext


class AIActionAuthorizationService:
    """Authorizes AI-proposed actions without executing business actions."""

    def authorize(
        self,
        context: RequestContext,
        action: AIActionRequest,
        *,
        required_permission: str,
        required_entitlement: str | None = None,
    ) -> None:
        if context.identity_id is None:
            raise PermissionError("Authenticated identity is required")

        if context.organisation_id is None:
            raise PermissionError("Organisation context is required")

        if not action.action_type or not action.action_type.strip():
            raise ValueError("AI action type is required")

        if not context.has_permission(required_permission):
            raise PermissionError(
                f"AI action permission required: {required_permission}"
            )

        if (
            required_entitlement is not None
            and not context.has_entitlement(required_entitlement)
        ):
            raise PermissionError(
                f"AI action entitlement required: {required_entitlement}"
            )
