from uuid import UUID

from phoenix_core.api.contracts import ApiResponse
from phoenix_core.errors import AuthorizationError
from phoenix_company.application.memberships import CompanyMembershipApplicationService


class CompanyUserApplicationService:
    """Company Platform workflows for users and memberships."""

    def __init__(self, core_api):
        self.core_api = core_api
        self.user_service = core_api.user_service
        self.membership_service = CompanyMembershipApplicationService(core_api)

    def create_user(
        self,
        context,
        *,
        username: str,
        display_name: str,
        password: str,
    ) -> ApiResponse:
        self.core_api.require_permission(context, "company.users.manage")

        user = self.user_service.create_user(
            username=username,
            display_name=display_name,
            password=password,
        )
        membership = self.membership_service.add_membership(
            user.identity_id,
            context.organisation_id,
        )

        self.core_api._audit(
            context,
            action="COMPANY_USER_CREATED",
            target_type="USER",
            target_id=user.id,
        )
        self.core_api._audit(
            context,
            action="COMPANY_MEMBERSHIP_CREATED",
            target_type="MEMBERSHIP",
            target_id=membership.id,
        )

        return ApiResponse(
            data={
                "user": {
                    "id": str(user.id),
                    "identity_id": str(user.identity_id),
                    "username": user.username,
                    "display_name": user.display_name,
                    "status": user.status,
                },
                "membership": {
                    "id": str(membership.id),
                    "status": membership.status,
                },
            },
            request_id=context.request_id,
        )

    def get_user_access(self, context, user_id: UUID) -> ApiResponse:
        self.core_api.require_permission(
            context,
            "company.roles.manage",
        )

        user = self.user_service.get_user(user_id)

        memberships = self.membership_service.list_memberships(
            context.organisation_id,
        )

        membership = next(
            (
                item
                for item in memberships
                if item.identity_id == user.identity_id
                and item.status != "REMOVED"
            ),
            None,
        )

        if not membership:
            raise AuthorizationError(
                "User does not belong to the current organisation."
            )

        # Company Admins are owned by the System Platform.
        if getattr(user, "platform_level", None) == "COMPANY_ADMIN":
            raise AuthorizationError(
                "Company Admin access is managed by the System Platform."
            )

        roles = self.core_api.role_service.list_assigned_roles(
            membership.id
        )

        permissions = []

        for role in roles:
            role_permissions = self.core_api.role_service.list_role_permissions(
                role.id
            )

            for permission in role_permissions:
                permissions.append(
                    {
                        "id": str(permission.id),
                        "code": permission.code,
                        "name": permission.name,
                    }
                )

        unique_permissions = {
            item["id"]: item
            for item in permissions
        }

        return ApiResponse(
            data={
                "user": {
                    "id": str(user.id),
                    "identity_id": str(user.identity_id),
                    "username": user.username,
                    "display_name": user.display_name,
                    "status": user.status,
                },
                "membership": {
                    "id": str(membership.id),
                    "status": membership.status,
                },
                "roles": [
                    {
                        "id": str(role.id),
                        "code": role.code,
                        "name": role.name,
                        "scope": role.scope,
                        "status": role.status,
                    }
                    for role in roles
                ],
                "permissions": sorted(
                    unique_permissions.values(),
                    key=lambda item: item["code"],
                ),
            },
            request_id=context.request_id,
        )
    def update_user(
        self,
        context,
        user_id: UUID,
        *,
        username: str | None = None,
        display_name: str | None = None,
    ) -> ApiResponse:
        self.core_api.require_permission(context, "company.users.manage")

        user = self.user_service.get_user(user_id)
        memberships = self.membership_service.list_memberships(
            context.organisation_id
        )

        if not any(
            item.identity_id == user.identity_id
            and item.status != "REMOVED"
            for item in memberships
        ):
            raise AuthorizationError(
                "User does not belong to the current organisation."
            )

        updated = self.user_service.update_user(
            user_id,
            username=username,
            display_name=display_name,
        )

        self.core_api._audit(
            context,
            action="COMPANY_USER_UPDATED",
            target_type="USER",
            target_id=updated.id,
        )

        return ApiResponse(
            data={
                "id": str(updated.id),
                "identity_id": str(updated.identity_id),
                "username": updated.username,
                "display_name": updated.display_name,
                "status": updated.status,
            },
            request_id=context.request_id,
        )

    def set_membership_status(
        self,
        context,
        membership_id: UUID,
        status: str,
    ) -> ApiResponse:
        self.core_api.require_permission(
            context,
            "company.memberships.manage",
        )

        membership = self.membership_service.get_membership(membership_id)

        if membership.organisation_id != context.organisation_id:
            raise AuthorizationError(
                "Membership does not belong to the current organisation."
            )

        updated = self.membership_service.set_membership_status(
            membership_id,
            status,
        )

        self.core_api._audit(
            context,
            action=f"COMPANY_MEMBERSHIP_{status}",
            target_type="MEMBERSHIP",
            target_id=updated.id,
        )

        return ApiResponse(
            data={
                "id": str(updated.id),
                "identity_id": str(updated.identity_id),
                "organisation_id": str(updated.organisation_id),
                "status": updated.status,
                "created_at": updated.created_at.isoformat(),
            },
            request_id=context.request_id,
        )

    def list_users(self, context) -> ApiResponse:
        self.core_api.require_permission(
            context,
            "company.memberships.manage",
        )

        memberships = self.membership_service.list_memberships(
            context.organisation_id
        )

        items = []

        for membership in memberships:
            platform_row = self.user_service.db.execute(
                """
                SELECT platform_level
                FROM users
                WHERE identity_id=?
                """,
                (str(membership.identity_id),),
            ).fetchone()

            # Company Admins are provisioned and managed from
            # the System Platform. They are not ordinary
            # Company Platform users.
            if (
                platform_row
                and platform_row["platform_level"] == "COMPANY_ADMIN"
            ):
                continue

            user = self.user_service.get_user_by_identity(
                membership.identity_id
            )

            items.append(
                {
                    "id": str(user.id),
                    "identity_id": str(user.identity_id),
                    "username": user.username,
                    "display_name": user.display_name,
                    "user_status": user.status,
                    "membership_id": str(membership.id),
                    "membership_status": membership.status,
                    "created_at": user.created_at.isoformat(),
                }
            )

        return ApiResponse(
            data={"items": items},
            request_id=context.request_id,
        )

    def list_memberships(self, context) -> ApiResponse:
        self.core_api.require_permission(
            context,
            "company.memberships.manage",
        )

        items = self.membership_service.list_memberships(
            context.organisation_id
        )

        return ApiResponse(
            data={
                "items": [
                    {
                        "id": str(item.id),
                        "identity_id": str(item.identity_id),
                        "organisation_id": str(item.organisation_id),
                        "status": item.status,
                        "created_at": item.created_at.isoformat(),
                    }
                    for item in items
                ]
            },
            request_id=context.request_id,
        )



