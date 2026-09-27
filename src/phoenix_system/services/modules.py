from fastapi import Request

from phoenix_core.errors import (
    AuthenticationError,
    AuthorizationError,
)


def _session_context(request: Request):
    api = request.app.state.core_api
    token = request.cookies.get("phoenix_session")

    if not token:
        raise AuthenticationError("Authentication required.")

    sid = api.resolve_session_id(token)

    row = api.db.execute(
        "SELECT u.id, u.identity_id, u.username, "
        "u.display_name, u.status, u.platform_level "
        "FROM users u "
        "JOIN sessions s ON s.identity_id=u.identity_id "
        "WHERE s.id=?",
        (str(sid),),
    ).fetchone()

    if not row:
        raise AuthenticationError("User session is not valid.")

    org = api.db.execute(
        "SELECT o.id,o.code,o.name,o.status "
        "FROM organisations o "
        "JOIN organisation_memberships m "
        "ON m.organisation_id=o.id "
        "WHERE m.identity_id=? "
        "AND m.status='ACTIVE' "
        "AND o.status='ACTIVE' LIMIT 1",
        (row["identity_id"],),
    ).fetchone()

    return api, row, org


def _require_system_admin(user):
    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError(
            "System Platform access required."
        )


def list_system_modules(request: Request):
    api, user, org = _session_context(request)

    _require_system_admin(user)

    rows = api.db.execute(
        "SELECT id,code,name,version,status "
        "FROM modules ORDER BY name"
    ).fetchall()

    return {
        "data": {
            "items": [dict(row) for row in rows]
        }
    }

def enable_system_module(request: Request, module_id):
    api, user, _org = _session_context(request)

    _require_system_admin(user)

    module = api.module_service.enable(module_id)

    return {
        "data": {
            "id": str(module.id),
            "code": module.code,
            "name": module.name,
            "version": module.version,
            "status": module.status,
            "created_at": module.created_at.isoformat(),
        }
    }


def disable_system_module(request: Request, module_id):
    api, user, _org = _session_context(request)

    _require_system_admin(user)

    module = api.module_service.disable(module_id)

    return {
        "data": {
            "id": str(module.id),
            "code": module.code,
            "name": module.name,
            "version": module.version,
            "status": module.status,
            "created_at": module.created_at.isoformat(),
        }
    }


def retire_system_module(request: Request, module_id):
    api, user, _org = _session_context(request)

    _require_system_admin(user)

    module = api.module_service.retire(module_id)

    return {
        "data": {
            "id": str(module.id),
            "code": module.code,
            "name": module.name,
            "version": module.version,
            "status": module.status,
            "created_at": module.created_at.isoformat(),
        }
    }