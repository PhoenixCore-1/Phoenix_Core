"""Company Platform context application service."""


from phoenix_core.api.contracts import ApiResponse


class CompanyContextApplicationService:
    def __init__(self, core_api):
        self.core_api = core_api
        self.core = core_api.core_service

    def get_current_company(self, context) -> ApiResponse:
        organisation = self.core.get_organisation(context.organisation_id)

        return ApiResponse(
            data={
                "id": str(organisation.id),
                "code": organisation.code,
                "name": organisation.name,
                "status": organisation.status,
                "created_at": organisation.created_at.isoformat(),
            },
            request_id=context.request_id,
        )
