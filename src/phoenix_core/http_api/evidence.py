"""Company Platform Compliance & Legal evidence endpoints."""

from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel

from phoenix_core.company.evidence import CompanyEvidenceApplicationService
from phoenix_core.http_api.authorization import resolve_request_context

router = APIRouter(prefix="/api/v1/company/evidence", tags=["Company Platform"])


class EvidencePayload(BaseModel):
    title: str
    evidence_type: str
    description: str | None = None
    policy_version_id: str | None = None
    document_id: str | None = None
    document_version_id: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None


def _service(request: Request) -> CompanyEvidenceApplicationService:
    return CompanyEvidenceApplicationService(request.app.state.core_api)


@router.get("")
async def list_evidence(request: Request, status: str | None = None):
    context = await resolve_request_context(request)
    result = _service(request).list_evidence(context, status=status)
    return {"data": result.data, "request_id": result.request_id}


@router.get("/{evidence_id}")
async def get_evidence(request: Request, evidence_id: UUID):
    context = await resolve_request_context(request)
    result = _service(request).get_evidence(context, evidence_id)
    return {"data": result.data, "request_id": result.request_id}


@router.post("")
async def create_evidence(request: Request, payload: EvidencePayload):
    context = await resolve_request_context(request)
    result = _service(request).create_evidence(
        context,
        title=payload.title,
        evidence_type=payload.evidence_type,
        description=payload.description,
        policy_version_id=payload.policy_version_id,
        document_id=payload.document_id,
        document_version_id=payload.document_version_id,
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
    )
    return {"data": result.data, "request_id": result.request_id}
