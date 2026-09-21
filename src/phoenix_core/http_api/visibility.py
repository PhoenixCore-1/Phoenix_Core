"""Company Platform data visibility HTTP endpoints."""

from uuid import UUID

from fastapi import APIRouter, Request

from phoenix_company.application.visibility import CompanyVisibilityApplicationService
from phoenix_core.http_api.authorization import resolve_request_context

router = APIRouter(prefix="/api/v1/company/visibility", tags=["Company Platform"])


def _application(request: Request) -> CompanyVisibilityApplicationService:
    return CompanyVisibilityApplicationService(request.app.state.core_api)


@router.get("")
async def list_visibility(request: Request):
    context = await resolve_request_context(request)
    return {"data": {"items": _application(request).list_visibility(context)}, "request_id": context.request_id}


@router.put("")
async def set_visibility(request: Request):
    context = await resolve_request_context(request)
    payload = await request.json()
    membership_id = UUID(payload["membership_id"]) if payload.get("membership_id") else None
    role_id = UUID(payload["role_id"]) if payload.get("role_id") else None
    result = _application(request).set_visibility(
        context,
        scope_type=str(payload.get("scope_type", "")),
        resource_code=str(payload.get("resource_code", "")),
        visible=payload.get("visible"),
        membership_id=membership_id,
        role_id=role_id,
    )
    return {"data": result, "request_id": context.request_id}


@router.delete("/{rule_id}")
async def delete_visibility(request: Request, rule_id: UUID):
    context = await resolve_request_context(request)
    removed = _application(request).delete_visibility(context, rule_id)
    return {"data": {"removed": removed, "id": str(rule_id)}, "request_id": context.request_id}
