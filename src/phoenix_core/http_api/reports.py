"""Company Platform reporting HTTP endpoints."""

from fastapi import APIRouter, Request

from phoenix_core.company.application import CompanyPlatformApplicationService
from phoenix_core.http_api.authorization import resolve_request_context

router = APIRouter(prefix="/api/v1/company/reports", tags=["Company Platform"])


@router.get("")
async def company_reports(request: Request):
    """Return tenant-level administration and oversight metrics."""
    context = await resolve_request_context(request)
    result = CompanyPlatformApplicationService(request.app.state.core_api).company_report(context)
    return {"data": result.data, "request_id": result.request_id}
