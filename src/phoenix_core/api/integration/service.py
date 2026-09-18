"""Phoenix Core integration service."""

from phoenix_core.api.integration.contracts import (
    IntegrationRequest,
    IntegrationResponse,
)
from phoenix_core.errors import ValidationError


class CoreIntegrationService:
    """Authoritative service boundary for Core integrations."""

    def __init__(self, api):
        self.api = api

    def handle(self, request: IntegrationRequest) -> IntegrationResponse:
        if not request.request_id:
            raise ValidationError("Integration request_id is required.")

        if not request.operation:
            raise ValidationError("Integration operation is required.")

        handler = getattr(
            self,
            f"_handle_{request.operation.replace('.', '_')}",
            None,
        )

        if handler is None:
            raise ValidationError(
                f"Unsupported integration operation: {request.operation}"
            )

        return handler(request)

    def _require_authenticated_context(self, request: IntegrationRequest) -> None:
        if request.session_id is None:
            raise ValidationError(
                "Integration request requires an authenticated session."
            )

        if request.organisation_id is None:
            raise ValidationError(
                "Integration request requires an organisation context."
            )

    def _handle_identity_current(
        self,
        request: IntegrationRequest,
    ) -> IntegrationResponse:
        self._require_authenticated_context(request)

        response = self.api.get_current_identity(
            request_id=request.request_id,
            session_id=request.session_id,
            organisation_id=request.organisation_id,
        )

        return IntegrationResponse(
            request_id=request.request_id,
            success=True,
            data=response.data,
        )
