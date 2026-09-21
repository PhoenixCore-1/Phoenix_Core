from uuid import UUID, uuid4

from fastapi import Request

from phoenix_core.errors import AuthenticationError, AuthorizationError, ValidationError


def _session_context(request: Request):
    api = request.app.state.core_api
    token = request.cookies.get("phoenix_session")

    if not token:
        raise AuthenticationError("Authentication required.")

    sid = api.resolve_session_id(token)

    row = api.db.execute(
        "SELECT u.id, u.identity_id, u.username, u.display_name, "
        "u.status, u.platform_level "
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
        "AND o.status='ACTIVE' "
        "LIMIT 1",
        (row["identity_id"],),
    ).fetchone()

    return api, row, org


def _require_system_admin(user):
    if user["platform_level"] != "SYSTEM_ADMIN":
        raise AuthorizationError("System Platform access required.")


def _audit_system_user(
    request: Request,
    api,
    user,
    org,
    *,
    action: str,
    target_id,
):
    token = request.cookies.get("phoenix_session")
    session_id = api.resolve_session_id(token)

    context = api.resolve_context(
        request_id=str(
            getattr(request.state, "request_id", None)
            or uuid4()
        ),
        session_id=session_id,
        organisation_id=(
            org["id"]
            if org is not None
            else None
        ),
    )

    api._audit(
        context,
        action=action,
        target_type="USER",
        target_id=UUID(str(target_id)),
    )


def list_system_users(request: Request, search: str = ""):
    api, user, _org = _session_context(request)

    _require_system_admin(user)

    search = search.strip()

    if search:
        rows = api.db.execute(
            "SELECT u.id,u.identity_id,u.username,u.display_name,"
            "u.status,u.platform_level,u.password_reset_required,u.created_at "
            "FROM users u "
            "WHERE u.platform_level='SYSTEM_ADMIN' "
            "AND (u.username LIKE ? OR u.display_name LIKE ?) "
            "ORDER BY u.display_name",
            (f"%{search}%", f"%{search}%"),
        ).fetchall()
    else:
        rows = api.db.execute(
            "SELECT u.id,u.identity_id,u.username,u.display_name,"
            "u.status,u.platform_level,u.password_reset_required,u.created_at "
            "FROM users u "
            "WHERE u.platform_level='SYSTEM_ADMIN' "
            "ORDER BY u.display_name"
        ).fetchall()

    return {"data": {"items": [dict(r) for r in rows]}}


def get_system_user(request: Request, user_id: UUID):
    api, user, _org = _session_context(request)

    _require_system_admin(user)

    target = api.db.execute(
        "SELECT id,identity_id,username,display_name,status,"
        "platform_level,password_reset_required,created_at "
        "FROM users "
        "WHERE id=? AND platform_level='SYSTEM_ADMIN'",
        (str(user_id),),
    ).fetchone()

    if not target:
        raise ValidationError("System user not found.")

    return {"data": dict(target)}

async def create_system_user(request: Request):
    api, user, _org = _session_context(request)

    _require_system_admin(user)

    payload = await request.json()
    username = str(payload.get("username", "")).strip()
    display_name = str(payload.get("display_name", "")).strip()
    password = str(payload.get("password", ""))

    if not username or not display_name or len(password) < 12:
        raise ValidationError(
            "Username, display name and a password of at least 12 characters are required."
        )

    created = api.core_service.create_user(
        username,
        display_name,
        password,
    )

    api.db.execute(
        "UPDATE users SET platform_level='SYSTEM_ADMIN' WHERE id=?",
        (str(created.id),),
    )
    api.db.commit()

    return {
        "data": {
            "id": str(created.id),
            "identity_id": str(created.identity_id),
            "username": created.username,
            "display_name": created.display_name,
            "status": created.status,
            "platform_level": "SYSTEM_ADMIN",
            "password_reset_required": 0,
        }
    }

def suspend_system_user(request: Request, user_id: UUID):
    api, user, org = _session_context(request)

    _require_system_admin(user)

    if str(user["id"]) == str(user_id):
        raise ValidationError(
            "A system administrator cannot suspend their own account."
        )

    target = api.db.execute(
        "SELECT id FROM users "
        "WHERE id=? AND platform_level='SYSTEM_ADMIN'",
        (str(user_id),),
    ).fetchone()

    if not target:
        raise ValidationError("System user not found.")

    api.core_service.suspend_user(user_id)

    _audit_system_user(
        request,
        api,
        user,
        org,
        action="SYSTEM_USER_SUSPENDED",
        target_id=user_id,
    )

    return {
        "data": {
            "id": str(user_id),
            "status": "SUSPENDED",
        }
    }

def reactivate_system_user(request: Request, user_id: UUID):
    api, user, org = _session_context(request)

    _require_system_admin(user)

    target = api.db.execute(
        "SELECT id FROM users "
        "WHERE id=? AND platform_level='SYSTEM_ADMIN'",
        (str(user_id),),
    ).fetchone()

    if not target:
        raise ValidationError("System user not found.")

    api.core_service.reactivate_user(user_id)

    _audit_system_user(
        request,
        api,
        user,
        org,
        action="SYSTEM_USER_REACTIVATED",
        target_id=user_id,
    )

    return {
        "data": {
            "id": str(user_id),
            "status": "ACTIVE",
        }
    }

async def reset_system_user_password(
    request: Request,
    user_id: UUID,
):
    api, user, org = _session_context(request)

    _require_system_admin(user)

    target = api.db.execute(
        "SELECT id FROM users "
        "WHERE id=? AND platform_level='SYSTEM_ADMIN'",
        (str(user_id),),
    ).fetchone()

    if not target:
        raise ValidationError("System user not found.")

    payload = await request.json()
    password = str(payload.get("password", ""))

    api.authentication_service.admin_reset_password(
        user_id,
        password,
    )

    _audit_system_user(
        request,
        api,
        user,
        org,
        action="SYSTEM_USER_PASSWORD_RESET",
        target_id=user_id,
    )

    return {
        "data": {
            "id": str(user_id),
            "password_reset_required": 1,
        }
    }

def require_system_user_password_reset(
    request: Request,
    user_id: UUID,
):
    api, user, org = _session_context(request)

    _require_system_admin(user)

    target = api.db.execute(
        "SELECT id FROM users "
        "WHERE id=? AND platform_level='SYSTEM_ADMIN'",
        (str(user_id),),
    ).fetchone()

    if not target:
        raise ValidationError("System user not found.")

    api.authentication_service.require_password_reset(user_id)

    _audit_system_user(
        request,
        api,
        user,
        org,
        action="SYSTEM_USER_PASSWORD_RESET_REQUIRED",
        target_id=user_id,
    )

    return {
        "data": {
            "id": str(user_id),
            "password_reset_required": 1,
        }
    }
