"""HTTP authorization helpers for the Phoenix Core API.

Authorization is always evaluated from Core-resolved RequestContext. The HTTP
layer never trusts identity, organisation, permissions, or entitlements sent
by the browser as authoritative values.
"""

from functools import wraps
from uuid import UUID

from fastapi import Request

from phoenix_core.errors import AuthenticationError, AuthorizationError


async def resolve_request_context(request: Request):
    """Resolve the authenticated Core RequestContext for an HTTP request."""
    core_api = request.app.state.core_api
    session_id = _session_id(request, core_api)
    organisation_id = _organisation_id(request)
    return core_api.resolve_context(
        request_id=request.state.request_id,
        session_id=session_id,
        organisation_id=organisation_id,
    )


def require_permission(permission: str):
    """Require a Core permission before entering a route handler."""
    def decorator(handler):
        @wraps(handler)
        async def wrapped(request: Request, *args, **kwargs):
            context = await resolve_request_context(request)
            request.state.core_context = context
            request.app.state.core_api.require_permission(context, permission)
            return await handler(request, *args, **kwargs)

        return wrapped

    return decorator


def require_entitlement(module_code: str):
    """Require a Core module entitlement before entering a route handler."""
    def decorator(handler):
        @wraps(handler)
        async def wrapped(request: Request, *args, **kwargs):
            context = await resolve_request_context(request)
            request.state.core_context = context
            request.app.state.core_api.require_entitlement(context, module_code)
            return await handler(request, *args, **kwargs)

        return wrapped

    return decorator


def _session_id(request: Request, core_api):
    token = request.cookies.get("phoenix_session")
    if not token:
        raise AuthenticationError("Authentication required.")
    return core_api.resolve_session_id(token)


def _organisation_id(request: Request):
    value = request.headers.get("X-Phoenix-Organisation")
    if not value:
        raise AuthenticationError("An organisation context is required.")
    try:
        return UUID(value)
    except ValueError as exc:
        raise AuthenticationError("Invalid organisation context.") from exc
