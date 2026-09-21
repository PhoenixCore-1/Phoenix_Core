from uuid import UUID

from phoenix_core.api.contracts import ApiResponse
from phoenix_core.errors import AuthorizationError


class CompanyUserApplicationService:
    """Company Platform workflows for users and memberships."""

    def __init__(self, core_api):
        self.core_api = core_api
        self.core_service = core_api.core_service

    def create_user(
        self,
        context,
        *,
        username: str,
        display_name: str,
        password: str,
    ) -> ApiResponse:
        self.core_api.require_permission(context, "company.users.manage")

        user = self.core_service.create_user(
            username,
            display_name,
            password,
        )
        membership = self.core_service.add_membership(
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

    def update_user(
        self,
        context,
        user_id: UUID,
        *,
        username: str | None = None,
        display_name: str | None = None,
    ) -> ApiResponse:
        self.core_api.require_permission(context, "company.users.manage")

        user = self.core_service.get_user(user_id)
        memberships = self.core_service.list_memberships(
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

        updated = self.core_service.update_user(
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

        membership = self.core_service.get_membership(membership_id)

        if membership.organisation_id != context.organisation_id:
            raise AuthorizationError(
                "Membership does not belong to the current organisation."
            )

        updated = self.core_service.set_membership_status(
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

        memberships = self.core_service.list_memberships(
            context.organisation_id
        )

        items = []
        for membership in memberships:
            user = self.core_service.get_user_by_identity(
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

        items = self.core_service.list_memberships(
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

    def list_users(self, context) -> ApiResponse:
        self.core_api.require_permission(
            context,
            "company.memberships.manage",
        )

        memberships = self.core_service.list_memberships(
            context.organisation_id
        )

        items = []
        for membership in memberships:
            user = self.core_service.get_user_by_identity(
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

        items = self.core_service.list_memberships(
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
