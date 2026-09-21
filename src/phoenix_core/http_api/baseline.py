"""Phoenix Core V1 baseline compatibility endpoints."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Request

from phoenix_core.errors import AuthenticationError
from phoenix_core.security.context import RequestContext

router = APIRouter(
    prefix="/api/v1/baseline",
    tags=["Phoenix Core V1 Baseline"],
)


def _session_context(request: Request):
    api = request.app.state.core_api

    token = request.cookies.get("phoenix_session")
    if not token:
        raise AuthenticationError("Authentication required.")

    session_id = api.resolve_session_id(token)

    session = api.context_resolver.session_service.get_active(session_id)
    identity_id = UUID(session["identity_id"])

    user = api.db.execute(
        """
        SELECT id, identity_id, username, display_name, status, platform_level
        FROM users
        WHERE identity_id=?
        """,
        (str(identity_id),),
    ).fetchone()

    if not user:
        raise AuthenticationError("User session is not valid.")

    organisation = api.db.execute(
        """
        SELECT o.id, o.code, o.name, o.status
        FROM organisations o
        JOIN organisation_memberships m
          ON m.organisation_id=o.id
        WHERE m.identity_id=?
          AND m.status='ACTIVE'
          AND o.status='ACTIVE'
        ORDER BY o.name
        LIMIT 1
        """,
        (str(identity_id),),
    ).fetchone()

    return api, session_id, user, organisation


def _modules(api, organisation_id):
    rows = api.db.execute(
        """
        SELECT
            m.id,
            m.code,
            m.name,
            m.version,
            m.status,
            CASE
                WHEN e.status='ACTIVE' THEN 1
                ELSE 0
            END AS active
        FROM modules m
        LEFT JOIN module_entitlements e
          ON e.module_id=m.id
         AND e.organisation_id=?
        WHERE m.status='ENABLED'
        ORDER BY m.name
        """,
        (str(organisation_id) if organisation_id else "",),
    ).fetchall()

    return [
        {
            "id": row["id"],
            "code": row["code"],
            "name": row["name"],
            "version": row["version"],
            "active": bool(row["active"]),
        }
        for row in rows
    ]


@router.get("/context")
def context(request: Request):
    api, session_id, user, organisation = _session_context(request)

    organisation_id = (
        UUID(str(organisation["id"]))
        if organisation is not None
        else None
    )

    resolved = api.resolve_context(
        request_id=str(
            getattr(request.state, "request_id", None)
            or uuid4()
        ),
        session_id=session_id,
        organisation_id=organisation_id,
    )

    return {
        "data": {
            "user": {
                "id": user["id"],
                "username": user["username"],
                "display_name": user["display_name"],
                "platform_level": user["platform_level"],
            },
            "company": (
                None
                if organisation is None
                else {
                    "id": organisation["id"],
                    "code": organisation["code"],
                    "name": organisation["name"],
                    "status": organisation["status"],
                }
            ),
            "modules": _modules(
                api,
                organisation_id,
            ),
            "permissions": sorted(resolved.permissions),
            "entitlements": sorted(resolved.entitlements),
        },
    }

