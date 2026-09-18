"""Company Platform workspace configuration HTTP endpoints."""

from fastapi import APIRouter, Request

from phoenix_core.company.application import CompanyPlatformApplicationService
from phoenix_core.http_api.authorization import resolve_request_context

router = APIRouter(prefix="/api/v1/company/workspaces", tags=["Company Platform"])


def _application(request: Request) -> CompanyPlatformApplicationService:
    return CompanyPlatformApplicationService(request.app.state.core_api)


@router.get("")
async def list_workspaces(request: Request):
    context = await resolve_request_context(request)
    result = _application(request).list_workspaces(context)
    return {"data": result.data, "request_id": result.request_id}


@router.patch("/{module_code}")
async def update_workspace(request: Request, module_code: str):
    context = await resolve_request_context(request)
    payload = await request.json()
    result = _application(request).update_workspace(
        context,
        module_code,
        display_name=payload.get("display_name"),
        visible=payload.get("visible"),
        sort_order=payload.get("sort_order"),
    )
    return {"data": result.data, "request_id": result.request_id}
