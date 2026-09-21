"""Phoenix Core V1.0.0 baseline platform endpoints.

This is intentionally small: it proves the SaaS shell end-to-end without
making the existing role/permission framework part of the baseline UX.
"""
from uuid import UUID, uuid4
from fastapi import APIRouter, Request
from phoenix_core.errors import AuthenticationError, AuthorizationError, ValidationError

router = APIRouter(prefix="/api/v1/baseline", tags=["Phoenix Core V1 Baseline"])

def _session_context(request: Request):
    api = request.app.state.core_api
    token = request.cookies.get("phoenix_session")
    if not token:
        raise AuthenticationError("Authentication required.")
    sid = api.resolve_session_id(token)
    row = api.db.execute(
        "SELECT u.id, u.identity_id, u.username, u.display_name, u.status, u.platform_level "
        "FROM users u JOIN sessions s ON s.identity_id=u.identity_id WHERE s.id=?",
        (str(sid),),
    ).fetchone()
    if not row:
        raise AuthenticationError("User session is not valid.")
    org = api.db.execute(
        "SELECT o.id,o.code,o.name,o.status FROM organisations o "
        "JOIN organisation_memberships m ON m.organisation_id=o.id "
        "WHERE m.identity_id=? AND m.status='ACTIVE' AND o.status='ACTIVE' LIMIT 1",
        (row["identity_id"],),
    ).fetchone()
    return api, row, org


def _audit_system_user(
    request: Request,
    api,
    user,
    org,
    *,
    action: str,
    target_id,
):
    """Record a system-user administrative action in Core audit."""
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
    rows = api.db.execute(
        "SELECT m.id,m.code,m.name,m.version,m.status, "
        "CASE WHEN e.status='ACTIVE' THEN 1 ELSE 0 END AS active "
        "FROM modules m LEFT JOIN module_entitlements e "
        "ON e.module_id=m.id AND e.organisation_id=? "
        "WHERE m.status='ENABLED' ORDER BY m.name",
        (str(org_id) if org_id else "",),
    ).fetchall()
    return [{"id":r["id"],"code":r["code"],"name":r["name"],"version":r["version"],"active":bool(r["active"])} for r in rows]

@router.get("/context")
def context(request: Request):
    api, user, org = _session_context(request)
    return {"data": {
        "user": {"id":user["id"],"username":user["username"],"display_name":user["display_name"],"platform_level":user["platform_level"]},
        "company": None if not org else {"id":org["id"],"code":org["code"],"name":org["name"],"status":org["status"]},
        "modules": _modules(api, org["id"] if org else None),
    }}

