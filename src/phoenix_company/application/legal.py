"""Company Platform legal compliance application service."""

from phoenix_core.api.contracts import ApiResponse


class CompanyLegalApplicationService:
    def __init__(self, core_api):
        self.core_api = core_api
        self.core = core_api.core_service

    def required_actions(self, context) -> ApiResponse:
        if context.organisation_id is None:
            from phoenix_core.errors import AuthorizationError
            raise AuthorizationError(
                "Company legal actions require an organisation context."
            )

        actions = self.core.legal_compliance_service.get_required_actions(
            organisation_id=context.organisation_id,
            identity_id=None,
        )

        company_actions = [
            item for item in actions
            if item.get("assignment_scope") == "COMPANY"
        ]

        return ApiResponse(
            data={"items": company_actions},
            request_id=context.request_id,
        )
