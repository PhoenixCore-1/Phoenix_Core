
from uuid import UUID

from fastapi import APIRouter, Request

from phoenix_core.errors import AuthorizationError, ValidationError
from phoenix_core.http_api.baseline import _session_context


router = APIRouter(prefix="/api/ip", tags=["IP Management"])


def _context(request: Request):
    api, user, org = _session_context(request)

    token = request.cookies.get("phoenix_session")
    if not token:
        raise AuthorizationError("Authentication required.")

    session_id = api.resolve_session_id(token)

    context = api.resolve_context(
        request_id=str(getattr(request.state, "request_id", None)),
        session_id=session_id,
        organisation_id=org["id"] if org else None,
    )

    return api, user, org, context


@router.get("/owners")
def list_owners(request: Request, owner_type: str | None = None):
    api, user, org, context = _context(request)

    if not context.has_permission("system.ip_management.view"):
        raise AuthorizationError("Permission denied.")

    return api.ip_list_owners(
        context,
        owner_type=owner_type,
    ).data


@router.post("/owners")
async def create_owner(request: Request):
    api, user, org, context = _context(request)

    if not context.has_permission("system.ip_management.manage"):
        raise AuthorizationError("Permission denied.")

    payload = await request.json()

    owner_type = str(payload.get("owner_type", "")).strip()
    name = str(payload.get("name", "")).strip()

    if not owner_type:
        raise ValidationError("owner_type is required.")

    if not name:
        raise ValidationError("name is required.")

    return api.ip_create_owner(
        context,
        owner_type=owner_type,
        name=name,
        description=payload.get("description"),
    ).data


@router.get("/owners/{owner_id}")
def get_owner(request: Request, owner_id: UUID):
    api, user, org, context = _context(request)

    if not context.has_permission("system.ip_management.view"):
        raise AuthorizationError("Permission denied.")

    return api.ip_get_owner(
        context,
        owner_id,
    ).data


@router.get("/assets")
def list_assets(
    request: Request,
    owner_id: UUID | None = None,
    asset_type: str | None = None,
):
    api, user, org, context = _context(request)

    if not context.has_permission("system.ip_management.view"):
        raise AuthorizationError("Permission denied.")

    return api.ip_list_assets(
        context,
        owner_id=owner_id,
        asset_type=asset_type,
    ).data


@router.post("/assets")
async def create_asset(request: Request):
    api, user, org, context = _context(request)

    if not context.has_permission("system.ip_management.manage"):
        raise AuthorizationError("Permission denied.")

    payload = await request.json()

    required = (
        "owner_id",
        "asset_code",
        "name",
        "asset_type",
    )

    missing = [
        field
        for field in required
        if not payload.get(field)
    ]

    if missing:
        raise ValidationError(
            "Missing required fields: " + ", ".join(missing)
        )

    try:
        owner_id = UUID(str(payload["owner_id"]))
    except ValueError as exc:
        raise ValidationError("owner_id must be a valid UUID.") from exc

    return api.ip_create_asset(
        context,
        owner_id=owner_id,
        asset_code=str(payload["asset_code"]),
        name=str(payload["name"]),
        asset_type=str(payload["asset_type"]),
        confidentiality_class=str(
            payload.get("confidentiality_class", "INTERNAL")
        ),
        description=payload.get("description"),
    ).data


@router.get("/assets/{asset_id}")
def get_asset(request: Request, asset_id: UUID):
    api, user, org, context = _context(request)

    if not context.has_permission("system.ip_management.view"):
        raise AuthorizationError("Permission denied.")

    return api.ip_get_asset(
        context,
        asset_id,
    ).data


@router.post("/assets/{asset_id}/transfer")
async def transfer_asset(request: Request, asset_id: UUID):
    api, user, org, context = _context(request)

    if not context.has_permission("system.ip_management.manage"):
        raise AuthorizationError("Permission denied.")

    payload = await request.json()

    if not payload.get("new_owner_id"):
        raise ValidationError("new_owner_id is required.")

    try:
        new_owner_id = UUID(str(payload["new_owner_id"]))
    except ValueError as exc:
        raise ValidationError(
            "new_owner_id must be a valid UUID."
        ) from exc

    document_id = None
    document_version_id = None

    if payload.get("document_id"):
        try:
            document_id = UUID(str(payload["document_id"]))
        except ValueError as exc:
            raise ValidationError(
                "document_id must be a valid UUID."
            ) from exc

    if payload.get("document_version_id"):
        try:
            document_version_id = UUID(
                str(payload["document_version_id"])
            )
        except ValueError as exc:
            raise ValidationError(
                "document_version_id must be a valid UUID."
            ) from exc

    return api.ip_transfer_ownership(
        context,
        asset_id,
        new_owner_id=new_owner_id,
        reason=payload.get("reason"),
        document_id=document_id,
        document_version_id=document_version_id,
    ).data

@router.post("/assets/{asset_id}/licences")
async def create_licence(
    request: Request,
    asset_id: UUID,
):
    api, user, org, context = _context(request)
    if not context.has_permission("system.ip_management.manage"):
        raise AuthorizationError("Permission denied.")

    body = await request.json()

    return api.ip_create_licence(
        context,
        asset_id,
        licence_type=body["licence_type"],
        licence_name=body.get("licence_name"),
        licence_version=body.get("licence_version"),
        licensor=body.get("licensor"),
        licensee=body.get("licensee"),
        permitted_use=body.get("permitted_use"),
        restrictions=body.get("restrictions"),
        source_url=body.get("source_url"),
        document_id=UUID(body["document_id"]) if body.get("document_id") else None,
        document_version_id=(
            UUID(body["document_version_id"])
            if body.get("document_version_id")
            else None
        ),
        effective_from=body.get("effective_from"),
        expires_at=body.get("expires_at"),
    ).data


@router.post("/assets/{asset_id}/assignments")
async def record_assignment(
    request: Request,
    asset_id: UUID,
):
    api, user, org, context = _context(request)
    if not context.has_permission("system.ip_management.manage"):
        raise AuthorizationError("Permission denied.")

    body = await request.json()

    return api.ip_record_assignment(
        context,
        asset_id,
        assignee_owner_id=UUID(body["assignee_owner_id"]),
        document_id=UUID(body["document_id"]),
        document_version_id=UUID(body["document_version_id"]),
        assignment_type=body["assignment_type"],
        assignor_owner_id=(
            UUID(body["assignor_owner_id"])
            if body.get("assignor_owner_id")
            else None
        ),
        effective_at=body.get("effective_at"),
        expires_at=body.get("expires_at"),
        notes=body.get("notes"),
    ).data


@router.post("/assets/{asset_id}/confidentiality")
async def create_confidentiality_record(
    request: Request,
    asset_id: UUID,
):
    api, user, org, context = _context(request)
    if not context.has_permission("system.ip_management.manage"):
        raise AuthorizationError("Permission denied.")

    body = await request.json()

    return api.ip_create_confidentiality_record(
        context,
        asset_id,
        owner_id=UUID(body["owner_id"]),
        party_name=body["party_name"],
        confidentiality_type=body["confidentiality_type"],
        document_id=UUID(body["document_id"]),
        document_version_id=UUID(body["document_version_id"]),
        effective_at=body["effective_at"],
        expires_at=body.get("expires_at"),
    ).data


@router.post("/assets/{asset_id}/third-party-components")
async def register_third_party_component(
    request: Request,
    asset_id: UUID,
):
    api, user, org, context = _context(request)
    if not context.has_permission("system.ip_management.manage"):
        raise AuthorizationError("Permission denied.")

    body = await request.json()

    return api.ip_register_third_party_component(
        context,
        asset_id,
        component_name=body["component_name"],
        component_version=body.get("component_version"),
        supplier=body.get("supplier"),
        licence_id=(
            UUID(body["licence_id"])
            if body.get("licence_id")
            else None
        ),
        source_url=body.get("source_url"),
        usage_notes=body.get("usage_notes"),
    ).data


@router.post("/assets/{asset_id}/documents")
async def add_asset_document(
    request: Request,
    asset_id: UUID,
):
    api, user, org, context = _context(request)
    if not context.has_permission("system.ip_management.manage"):
        raise AuthorizationError("Permission denied.")

    body = await request.json()

    return api.ip_add_asset_document(
        context,
        asset_id,
        document_id=UUID(body["document_id"]),
        document_version_id=UUID(body["document_version_id"]),
        document_role=body["document_role"],
    ).data


@router.get("/assets/{asset_id}/documents")
def list_asset_documents(
    request: Request,
    asset_id: UUID,
):
    api, user, org, context = _context(request)
    if not context.has_permission("system.ip_management.view"):
        raise AuthorizationError("Permission denied.")

    return api.ip_list_asset_documents(
        context,
        asset_id,
    ).data

@router.post("/assets/{asset_id}/versions")
async def create_asset_version(
    request: Request,
    asset_id: UUID,
):
    api, user, org, context = _context(request)

    if not context.has_permission("system.ip_management.manage"):
        raise AuthorizationError("Permission denied.")

    body = await request.json()

    if not body.get("version_label"):
        raise ValidationError("version_label is required.")

    return api.ip_create_asset_version(
        context,
        asset_id,
        version_label=str(body["version_label"]),
        description=body.get("description"),
        document_id=(
            UUID(body["document_id"])
            if body.get("document_id")
            else None
        ),
        document_version_id=(
            UUID(body["document_version_id"])
            if body.get("document_version_id")
            else None
        ),
        checksum=body.get("checksum"),
        effective_from=body.get("effective_from"),
    ).data


@router.get("/assets/{asset_id}/versions")
def list_asset_versions(
    request: Request,
    asset_id: UUID,
):
    api, user, org, context = _context(request)

    if not context.has_permission("system.ip_management.view"):
        raise AuthorizationError("Permission denied.")

    return api.ip_list_asset_versions(
        context,
        asset_id,
    ).data


@router.get("/asset-versions/{version_id}")
def get_asset_version(
    request: Request,
    version_id: UUID,
):
    api, user, org, context = _context(request)

    if not context.has_permission("system.ip_management.view"):
        raise AuthorizationError("Permission denied.")

    return api.ip_get_asset_version(
        context,
        version_id,
    ).data


@router.post("/asset-versions/{version_id}/retire")
async def retire_asset_version(
    request: Request,
    version_id: UUID,
):
    api, user, org, context = _context(request)

    if not context.has_permission("system.ip_management.manage"):
        raise AuthorizationError("Permission denied.")

    body = await request.json()

    return api.ip_retire_asset_version(
        context,
        version_id,
        retired_at=body.get("retired_at"),
    ).data

