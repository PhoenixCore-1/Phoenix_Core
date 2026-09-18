from phoenix_core.ai.action_authorization import AIActionAuthorizationService
from phoenix_core.ai.contracts import AIActionRequest
from phoenix_core.security.context import RequestContext


class AIActionService:
    """Core boundary for authorizing AI-proposed actions.

    This service authorizes proposals only. It never executes business actions.
    """

    def __init__(self, authorization_service=None):
        self.authorization_service = (
            authorization_service or AIActionAuthorizationService()
        )

    def authorize_proposal(
        self,
        context: RequestContext,
        action: AIActionRequest,
        *,
        required_permission: str,
        required_entitlement: str | None = None,
    ) -> AIActionRequest:
        self.authorization_service.authorize(
            context,
            action,
            required_permission=required_permission,
            required_entitlement=required_entitlement,
        )

        return action
