from fastapi.testclient import TestClient

from phoenix_core.errors import AuthorizationError
from phoenix_core.http_api import authorization
from phoenix_core.http_api.app import create_development_app


def _context():
    class FakeContext:
        organisation_id = "42"
        request_id = "wp6-slice5"
        session_id = "test-session"

    return FakeContext()


def _configure_context(monkeypatch, app, context):
    async def resolve(request):
        return context

    monkeypatch.setattr(
        authorization,
        "resolve_request_context",
        resolve,
    )

    monkeypatch.setattr(
        app.state.core_api,
        "require_permission",
        lambda context, permission: None,
    )


def test_operational_snapshot_requires_production_entitlement(
    monkeypatch,
):
    app = create_development_app()
    context = _context()

    _configure_context(monkeypatch, app, context)

    def deny_entitlement(context, entitlement):
        assert entitlement == "production"
        raise AuthorizationError(
            "Production entitlement required"
        )

    monkeypatch.setattr(
        app.state.core_api,
        "require_entitlement",
        deny_entitlement,
    )

    response = TestClient(app).get(
        "/api/v1/production/operational-snapshot"
    )

    assert response.status_code == 403


def test_operational_snapshot_requires_production_view_permission(
    monkeypatch,
):
    app = create_development_app()
    context = _context()

    _configure_context(monkeypatch, app, context)

    def allow_entitlement(context, entitlement):
        assert entitlement == "production"

    monkeypatch.setattr(
        app.state.core_api,
        "require_entitlement",
        allow_entitlement,
    )

    def deny_permission(context, permission):
        assert permission == "production.view"
        raise AuthorizationError(
            "Production view permission required"
        )

    monkeypatch.setattr(
        app.state.core_api,
        "require_permission",
        deny_permission,
    )

    response = TestClient(app).get(
        "/api/v1/production/operational-snapshot"
    )

    assert response.status_code == 403


def test_operational_snapshot_authorization_order(
    monkeypatch,
):
    app = create_development_app()
    context = _context()
    calls = []

    _configure_context(monkeypatch, app, context)

    def entitlement(context, entitlement):
        calls.append(("entitlement", entitlement))

    def permission(context, permission):
        calls.append(("permission", permission))

    monkeypatch.setattr(
        app.state.core_api,
        "require_entitlement",
        entitlement,
    )

    monkeypatch.setattr(
        app.state.core_api,
        "require_permission",
        permission,
    )

    response = TestClient(app).get(
        "/api/v1/production/operational-snapshot"
    )

    assert calls == [
        ("entitlement", "production"),
        ("permission", "production.view"),
    ]

    # Authorization completed successfully. The request may fail
    # later because this test intentionally has no production DB.
    assert response.status_code in (200, 500)


def test_release_order_requires_release_permission(
    monkeypatch,
):
    app = create_development_app()
    context = _context()

    context.identity_id = "test-identity"

    _configure_context(monkeypatch, app, context)

    def allow_entitlement(context, entitlement):
        assert entitlement == "production"

    monkeypatch.setattr(
        app.state.core_api,
        "require_entitlement",
        allow_entitlement,
    )

    def deny_permission(context, permission):
        assert permission == "production.order.release"
        raise AuthorizationError(
            "Production order release permission required"
        )

    monkeypatch.setattr(
        app.state.core_api,
        "require_permission",
        deny_permission,
    )

    response = TestClient(app).post(
        "/api/v1/production/orders/1/release"
    )

    assert response.status_code == 403


def test_release_order_authorization_order(
    monkeypatch,
):
    app = create_development_app()
    context = _context()
    context.identity_id = "test-identity"
    calls = []

    _configure_context(monkeypatch, app, context)

    def entitlement(context, entitlement):
        calls.append(("entitlement", entitlement))

    def permission(context, permission):
        calls.append(("permission", permission))

    monkeypatch.setattr(
        app.state.core_api,
        "require_entitlement",
        entitlement,
    )

    monkeypatch.setattr(
        app.state.core_api,
        "require_permission",
        permission,
    )

    response = TestClient(app).post(
        "/api/v1/production/orders/1/release"
    )

    assert calls == [
        ("entitlement", "production"),
        ("permission", "production.order.release"),
    ]

    # Authorization completed successfully. The request may fail
    # later because this test intentionally has no production DB.
    assert response.status_code in (200, 404, 500)
