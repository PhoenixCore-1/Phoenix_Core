from uuid import UUID

from phoenix_core.errors import AuthorizationError


class CompanyRoleQueryService:
    """Company Platform read workflows for roles and permissions."""

    def __init__(self, core_api):
        self.core_api = core_api
        self.core_service = core_api.core_service

    def list_roles(self, context):
        self.core_api.require_permission(context, "company.roles.manage")

        items = self.core_service.list_roles(
            context.organisation_id
        )

        return {
            "items": [
                {
                    "id": str(item.id),
                    "organisation_id": str(item.organisation_id),
                    "code": item.code,
                    "name": item.name,
                    "scope": item.scope,
                    "status": item.status,
                    "created_at": item.created_at.isoformat(),
                }
                for item in items
            ]
        }

    def list_role_permissions(self, context, role_id: UUID):
        self.core_api.require_permission(context, "company.roles.manage")

        role = self.core_service.get_role(role_id)

        if role.organisation_id != context.organisation_id:
            raise AuthorizationError(
                "Role does not belong to the current organisation."
            )

        items = self.core_service.list_role_permissions(role_id)

        return {
            "items": [
                {
                    "id": str(item.id),
                    "code": item.code,
                    "name": item.name,
                    "created_at": item.created_at.isoformat(),
                }
                for item in items
            ]
        }

    def list_permissions(self, context):
        self.core_api.require_permission(context, "company.roles.manage")

        items = self.core_service.list_permissions()

        return {
            "items": [
                {
                    "id": str(item.id),
                    "code": item.code,
                    "name": item.name,
                    "created_at": item.created_at.isoformat(),
                }
                for item in items
            ]
        }
