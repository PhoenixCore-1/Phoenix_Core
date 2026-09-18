"""Company Platform application services.

The HTTP adapter must not reach into Core persistence or construct business
services itself. These application services receive the authoritative Core
service and keep tenant scoping and audit behavior inside the application
boundary.
"""

from uuid import UUID

from phoenix_core.api.contracts import ApiResponse
from phoenix_core.audit.domain import AuditEvent
from phoenix_core.company.workspaces import CompanyWorkspaceService


class CompanyPlatformApplicationService:
    def __init__(self, core_api):
        self.core_api = core_api
        self.core = core_api.core_service

    def list_workspaces(self, context) -> ApiResponse:
        service = CompanyWorkspaceService(
            self.core.db, self.core.module_service, self.core.entitlement_service
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
        self.core_api.require_permission(context, "company.workspaces.manage")
        service = CompanyWorkspaceService(
            self.core.db, self.core.module_service, self.core.entitlement_service
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
        return ApiResponse(data=result, request_id=context.request_id)

    def company_report(self, context) -> ApiResponse:
        self.core_api.require_permission(context, "company.reports.view")
        memberships = self.core.list_memberships(context.organisation_id)
        roles = self.core.list_roles(context.organisation_id)
        permissions = self.core.list_permissions()
        return ApiResponse(
            data={
                "organisation_id": str(context.organisation_id),
                "people": {
                    "total_memberships": len(memberships),
                    "active": sum(1 for item in memberships if item.status == "ACTIVE"),
                    "suspended": sum(1 for item in memberships if item.status == "SUSPENDED"),
                    "removed": sum(1 for item in memberships if item.status == "REMOVED"),
                },
                "roles": {
                    "total": len(roles),
                    "active": sum(1 for item in roles if item.status == "ACTIVE"),
                    "disabled": sum(1 for item in roles if item.status == "DISABLED"),
                },
                "security": {
                    "effective_permissions": len(context.permissions),
                    "available_permissions": len(permissions),
                },
                "modules": {"entitled": sorted(context.entitlements)},
                "report_scope": "COMPANY_ADMINISTRATION",
            },
            request_id=context.request_id,
        )
