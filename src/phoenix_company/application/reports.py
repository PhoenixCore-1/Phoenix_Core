from phoenix_core.api.contracts import ApiResponse


class CompanyReportApplicationService:
    """Company Platform administration and oversight reporting."""

    def __init__(self, core_api):
        self.core_api = core_api
        self.core = core_api.core_service

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
                    "active": sum(
                        1 for item in memberships if item.status == "ACTIVE"
                    ),
                    "suspended": sum(
                        1 for item in memberships if item.status == "SUSPENDED"
                    ),
                    "removed": sum(
                        1 for item in memberships if item.status == "REMOVED"
                    ),
                },
                "roles": {
                    "total": len(roles),
                    "active": sum(
                        1 for item in roles if item.status == "ACTIVE"
                    ),
                    "disabled": sum(
                        1 for item in roles if item.status == "DISABLED"
                    ),
                },
                "security": {
                    "effective_permissions": len(context.permissions),
                    "available_permissions": len(permissions),
                },
                "modules": {
                    "entitled": sorted(context.entitlements)
                },
                "report_scope": "COMPANY_ADMINISTRATION",
            },
            request_id=context.request_id,
        )
