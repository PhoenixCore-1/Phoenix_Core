from datetime import datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from phoenix_core.http_api.app import create_development_app
from phoenix_core.http_api import authorization
from phoenix_production_module.production.service import ProductionService


def _client(monkeypatch):
    app = create_development_app()

    class FakeContext:
        organisation_id = "42"
        request_id = "wp6-slice4"
        session_id = "test-session"

    context = FakeContext()

    async def fake_resolve_request_context(request):
        return context

    monkeypatch.setattr(
        authorization,
        "resolve_request_context",
        fake_resolve_request_context,
    )

    monkeypatch.setattr(
        app.state.core_api,
        "require_permission",
        lambda context, permission: None,
    )

    monkeypatch.setattr(
        app.state.core_api,
        "require_entitlement",
        lambda context, entitlement: None,
    )

    return app, context


def test_operational_snapshot_http_path(monkeypatch):
    app, context = _client(monkeypatch)

    class FakePerformance:
        organisation_id = "42"
        order_count = 2
        open_order_count = 1
        completed_order_count = 1
        planned_quantity = Decimal("100")
        actual_quantity = Decimal("75")
        completion_ratio = Decimal("0.75")
        total_production_seconds = Decimal("3600")
        average_production_seconds = Decimal("1800")
        average_actual_rate = Decimal("0.0208333333")

    performance_context = {}

    def fake_performance(self, db, **kwargs):
        performance_context.update(kwargs)
        return FakePerformance()

    monkeypatch.setattr(
        ProductionService,
        "calculate_performance",
        fake_performance,
    )

    from phoenix_core.http_api import production

    order_context = {}

    def fake_operational_orders(db, **kwargs):
        order_context.update(kwargs)

        return [
            {
                "production_order_id": 1001,
                "status": "In Production",
                "planned_quantity": "100",
                "required_date": "2026-09-30T00:00:00",
                "eta": {
                    "production_order_id": 1001,
                    "planned_eta": "2026-09-29T00:00:00",
                    "current_eta": "2026-10-01T00:00:00",
                    "required_date": "2026-09-30T00:00:00",
                    "schedule_risk": "MEDIUM",
                    "required_date_risk": "HIGH",
                    "decision": "ACTION_REQUIRED",
                    "action_required": True,
                    "summary": "Required date at risk",
                },
                "active_hold_count": 1,
            }
        ]

    monkeypatch.setattr(
        production,
        "_operational_orders",
        fake_operational_orders,
    )

    client = TestClient(
        app,
        raise_server_exceptions=True,
    )

    response = client.get(
        "/api/v1/production/operational-snapshot",
        params={
            "start_at": "2026-09-01T00:00:00",
            "end_at": "2026-09-30T00:00:00",
        },
    )

    assert response.status_code == 200

    body = response.json()

    expected_start = datetime(2026, 9, 1)
    expected_end = datetime(2026, 9, 30)

    assert performance_context["organisation_id"] == "42"
    assert performance_context["start_at"] == expected_start
    assert performance_context["end_at"] == expected_end

    assert order_context["organisation_id"] == "42"
    assert order_context["start_at"] == expected_start
    assert order_context["end_at"] == expected_end

    assert body["request_id"] == "wp6-slice4"
    assert body["data"]["organisation_id"] == "42"
    assert body["data"]["order_count"] == 1

    assert body["data"]["performance"]["order_count"] == 2
    assert body["data"]["performance"]["planned_quantity"] == "100"
    assert body["data"]["performance"]["actual_quantity"] == "75"

    order = body["data"]["orders"][0]

    assert order["production_order_id"] == 1001
    assert order["active_hold_count"] == 1
    assert order["eta"]["required_date_risk"] == "HIGH"
    assert order["eta"]["action_required"] is True


def test_operational_snapshot_rejects_unauthenticated(monkeypatch):
    app = create_development_app()

    async def reject(request):
        raise authorization.AuthenticationError(
            "Authentication required"
        )

    monkeypatch.setattr(
        authorization,
        "resolve_request_context",
        reject,
    )

    client = TestClient(app)

    response = client.get(
        "/api/v1/production/operational-snapshot"
    )

    assert response.status_code == 401
