"""Company Platform settings application service.

Company settings are tenant-scoped Core configuration. Phoenix System Platform
remains authoritative for global/platform settings and feature flags.
"""

from typing import Any

from phoenix_core.api.contracts import ApiResponse
from phoenix_core.audit.domain import AuditEvent
from phoenix_core.configuration.domain import decode_value


class CompanySettingsApplicationService:
    def __init__(self, core_api):
        self.core_api = core_api
        self.core = core_api.core_service

    @staticmethod
    def _serialize(setting):
        return {
            "id": str(setting.id),
            "organisation_id": str(setting.organisation_id),
            "key": setting.key,
            "value_type": setting.value_type,
            "value": decode_value(setting.value, setting.value_type),
            "description": setting.description,
            "created_at": setting.created_at.isoformat(),
            "updated_at": setting.updated_at.isoformat(),
        }

    def list_settings(self, context) -> ApiResponse:
        self.core_api.require_permission(context, "company.configuration.manage")
        items = self.core.configuration_service.list_settings(
            organisation_id=context.organisation_id,
            include_global=False,
        )
        return ApiResponse(
            data={"organisation_id": str(context.organisation_id), "items": [self._serialize(item) for item in items]},
            request_id=context.request_id,
        )

    def upsert_setting(
        self,
        context,
        key: str,
        value: Any,
        *,
        value_type: str | None = None,
        description: str | None = None,
    ) -> ApiResponse:
        self.core_api.require_permission(context, "company.configuration.manage")
        key = key.strip()
        existing = self.core.configuration_service.get_setting(
            key, organisation_id=context.organisation_id, required=False
        )
        effective_type = (value_type or (existing.value_type if existing else "STRING")).strip().upper()
        effective_description = description if description is not None else (existing.description if existing else None)
        setting = self.core.configuration_service.create_setting(
            key,
            value,
            effective_type,
            organisation_id=context.organisation_id,
            description=effective_description,
        )
        self.core.audit_service.record(
            AuditEvent.create(
                action="COMPANY_SETTING_UPDATED",
                organisation_id=context.organisation_id,
                identity_id=context.identity_id,
                target_type="SETTING",
                target_id=setting.id,
                request_id=context.request_id,
            )
        )
        return ApiResponse(data=self._serialize(setting), request_id=context.request_id)
