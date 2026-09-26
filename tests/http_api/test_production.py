from decimal import Decimal
from types import SimpleNamespace

from fastapi.testclient import TestClient

from phoenix_core.http_api.app import create_development_app
from phoenix_core.http_api import authorization
from phoenix_production_module.production import service as production_service


def _performance_result():
    return SimpleNamespace(
        organisation_id="11111111-1111-4111-8111-111111111111",
        order_count=4,
        open_order_count=1,
        completed_order_count=3,
        planned_quantity=Decimal("100"),
        actual_quantity=Decimal("75"),
        completion_ratio=Decimal("0.75"),
        total_production_seconds=Decimal("3600"),
        average_production_seconds=Decimal("1200"),
        average_actual_rate=Decimal("0.0208333333"),
    )


def test_production_performance_requires_authentication(tmp_path):
    app = create_development_app(
        str(tmp_path / "core.db")
    )

    client = TestClient(
        app,
        base_url="https://testserver",
    )

    response = client.get(
        "/api/v1/production/performance",
        headers={
            "X-Phoenix-Organisation":
                "00000000-0000-4000-8000-000000000001",
        },
    )

    assert response.status_code == 401


def test_production_performance_passes_tenant_and_date_filters(
    tmp_path,
    monkeypatch,
):
    app = create_development_app(
        str(tmp_path / "core.db")
    )

    organisation_id = "11111111-1111-4111-8111-111111111111"

    context = SimpleNamespace(
        organisation_id=organisation_id,
        request_id="test-request-001",
    )

    captured = {}

    async def fake_resolve_request_context(request):
        request.state.core_context = context
        return context

    def fake_require_permission(context, permission):
        assert permission == "production.view"

    def fake_require_entitlement(context, module_code):
        assert module_code == "production"

    def fake_calculate_performance(
        self,
        db,
        *,
        organisation_id,
        start_at=None,
        end_at=None,
    ):
        captured["db"] = db
        captured["organisation_id"] = organisation_id
        captured["start_at"] = start_at
        captured["end_at"] = end_at
        return _performance_result()

    monkeypatch.setattr(
        authorization,
        "resolve_request_context",
        fake_resolve_request_context,
    )

    app.state.core_api.require_permission = fake_require_permission
    app.state.core_api.require_entitlement = fake_require_entitlement

    monkeypatch.setattr(
        production_service.ProductionService,
        "calculate_performance",
        fake_calculate_performance,
    )

    client = TestClient(
        app,
        base_url="https://testserver",
    )

    response = client.get(
        "/api/v1/production/performance",
        params={
            "start_at": "2026-09-01T00:00:00",
            "end_at": "2026-09-30T00:00:00",
        },
        headers={
            "X-Phoenix-Organisation": organisation_id,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["request_id"] == "test-request-001"

    assert body["data"]["organisation_id"] == organisation_id
    assert body["data"]["order_count"] == 4
    assert body["data"]["open_order_count"] == 1
    assert body["data"]["completed_order_count"] == 3
    assert body["data"]["planned_quantity"] == "100"
    assert body["data"]["actual_quantity"] == "75"
    assert body["data"]["completion_ratio"] == "0.75"

    assert captured["db"] is app.state.core_api.db
    assert captured["organisation_id"] == organisation_id
    assert captured["start_at"].isoformat() == "2026-09-01T00:00:00"
    assert captured["end_at"].isoformat() == "2026-09-30T00:00:00"
