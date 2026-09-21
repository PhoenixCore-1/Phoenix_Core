"""Company Platform data visibility application service."""

from uuid import UUID

from phoenix_core.audit.domain import AuditEvent


class CompanyVisibilityApplicationService:
    def __init__(self, core_api):
        self.core_api = core_api
        self.core = core_api.core_service

    def _service(self):
        from phoenix_core.company.visibility import CompanyVisibilityService
        return CompanyVisibilityService(self.core.db)

    def list_visibility(self, context):
        return self._service().list(context.organisation_id)

    def set_visibility(
        self,
        context,
        *,
        scope_type: str,
        resource_code: str,
        visible: bool,
        membership_id: UUID | None = None,
        role_id: UUID | None = None,
    ):
        self.core_api.require_permission(
            context,
            "company.visibility.manage",
        )

        result = self._service().upsert(
            context.organisation_id,
            scope_type=scope_type,
            resource_code=resource_code,
            visible=visible,
            membership_id=membership_id,
            role_id=role_id,
        )

        self.core.audit_service.record(
            AuditEvent.create(
                action="COMPANY_VISIBILITY_UPDATED",
                organisation_id=context.organisation_id,
                identity_id=context.identity_id,
                target_type="VISIBILITY_RULE",
                target_id=UUID(result["id"]),
                request_id=context.request_id,
            )
        )

        return result

    def delete_visibility(self, context, rule_id: UUID):
        self.core_api.require_permission(
            context,
            "company.visibility.manage",
        )

        removed = self._service().delete(
            context.organisation_id,
            rule_id,
        )

        self.core.audit_service.record(
            AuditEvent.create(
                action="COMPANY_VISIBILITY_DELETED",
                organisation_id=context.organisation_id,
                identity_id=context.identity_id,
                target_type="VISIBILITY_RULE",
                target_id=rule_id,
                request_id=context.request_id,
            )
        )

        return removed
