"""Company Platform data visibility HTTP endpoints."""

from uuid import UUID

from fastapi import APIRouter, Request

from phoenix_core.audit.domain import AuditEvent
from phoenix_core.company.visibility import CompanyVisibilityService
from phoenix_core.http_api.authorization import resolve_request_context

router = APIRouter(prefix="/api/v1/company/visibility", tags=["Company Platform"])


def _service(request: Request) -> CompanyVisibilityService:
    return CompanyVisibilityService(request.app.state.core_api.core_service.db)


@router.get("")
async def list_visibility(request: Request):
    context = await resolve_request_context(request)
    return {"data": {"items": _service(request).list(context.organisation_id)}, "request_id": context.request_id}


@router.put("")
async def set_visibility(request: Request):
    context = await resolve_request_context(request)
    request.app.state.core_api.require_permission(context, "company.visibility.manage")
    payload = await request.json()
    membership_id = UUID(payload["membership_id"]) if payload.get("membership_id") else None
    role_id = UUID(payload["role_id"]) if payload.get("role_id") else None
    result = _service(request).upsert(
        context.organisation_id,
        scope_type=str(payload.get("scope_type", "")),
        resource_code=str(payload.get("resource_code", "")),
        visible=payload.get("visible"),
        membership_id=membership_id,
        role_id=role_id,
    )
    request.app.state.core_api.core_service.audit_service.record(AuditEvent.create(
        action="COMPANY_VISIBILITY_UPDATED",
        organisation_id=context.organisation_id,
        identity_id=context.identity_id,
        target_type="VISIBILITY_RULE",
        target_id=UUID(result["id"]),
        request_id=context.request_id,
    ))
    return {"data": result, "request_id": context.request_id}


@router.delete("/{rule_id}")
async def delete_visibility(request: Request, rule_id: UUID):
    context = await resolve_request_context(request)
    request.app.state.core_api.require_permission(context, "company.visibility.manage")
    removed = _service(request).delete(context.organisation_id, rule_id)
    request.app.state.core_api.core_service.audit_service.record(AuditEvent.create(
        action="COMPANY_VISIBILITY_DELETED",
        organisation_id=context.organisation_id,
        identity_id=context.identity_id,
        target_type="VISIBILITY_RULE",
        target_id=rule_id,
        request_id=context.request_id,
    ))
    return {"data": {"removed": removed, "id": str(rule_id)}, "request_id": context.request_id}
