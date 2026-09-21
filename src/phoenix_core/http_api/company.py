"""Company Platform HTTP endpoints backed by Phoenix Core authority."""

from uuid import UUID

from fastapi import APIRouter, Request

from phoenix_core.http_api.authorization import resolve_request_context
from phoenix_company.application.users import CompanyUserApplicationService
from phoenix_company.application.activity import CompanyActivityApplicationService
from phoenix_company.application.context import CompanyContextApplicationService
from phoenix_company.application.roles import CompanyRoleApplicationService
from phoenix_company.application.role_queries import CompanyRoleQueryService

router = APIRouter(prefix="/api/v1/company", tags=["Company Platform"])




def _user_service(request: Request):
    return CompanyUserApplicationService(request.app.state.core_api)

def _context_service(request: Request):
    return CompanyContextApplicationService(request.app.state.core_api)

def _activity_service(request: Request):
    return CompanyActivityApplicationService(request.app.state.core_api)

def _role_service(request: Request):
    return CompanyRoleApplicationService(request.app.state.core_api)

def _role_query_service(request: Request):
    return CompanyRoleQueryService(request.app.state.core_api)


def _organisation(context):
    return context.organisation_id


def _role_data(role):
    return {"id": str(role.id), "organisation_id": str(role.organisation_id), "code": role.code, "name": role.name, "scope": role.scope, "status": role.status, "created_at": role.created_at.isoformat()}


def _membership_data(item):
    return {"id": str(item.id), "identity_id": str(item.identity_id), "organisation_id": str(item.organisation_id), "status": item.status, "created_at": item.created_at.isoformat()}


@router.get("")
async def current_company(request: Request):
    context = await resolve_request_context(request)
    result = _context_service(request).get_current_company(context)
    return {"data": result.data, "request_id": result.request_id}


@router.get("/users")
async def users(request: Request):
    context = await resolve_request_context(request)
    result = _user_service(request).list_users(context)
    return {"data": result.data, "request_id": result.request_id}

@router.get("/memberships")
async def memberships(request: Request):
    context = await resolve_request_context(request)
    result = _user_service(request).list_memberships(context)
    return {"data": result.data, "request_id": result.request_id}

@router.get("/activity")
async def activity(request: Request):
    context = await resolve_request_context(request)
    action = request.query_params.get("action") or None
    target_type = request.query_params.get("target_type") or None
    identity_value = request.query_params.get("identity_id") or None
    identity_id = UUID(identity_value) if identity_value else None
    try:
        limit = int(request.query_params.get("limit", "100"))
        offset = int(request.query_params.get("offset", "0"))
    except ValueError as exc:
        from phoenix_core.errors import ValidationError
        raise ValidationError("Activity limit and offset must be integers.") from exc
    result = _activity_service(request).list_activity(
        context,
        action=action,
        target_type=target_type,
        identity_id=identity_id,
        limit=limit,
        offset=offset,
    )
    return {"data": result.data, "request_id": result.request_id}


@router.post("/users")
async def create_user(request: Request):
    context = await resolve_request_context(request)
    payload = await request.json()
    result = _user_service(request).create_user(
        context,
        username=str(payload.get("username", "")),
        display_name=str(payload.get("display_name", "")),
        password=str(payload.get("password", "")),
    )
    return {"data": result.data, "request_id": result.request_id}


@router.patch("/users/{user_id}")
async def update_user(request: Request, user_id: UUID):
    context = await resolve_request_context(request)
    payload = await request.json()
    result = _user_service(request).update_user(
        context,
        user_id,
        username=payload.get("username"),
        display_name=payload.get("display_name"),
    )
    return {"data": result.data, "request_id": result.request_id}


@router.post("/memberships/{membership_id}/suspend")
async def suspend_membership(request: Request, membership_id: UUID):
    context = await resolve_request_context(request)
    result = _user_service(request).set_membership_status(context, membership_id, "SUSPENDED")
    return {"data": result.data, "request_id": result.request_id}


@router.post("/memberships/{membership_id}/restore")
async def restore_membership(request: Request, membership_id: UUID):
    context = await resolve_request_context(request)
    result = _user_service(request).set_membership_status(context, membership_id, "ACTIVE")
    return {"data": result.data, "request_id": result.request_id}


@router.post("/memberships/{membership_id}/remove")
async def remove_membership(request: Request, membership_id: UUID):
    context = await resolve_request_context(request)
    result = _user_service(request).set_membership_status(context, membership_id, "REMOVED")
    return {"data": result.data, "request_id": result.request_id}


@router.get("/roles")
async def roles(request: Request):
    context = await resolve_request_context(request)
    data = _role_query_service(request).list_roles(context)
    return {"data": data, "request_id": context.request_id}

@router.post("/roles")
async def create_role(request: Request):
    context = await resolve_request_context(request)
    payload = await request.json()
    result = _role_service(request).create_role(
        context,
        code=str(payload.get("code", "")),
        name=str(payload.get("name", "")),
    )
    return {"data": result.data, "request_id": result.request_id}


@router.patch("/roles/{role_id}")
async def update_role(request: Request, role_id: UUID):
    context = await resolve_request_context(request)
    payload = await request.json()
    result = _role_service(request).update_role(
        context,
        role_id,
        code=payload.get("code"),
        name=payload.get("name"),
    )
    return {"data": result.data, "request_id": result.request_id}


@router.post("/roles/{role_id}/disable")
async def disable_role(request: Request, role_id: UUID):
    context = await resolve_request_context(request)
    result = _role_service(request).set_role_status(context, role_id, "DISABLED")
    return {"data": result.data, "request_id": result.request_id}


@router.post("/roles/{role_id}/enable")
async def enable_role(request: Request, role_id: UUID):
    context = await resolve_request_context(request)
    result = _role_service(request).set_role_status(context, role_id, "ACTIVE")
    return {"data": result.data, "request_id": result.request_id}


@router.get("/roles/{role_id}/permissions")
async def role_permissions(request: Request, role_id: UUID):
    context = await resolve_request_context(request)
    data = _role_query_service(request).list_role_permissions(
        context,
        role_id,
    )
    return {"data": data, "request_id": context.request_id}

@router.post("/roles/{role_id}/permissions/{permission_id}")
async def grant_role_permission(request: Request, role_id: UUID, permission_id: UUID):
    context = await resolve_request_context(request)
    result = _role_service(request).grant_permission(context, role_id, permission_id)
    return {"data": result.data, "request_id": result.request_id}


@router.delete("/roles/{role_id}/permissions/{permission_id}")
async def revoke_role_permission(request: Request, role_id: UUID, permission_id: UUID):
    context = await resolve_request_context(request)
    result = _role_service(request).revoke_permission(context, role_id, permission_id)
    return {"data": result.data, "request_id": result.request_id}


@router.post("/memberships/{membership_id}/roles/{role_id}")
async def assign_role(request: Request, membership_id: UUID, role_id: UUID):
    context = await resolve_request_context(request)
    result = _role_service(request).assign_role(context, membership_id, role_id)
    return {"data": result.data, "request_id": result.request_id}


@router.delete("/memberships/{membership_id}/roles/{role_id}")
async def remove_role(request: Request, membership_id: UUID, role_id: UUID):
    context = await resolve_request_context(request)
    result = _role_service(request).remove_role(context, membership_id, role_id)
    return {"data": result.data, "request_id": result.request_id}


@router.get("/permissions")
async def permissions(request: Request):
    context = await resolve_request_context(request)
    data = _role_query_service(request).list_permissions(context)
    return {"data": data, "request_id": context.request_id}
