"""Company Platform settings HTTP endpoints."""

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from phoenix_core.company.settings import CompanySettingsApplicationService
from phoenix_core.http_api.authorization import resolve_request_context

router = APIRouter(prefix="/api/v1/company/settings", tags=["Company Platform"])


class CompanySettingPayload(BaseModel):
    value: Any
    value_type: str | None = None
    description: str | None = None


def _application(request: Request) -> CompanySettingsApplicationService:
    return CompanySettingsApplicationService(request.app.state.core_api)


@router.get("")
async def list_settings(request: Request):
    context = await resolve_request_context(request)
    result = _application(request).list_settings(context)
    return {"data": result.data, "request_id": result.request_id}


@router.patch("/{key}")
async def update_setting(request: Request, key: str, payload: CompanySettingPayload):
    context = await resolve_request_context(request)
    result = _application(request).upsert_setting(
        context,
        key,
        payload.value,
        value_type=payload.value_type,
        description=payload.description,
    )
    return {"data": result.data, "request_id": result.request_id}
