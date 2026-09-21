"""Company Platform activity application service."""

from uuid import UUID

from phoenix_core.api.contracts import ApiResponse
from phoenix_core.errors import AuthorizationError


class CompanyActivityApplicationService:
    def __init__(self, core_api):
        self.core_api = core_api
        self.core = core_api.core_service

    def list_activity(
        self,
        context,
        *,
        action=None,
        target_type=None,
        identity_id: UUID | None = None,
        limit=100,
        offset=0,
    ) -> ApiResponse:
        self.core_api.require_permission(
            context,
            "company.activity.view",
        )

        if identity_id is not None:
            memberships = self.core.list_memberships(
                context.organisation_id
            )
            if not any(
                item.identity_id == identity_id
                and item.status != "REMOVED"
                for item in memberships
            ):
                raise AuthorizationError(
                    "Activity identity does not belong to the current organisation."
                )

        events = self.core.audit_service.list(
            organisation_id=context.organisation_id,
            identity_id=identity_id,
            action=action,
            target_type=target_type,
            limit=limit,
            offset=offset,
        )

        return ApiResponse(
            data={
                "items": [
                    {
                        "id": str(event.id),
                        "organisation_id": (
                            str(event.organisation_id)
                            if event.organisation_id
                            else None
                        ),
                        "identity_id": (
                            str(event.identity_id)
                            if event.identity_id
                            else None
                        ),
                        "action": event.action,
                        "target_type": event.target_type,
                        "target_id": (
                            str(event.target_id)
                            if event.target_id
                            else None
                        ),
                        "request_id": event.request_id,
                        "created_at": event.created_at.isoformat(),
                    }
                    for event in events
                ],
                "limit": limit,
                "offset": offset,
            },
            request_id=context.request_id,
        )
