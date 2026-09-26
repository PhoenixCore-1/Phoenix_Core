"""FastAPI transport adapter for Phoenix Core.

The adapter owns HTTP concerns only. Business authority remains in CoreApi
and Core application services.
"""

from urllib.parse import urlparse
from uuid import UUID, uuid4

from fastapi import FastAPI, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from phoenix_core.api.application import CoreApi
from phoenix_core.api.contracts import error_from_exception
from phoenix_core.errors import (
    AuthenticationError,
    AuthorizationError,
    PhoenixError,
    ValidationError,
)
from phoenix_core.http_api.baseline import router as baseline_router
from phoenix_system.api.users import router as system_users_router
from phoenix_system.api.companies import router as system_companies_router
from phoenix_system.api.modules import router as system_modules_router
from phoenix_core.http_api.legal import router as legal_router
from phoenix_core.http_api.ip import router as ip_router
from phoenix_core.http_api.company import router as company_router
from phoenix_core.http_api.compliance import router as compliance_router
from phoenix_core.http_api.evidence import router as evidence_router
from phoenix_core.http_api.monitoring import router as monitoring_router
from phoenix_core.http_api.reports import router as reports_router
from phoenix_core.http_api.settings import router as settings_router
from phoenix_core.http_api.visibility import router as visibility_router
from phoenix_core.http_api.workspaces import router as workspace_router
from phoenix_core.http_api.production import router as production_router
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.migration_runner import apply_all as apply_all_migrations
from phoenix_production_module import __module_code__, __module_name__, __version__


SESSION_COOKIE = "phoenix_session"
ORGANISATION_HEADER = "X-Phoenix-Organisation"
REQUEST_ID_HEADER = "X-Request-ID"

_MUTATING_METHODS = {
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
}

# Local Vite development origins.
_ALLOWED_DEV_ORIGINS = {
    "http://localhost:5174",
    "http://127.0.0.1:5174",
}


def _request_id(request: Request) -> str:
    """Return the incoming request ID or generate one."""
    return (
        request.headers.get(REQUEST_ID_HEADER)
        or str(uuid4())
    )


def _session_id(
    request: Request,
    core_api: CoreApi,
) -> UUID:
    """Resolve the Phoenix session cookie to a session ID."""

    token = request.cookies.get(SESSION_COOKIE)

    if not token:
        raise AuthenticationError(
            "Authentication required."
        )

    return core_api.resolve_session_id(token)


def _organisation_id(
    request: Request,
) -> UUID | None:
    """Read the optional Phoenix organisation context."""

    value = request.headers.get(
        ORGANISATION_HEADER
    )

    if not value:
        return None

    try:
        return UUID(value)
    except ValueError as exc:
        raise ValidationError(
            "Invalid organisation context."
        ) from exc


def _validate_same_origin(
    request: Request,
) -> None:
    """Reject cross-origin state-changing browser requests.

    Phoenix uses an HTTP-only session cookie, so state-changing requests need a
    browser-origin check in addition to SameSite cookie protection.

    Requests without an Origin header remain valid for non-browser/API clients.

    Local Vite development origins are explicitly allowed because the frontend
    runs on port 5174 while Phoenix Core runs on port 8000.
    """

    if request.method not in _MUTATING_METHODS:
        return

    origin = request.headers.get("Origin")

    if not origin:
        return

    parsed = urlparse(origin)
    host = request.headers.get("host")

    if (
        not parsed.scheme
        or not parsed.netloc
        or not host
    ):
        raise ValidationError(
            "Invalid request origin."
        )

    forwarded_proto = request.headers.get(
        "x-forwarded-proto"
    )

    request_scheme = (
        forwarded_proto.split(",", 1)[0].strip()
        if forwarded_proto
        else request.url.scheme
    )

    expected = (
        f"{request_scheme}://{host}"
    )

    normalized_origin = origin.rstrip("/")
    normalized_expected = expected.rstrip("/")

    if (
        normalized_origin != normalized_expected
        and normalized_origin
        not in _ALLOWED_DEV_ORIGINS
    ):
        raise ValidationError(
            "Cross-origin state-changing requests "
            "are not allowed."
        )


def _error_response(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Convert Phoenix exceptions into the API error contract."""

    api_error = error_from_exception(
        exc,
        request_id=getattr(
            request.state,
            "request_id",
            _request_id(request),
        ),
    )

    status_code = 500

    if isinstance(exc, AuthenticationError):
        status_code = 401
    elif isinstance(exc, AuthorizationError):
        status_code = 403
    elif isinstance(exc, ValidationError):
        status_code = 422
    elif isinstance(exc, PhoenixError):
        status_code = 400

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(api_error),
    )


def create_development_app(
    database_path: str = ".local/phoenix_core_v1_dev.db",
    db=None,
) -> FastAPI:
    """Create the Phoenix Core V1 development application."""

    app = FastAPI(
        title="Phoenix Core",
        version="1.0.0",
    )

    if db is None:
        db = SQLiteDatabase(database_path)

    apply_all_migrations(db)

    core_api = CoreApi(db)

    app.state.db = db
    app.state.core_api = core_api

    @app.middleware("http")
    async def phoenix_request_middleware(
        request: Request,
        call_next,
    ):
        request.state.request_id = _request_id(
            request
        )

        try:
            _validate_same_origin(request)

            response = await call_next(request)

            response.headers[
                REQUEST_ID_HEADER
            ] = request.state.request_id

            return response

        except Exception as exc:
            return _error_response(
                request,
                exc,
            )

    @app.get("/health")
    async def health():
        return {
            "data": {
                "status": "ok",
                "service": "phoenix-core",
            },
            "request_id": str(uuid4()),
        }

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    @app.post("/api/v1/auth/login")
    async def login(
        request: Request,
        response: Response,
    ):
        payload = await request.json()

        username = payload.get("username")
        password = payload.get("password")
        organisation_id = payload.get(
            "organisation_id"
        )

        if not username or not password:
            raise ValidationError(
                "Username and password are required."
            )

        organisation_uuid = None

        if organisation_id:
            try:
                organisation_uuid = UUID(
                    organisation_id
                )
            except ValueError as exc:
                raise ValidationError(
                    "Invalid organisation context."
                ) from exc

        result = core_api.authenticate(
            request_id=request.state.request_id,
            username=username,
            password=password,
            organisation_id=organisation_uuid,
        )

        # CoreApi.authenticate returns ApiResponse.
        # The actual opaque browser credential is stored
        # in result.data["token"].
        token = result.data["token"]

        response.set_cookie(
            key=SESSION_COOKIE,
            value=token,
            httponly=True,
            samesite="lax",
            secure=True,
            path="/",
        )

        return {
            "data": result.data,
            "request_id": request.state.request_id,
        }

    @app.post("/api/v1/auth/logout")
    async def logout(
        request: Request,
        response: Response,
    ):
        token = request.cookies.get(
            SESSION_COOKIE
        )

        if token:
            core_api.revoke_session(
                request_id=request.state.request_id,
                token=token,
            )

        response.delete_cookie(
            key=SESSION_COOKIE,
            path="/",
        )

        return {
            "data": {
                "status": "ok",
            },
            "request_id": request.state.request_id,
        }

    # ------------------------------------------------------------------
    # Current user / organisation
    # ------------------------------------------------------------------

    @app.get("/api/v1/me")
    async def me(request: Request):
        session_id = _session_id(
            request,
            core_api,
        )

        organisation_id = _organisation_id(
            request
        )

        result = core_api.get_current_user(
            request_id=request.state.request_id,
            session_id=session_id,
            organisation_id=organisation_id,
        )

        return {
            "data": result.data,
            "request_id": request.state.request_id,
        }

    @app.get("/api/v1/me/identity")
    async def me_identity(
        request: Request,
    ):
        session_id = _session_id(
            request,
            core_api,
        )

        organisation_id = _organisation_id(
            request
        )

        result = core_api.get_current_identity(
            request_id=request.state.request_id,
            session_id=session_id,
            organisation_id=organisation_id,
        )

        return {
            "data": result.data,
            "request_id": request.state.request_id,
        }

    @app.get("/api/v1/me/organisation")
    async def me_organisation(
        request: Request,
    ):
        session_id = _session_id(
            request,
            core_api,
        )

        organisation_id = _organisation_id(
            request
        )

        result = core_api.get_current_organisation(
            request_id=request.state.request_id,
            session_id=session_id,
            organisation_id=organisation_id,
        )

        return {
            "data": result.data,
            "request_id": request.state.request_id,
        }

    @app.get("/api/v1/me/permissions")
    async def me_permissions(
        request: Request,
    ):
        session_id = _session_id(
            request,
            core_api,
        )

        organisation_id = _organisation_id(
            request
        )

        context = core_api.resolve_context(
            request_id=request.state.request_id,
            session_id=session_id,
            organisation_id=organisation_id,
        )

        permissions = sorted(
            context.permissions
        )

        return {
            "data": {
                "permissions": permissions,
            },
            "request_id": request.state.request_id,
        }

    @app.get("/api/v1/me/entitlements")
    async def me_entitlements(
        request: Request,
    ):
        session_id = _session_id(
            request,
            core_api,
        )

        organisation_id = _organisation_id(
            request
        )

        context = core_api.resolve_context(
            request_id=request.state.request_id,
            session_id=session_id,
            organisation_id=organisation_id,
        )

        entitlements = sorted(
            context.entitlements
        )

        return {
            "data": {
                "entitlements": entitlements,
            },
            "request_id": request.state.request_id,
        }

    # ------------------------------------------------------------------
    # Phoenix Core HTTP routers
    # ------------------------------------------------------------------

    app.include_router(company_router)
    app.include_router(baseline_router)
    app.include_router(system_users_router)
    app.include_router(system_companies_router)
    app.include_router(system_modules_router)
    app.include_router(legal_router)
    app.include_router(ip_router)
    app.include_router(compliance_router)
    app.include_router(evidence_router)
    app.include_router(monitoring_router)
    app.include_router(reports_router)
    app.include_router(settings_router)
    app.include_router(visibility_router)
    app.include_router(workspace_router)
    app.include_router(production_router)

    return app












