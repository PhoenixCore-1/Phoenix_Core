"""Company Platform compliance monitoring HTTP endpoints."""

from fastapi import APIRouter, Query, Request

from phoenix_core.company.monitoring import CompanyComplianceMonitoringService
from phoenix_core.http_api.authorization import resolve_request_context

router = APIRouter(prefix="/api/v1/company/compliance/monitoring", tags=["Company Platform"])


@router.get("")
async def monitoring(request: Request, days: int = Query(default=30, ge=1, le=365)):
    context = await resolve_request_context(request)
    result = CompanyComplianceMonitoringService(request.app.state.core_api).overview(context, days=days)
    return {"data": result.data, "request_id": result.request_id}
