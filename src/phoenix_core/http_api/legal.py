from uuid import UUID, uuid4

from fastapi import APIRouter, Request

from phoenix_company.application.legal import CompanyLegalApplicationService
from phoenix_core.errors import AuthenticationError, AuthorizationError, ValidationError
from phoenix_core.http_api.baseline import _session_context

router = APIRouter(prefix="/api/legal", tags=["Legal Compliance"])


def _legal_context(request: Request):
    api, user, org = _session_context(request)

    token = request.cookies.get("phoenix_session")
    if not token:
        raise AuthenticationError("Authentication required.")

    session_id = api.resolve_session_id(token)

    context = api.resolve_context(
        request_id=str(
            getattr(request.state, "request_id", None)
            or uuid4()
        ),
        session_id=session_id,
        organisation_id=org["id"] if org else None,
    )

    return api, user, org, context


@router.get("/required-actions")
def required_actions(request: Request):
    api, user, org, context = _legal_context(request)

    if not context.has_permission("user.legal_compliance.view"):
        raise AuthorizationError("Legal compliance access required.")

    return api.legal_required_actions(context).data


@router.get("/company/required-actions")
def company_required_actions(request: Request):
    api, user, org, context = _legal_context(request)

    if not context.has_permission("company.compliance_legal.view"):
        raise AuthorizationError(
            "Company legal compliance access required."
        )

    return CompanyLegalApplicationService(api).required_actions(context).data


@router.post("/actions/{assignment_id}/complete")
async def complete_action(request: Request, assignment_id: UUID):
    api, user, org, context = _legal_context(request)

    if not context.has_permission("user.legal_compliance.action"):
        raise AuthorizationError("Legal compliance action access required.")

    payload = await request.json()

    action_type = str(
        payload.get("action_type", "")
    ).strip().upper()

    document_version_id = payload.get("document_version_id")
    document_checksum = str(
        payload.get("document_checksum", "")
    ).strip()

    if not action_type:
        raise ValidationError("action_type is required.")

    if not document_version_id:
        raise ValidationError("document_version_id is required.")

    if not document_checksum:
        raise ValidationError("document_checksum is required.")

    try:
        version_id = UUID(str(document_version_id))
    except ValueError as exc:
        raise ValidationError(
            "document_version_id must be a valid UUID."
        ) from exc

    result = api.legal_complete_action(
        context,
        assignment_id,
        action_type=action_type,
        document_version_id=version_id,
        document_checksum=document_checksum,
        confirmation_reference=payload.get(
            "confirmation_reference"
        ),
        signature_provider=payload.get(
            "signature_provider"
        ),
        signature_reference=payload.get(
            "signature_reference"
        ),
        technical_evidence=payload.get(
            "technical_evidence"
        ),
    )

    return result.data
