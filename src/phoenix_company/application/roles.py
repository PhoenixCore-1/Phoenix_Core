from uuid import UUID

from phoenix_core.api.contracts import ApiResponse
from phoenix_core.errors import AuthorizationError


class CompanyRoleApplicationService:
    """Company Platform workflows for roles and role permissions."""

    def __init__(self, core_api):
        self.core_api = core_api
        self.core_service = core_api.core_service

    def create_role(self, context, *, code: str, name: str) -> ApiResponse:
        self.core_api.require_permission(context, "company.roles.manage")

        role = self.core_service.create_role(
            context.organisation_id,
            code,
            name,
        )

        self.core_api._audit(
            context,
            action="COMPANY_ROLE_CREATED",
            target_type="ROLE",
            target_id=role.id,
        )

        return ApiResponse(
            data={
                "id": str(role.id),
                "organisation_id": str(role.organisation_id),
                "code": role.code,
                "name": role.name,
                "scope": role.scope,
                "status": role.status,
            },
            request_id=context.request_id,
        )

    def update_role(
        self,
        context,
        role_id: UUID,
        *,
        code: str | None = None,
        name: str | None = None,
    ) -> ApiResponse:
        self.core_api.require_permission(context, "company.roles.manage")

        role = self.core_service.get_role(role_id)

        if role.organisation_id != context.organisation_id:
            raise AuthorizationError(
                "Role does not belong to the current organisation."
            )

        updated = self.core_service.update_role(
            role_id,
            code=code,
            name=name,
        )

        self.core_api._audit(
            context,
            action="COMPANY_ROLE_UPDATED",
            target_type="ROLE",
            target_id=updated.id,
        )

        return ApiResponse(
            data={
                "id": str(updated.id),
                "organisation_id": str(updated.organisation_id),
                "code": updated.code,
                "name": updated.name,
                "scope": updated.scope,
                "status": updated.status,
            },
            request_id=context.request_id,
        )

    def set_role_status(
        self,
        context,
        role_id: UUID,
        status: str,
    ) -> ApiResponse:
        self.core_api.require_permission(context, "company.roles.manage")

        role = self.core_service.get_role(role_id)

        if role.organisation_id != context.organisation_id:
            raise AuthorizationError(
                "Role does not belong to the current organisation."
            )

        updated = self.core_service.set_role_status(
            role_id,
            status,
        )

        self.core_api._audit(
            context,
            action=f"COMPANY_ROLE_{status}",
            target_type="ROLE",
            target_id=updated.id,
        )

        return ApiResponse(
            data={
                "id": str(updated.id),
                "organisation_id": str(updated.organisation_id),
                "code": updated.code,
                "name": updated.name,
                "scope": updated.scope,
                "status": updated.status,
            },
            request_id=context.request_id,
        )

    def assign_role(
        self,
        context,
        membership_id: UUID,
        role_id: UUID,
    ) -> ApiResponse:
        self.core_api.require_permission(context, "company.roles.manage")

        membership = self.core_service.get_membership(membership_id)
        role = self.core_service.get_role(role_id)

        if (
            membership.organisation_id != context.organisation_id
            or role.organisation_id != context.organisation_id
        ):
            raise AuthorizationError(
                "Role and membership must belong to the current organisation."
            )

        assignment_id = self.core_service.assign_role(
            membership_id,
            role_id,
        )

        self.core_api._audit(
            context,
            action="COMPANY_ROLE_ASSIGNED",
            target_type="ROLE_ASSIGNMENT",
            target_id=UUID(assignment_id),
        )

        return ApiResponse(
            data={
                "id": assignment_id,
                "membership_id": str(membership_id),
                "role_id": str(role_id),
            },
            request_id=context.request_id,
        )

    def remove_role(
        self,
        context,
        membership_id: UUID,
        role_id: UUID,
    ) -> ApiResponse:
        self.core_api.require_permission(context, "company.roles.manage")

        membership = self.core_service.get_membership(membership_id)
        role = self.core_service.get_role(role_id)

        if (
            membership.organisation_id != context.organisation_id
            or role.organisation_id != context.organisation_id
        ):
            raise AuthorizationError(
                "Role and membership must belong to the current organisation."
            )

        removed = self.core_service.remove_role(
            membership_id,
            role_id,
        )

        if removed:
            self.core_api._audit(
                context,
                action="COMPANY_ROLE_REMOVED",
                target_type="ROLE",
                target_id=role_id,
            )

        return ApiResponse(
            data={
                "removed": removed,
                "membership_id": str(membership_id),
                "role_id": str(role_id),
            },
            request_id=context.request_id,
        )

    def grant_permission(
        self,
        context,
        role_id: UUID,
        permission_id: UUID,
    ) -> ApiResponse:
        self.core_api.require_permission(context, "company.roles.manage")

        role = self.core_service.get_role(role_id)

        if role.organisation_id != context.organisation_id:
            raise AuthorizationError(
                "Role does not belong to the current organisation."
            )

        self.core_service.grant_permission(
            role_id,
            permission_id,
        )

        self.core_api._audit(
            context,
            action="COMPANY_ROLE_PERMISSION_GRANTED",
            target_type="ROLE",
            target_id=role_id,
        )

        return ApiResponse(
            data={
                "granted": True,
                "role_id": str(role_id),
                "permission_id": str(permission_id),
            },
            request_id=context.request_id,
        )

    def revoke_permission(
        self,
        context,
        role_id: UUID,
        permission_id: UUID,
    ) -> ApiResponse:
        self.core_api.require_permission(context, "company.roles.manage")

        role = self.core_service.get_role(role_id)

        if role.organisation_id != context.organisation_id:
            raise AuthorizationError(
                "Role does not belong to the current organisation."
            )

        removed = self.core_service.revoke_permission(
            role_id,
            permission_id,
        )

        if removed:
            self.core_api._audit(
                context,
                action="COMPANY_ROLE_PERMISSION_REVOKED",
                target_type="ROLE",
                target_id=role_id,
            )

        return ApiResponse(
            data={
                "revoked": removed,
                "role_id": str(role_id),
                "permission_id": str(permission_id),
            },
            request_id=context.request_id,
        )
