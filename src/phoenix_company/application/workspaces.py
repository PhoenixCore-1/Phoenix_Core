"""Company Platform workspace application service."""

from uuid import UUID

from phoenix_core.api.contracts import ApiResponse
from phoenix_core.audit.domain import AuditEvent
from phoenix_core.company.workspaces import CompanyWorkspaceService


class CompanyWorkspaceApplicationService:
    def __init__(self, core_api):
        self.core_api = core_api
        self.core = core_api.core_service

    def list_workspaces(self, context) -> ApiResponse:
        service = CompanyWorkspaceService(
            self.core.db,
            self.core.module_service,
            self.core.entitlement_service,
        )
        return ApiResponse(
            data={"items": service.list(context.organisation_id)},
            request_id=context.request_id,
        )

    def update_workspace(
        self,
        context,
        module_code: str,
        *,
        display_name=None,
        visible=None,
        sort_order=None,
    ) -> ApiResponse:
        self.core_api.require_permission(
            context,
            "company.workspaces.manage",
        )
        service = CompanyWorkspaceService(
            self.core.db,
            self.core.module_service,
            self.core.entitlement_service,
        )
        result = service.update(
            context.organisation_id,
            module_code,
            display_name=display_name,
            visible=visible,
            sort_order=sort_order,
        )
        module = self.core.module_service.get_by_code(module_code)
        self.core.audit_service.record(
            AuditEvent.create(
                action="COMPANY_WORKSPACE_UPDATED",
                organisation_id=context.organisation_id,
                identity_id=context.identity_id,
                target_type="MODULE",
                target_id=UUID(str(module.id)),
                request_id=context.request_id,
            )
        )
        return ApiResponse(
            data=result,
            request_id=context.request_id,
        )
