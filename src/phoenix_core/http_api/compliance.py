"""Company Platform Compliance & Legal HTTP endpoints."""

from fastapi import APIRouter, Request

from phoenix_core.company.compliance import CompanyComplianceApplicationService
from phoenix_core.http_api.authorization import resolve_request_context

router = APIRouter(prefix="/api/v1/company/compliance", tags=["Company Platform"])


@router.get("")
async def compliance_overview(request: Request):
    """Return tenant-scoped compliance status from Phoenix Core legal records."""
    context = await resolve_request_context(request)
    result = CompanyComplianceApplicationService(request.app.state.core_api).overview(context)
    return {"data": result.data, "request_id": result.request_id}
