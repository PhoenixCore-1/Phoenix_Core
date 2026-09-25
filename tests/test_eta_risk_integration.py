from datetime import datetime
from decimal import Decimal

from phoenix_production_module.production.eta_risk import (
    ETARiskLevel,
    ETARiskThresholds,
)
from phoenix_production_module.production.models import (
    ETAStatus,
    ManufacturingOrder,
)
from phoenix_production_module.production.service import (
    ProductionService,
)


# ---------------------------------------------------------------------------
# Phoenix Production Module 1.3.17
# ETA Risk Integration
# ---------------------------------------------------------------------------


def make_order(
    qty="1000",
):
    return ManufacturingOrder(
        tenant_id="TEST_TENANT",
        site_id="TEST_SITE",
        product_id="TEST_PRODUCT",
        planned_quantity=Decimal(qty),
        required_date=datetime(2026, 8, 31),
    )


def test_service_eta_schedule_variance_reads_order_eta_values():
    service = ProductionService()
    order = make_order()

    planned_eta = datetime(
        2026,
        8,
        25,
        16,
        0,
    )

    current_eta = datetime(
        2026,
        8,
        25,
        20,
        0,
    )

    service.establish_planned_eta(
        order,
        planned_production_start=datetime(
            2026,
            8,
            25,
            8,
            0,
        ),
        planned_eta=planned_eta,
    )

    service.update_current_eta(
        order,
        current_eta,
        calculated_at=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        reason="Test live ETA",
    )

    result = service.calculate_eta_schedule_variance(
        order,
    )

    assert result.planned_eta == planned_eta
    assert result.current_eta == current_eta
    assert result.variance_hours == Decimal("4")
    assert result.risk_level == ETARiskLevel.ON_TRACK


def test_service_eta_schedule_variance_can_use_explicit_values():
    service = ProductionService()
    order = make_order()

    planned_eta = datetime(
        2026,
        8,
        25,
        16,
        0,
    )

    current_eta = datetime(
        2026,
        8,
        26,
        2,
        0,
    )

    result = service.calculate_eta_schedule_variance(
        order,
        planned_eta=planned_eta,
        current_eta=current_eta,
        status=ETAStatus.ON_TRACK,
    )

    assert result.planned_eta == planned_eta
    assert result.current_eta == current_eta
    assert result.variance_hours == Decimal("10")
    assert result.risk_level == ETARiskLevel.LATE
    assert result.status == ETAStatus.LATE


def test_service_eta_schedule_variance_uses_order_status_by_default():
    service = ProductionService()
    order = make_order()

    service.establish_planned_eta(
        order,
        planned_production_start=datetime(
            2026,
            8,
            25,
            8,
            0,
        ),
        planned_eta=datetime(
            2026,
            8,
            25,
            16,
            0,
        ),
    )

    service.update_current_eta(
        order,
        datetime(
            2026,
            8,
            26,
            2,
            0,
        ),
        calculated_at=datetime(
            2026,
            8,
            25,
            16,
            0,
        ),
        reason="Delayed production",
    )

    result = service.calculate_eta_schedule_variance(
        order,
    )

    assert result.status == ETAStatus.LATE
    assert result.risk_level == ETARiskLevel.LATE


def test_service_eta_risk_level_returns_only_risk_level():
    service = ProductionService()
    order = make_order()

    service.establish_planned_eta(
        order,
        planned_production_start=datetime(
            2026,
            8,
            25,
            8,
            0,
        ),
        planned_eta=datetime(
            2026,
            8,
            25,
            16,
            0,
        ),
    )

    service.update_current_eta(
        order,
        datetime(
            2026,
            8,
            25,
            21,
            0,
        ),
        calculated_at=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        reason="Production delay",
    )

    risk = service.get_eta_risk_level(
        order,
    )

    assert risk == ETARiskLevel.AT_RISK


def test_service_calculate_eta_status_returns_schedule_aware_status():
    service = ProductionService()
    order = make_order()

    service.establish_planned_eta(
        order,
        planned_production_start=datetime(
            2026,
            8,
            25,
            8,
            0,
        ),
        planned_eta=datetime(
            2026,
            8,
            25,
            16,
            0,
        ),
    )

    service.update_current_eta(
        order,
        datetime(
            2026,
            8,
            26,
            2,
            0,
        ),
        calculated_at=datetime(
            2026,
            8,
            25,
            16,
            0,
        ),
        reason="Production delay",
    )

    status = service.calculate_eta_status(
        order,
    )

    assert status == ETAStatus.LATE


def test_service_eta_risk_does_not_modify_order_eta():
    service = ProductionService()
    order = make_order()

    planned_eta = datetime(
        2026,
        8,
        25,
        16,
        0,
    )

    current_eta = datetime(
        2026,
        8,
        25,
        21,
        0,
    )

    service.establish_planned_eta(
        order,
        planned_production_start=datetime(
            2026,
            8,
            25,
            8,
            0,
        ),
        planned_eta=planned_eta,
    )

    service.update_current_eta(
        order,
        current_eta,
        calculated_at=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        reason="Test ETA",
    )

    original_planned = order.eta.planned_eta
    original_current = order.eta.current_eta
    original_status = order.eta.status

    result = service.calculate_eta_schedule_variance(
        order,
    )

    assert result.risk_level == ETARiskLevel.AT_RISK

    assert order.eta.planned_eta == original_planned
    assert order.eta.current_eta == original_current
    assert order.eta.status == original_status


def test_service_eta_risk_supports_custom_thresholds():
    service = ProductionService()
    order = make_order()

    result = service.calculate_eta_schedule_variance(
        order,
        planned_eta=datetime(
            2026,
            8,
            25,
            16,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            25,
            19,
            0,
        ),
        status=ETAStatus.ON_TRACK,
        risk_thresholds=ETARiskThresholds(
            at_risk_hours=Decimal("2"),
            late_hours=Decimal("6"),
        ),
    )

    assert result.variance_hours == Decimal("3")
    assert result.risk_level == ETARiskLevel.AT_RISK
    assert result.status == ETAStatus.AT_RISK


def test_service_eta_risk_can_identify_ahead_schedule():
    service = ProductionService()
    order = make_order()

    result = service.calculate_eta_schedule_variance(
        order,
        planned_eta=datetime(
            2026,
            8,
            25,
            16,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        status=ETAStatus.ON_TRACK,
    )

    assert result.variance_hours == Decimal("-4")
    assert result.risk_level == ETARiskLevel.ON_TRACK
    assert result.is_ahead


def test_service_eta_risk_identifies_exact_schedule():
    service = ProductionService()
    order = make_order()

    eta = datetime(
        2026,
        8,
        25,
        16,
        0,
    )

    result = service.calculate_eta_schedule_variance(
        order,
        planned_eta=eta,
        current_eta=eta,
        status=ETAStatus.ON_TRACK,
    )

    assert result.variance_hours == Decimal("0")
    assert result.risk_level == ETARiskLevel.ON_TRACK
    assert result.is_on_schedule


def test_service_eta_risk_preserves_material_wait_status():
    service = ProductionService()
    order = make_order()

    result = service.calculate_eta_schedule_variance(
        order,
        planned_eta=datetime(
            2026,
            8,
            25,
            16,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            26,
            2,
            0,
        ),
        status=ETAStatus.MATERIAL_WAIT,
    )

    assert result.risk_level == ETARiskLevel.LATE
    assert result.status == ETAStatus.MATERIAL_WAIT


def test_service_eta_risk_preserves_not_started_status():
    service = ProductionService()
    order = make_order()

    result = service.calculate_eta_schedule_variance(
        order,
        planned_eta=datetime(
            2026,
            8,
            25,
            16,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            26,
            2,
            0,
        ),
        status=ETAStatus.NOT_STARTED,
    )

    assert result.risk_level == ETARiskLevel.LATE
    assert result.status == ETAStatus.NOT_STARTED


def test_service_eta_risk_preserves_unknown_status():
    service = ProductionService()
    order = make_order()

    result = service.calculate_eta_schedule_variance(
        order,
        planned_eta=datetime(
            2026,
            8,
            25,
            16,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            26,
            2,
            0,
        ),
        status=ETAStatus.UNKNOWN,
    )

    assert result.risk_level == ETARiskLevel.LATE
    assert result.status == ETAStatus.UNKNOWN


def test_service_eta_risk_completed_order_is_completed():
    service = ProductionService()
    order = make_order()

    result = service.calculate_eta_schedule_variance(
        order,
        planned_eta=datetime(
            2026,
            8,
            25,
            16,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            25,
            20,
            0,
        ),
        status=ETAStatus.COMPLETED,
    )

    assert result.risk_level == ETARiskLevel.COMPLETED
    assert result.status == ETAStatus.COMPLETED


def test_service_eta_risk_handles_missing_planned_eta():
    service = ProductionService()
    order = make_order()

    result = service.calculate_eta_schedule_variance(
        order,
        current_eta=datetime(
            2026,
            8,
            25,
            16,
            0,
        ),
        status=ETAStatus.ON_TRACK,
    )

    assert result.risk_level == ETARiskLevel.UNKNOWN
    assert result.variance is None


def test_service_eta_risk_handles_missing_current_eta():
    service = ProductionService()
    order = make_order()

    result = service.calculate_eta_schedule_variance(
        order,
        planned_eta=datetime(
            2026,
            8,
            25,
            16,
            0,
        ),
        status=ETAStatus.ON_TRACK,
    )

    assert result.risk_level == ETARiskLevel.UNKNOWN
    assert result.variance is None


def test_service_eta_risk_reads_current_eta_after_live_eta_calculation():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(
            2026,
            8,
            20,
            8,
            0,
        ),
    )

    service.record_quantity(
        order,
        accepted=Decimal("500"),
    )

    service.establish_planned_eta(
        order,
        planned_production_start=datetime(
            2026,
            8,
            20,
            8,
            0,
        ),
        planned_eta=datetime(
            2026,
            8,
            21,
            8,
            0,
        ),
    )

    snapshot = service.calculate_live_eta_from_actual_rate(
        order,
        calculated_at=datetime(
            2026,
            8,
            20,
            18,
            0,
        ),
    )

    assert snapshot is not None
    assert order.eta.current_eta is not None

    result = service.calculate_eta_schedule_variance(
        order,
    )

    assert result.planned_eta == datetime(
        2026,
        8,
        21,
        8,
        0,
    )

    assert result.current_eta == order.eta.current_eta
    assert result.variance is not None


def test_service_eta_risk_can_follow_selected_rate_live_eta():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(
            2026,
            8,
            20,
            8,
            0,
        ),
    )

    service.record_quantity(
        order,
        accepted=Decimal("800"),
    )

    service.establish_planned_eta(
        order,
        planned_production_start=datetime(
            2026,
            8,
            20,
            8,
            0,
        ),
        planned_eta=datetime(
            2026,
            8,
            21,
            8,
            0,
        ),
    )

    snapshot = service.calculate_live_eta_from_selected_rate(
        order,
        calculated_at=datetime(
            2026,
            8,
            20,
            16,
            0,
        ),
        rolling_window_hours=Decimal("4"),
        quantity_produced=Decimal("600"),
        minimum_history_hours=Decimal("4"),
        high_confidence_hours=Decimal("8"),
    )

    assert snapshot is not None
    assert order.eta.current_eta is not None

    result = service.calculate_eta_schedule_variance(
        order,
    )

    assert result.planned_eta == datetime(
        2026,
        8,
        21,
        8,
        0,
    )

    assert result.current_eta == order.eta.current_eta
    assert result.variance is not None
    assert result.risk_level in (
        ETARiskLevel.ON_TRACK,
        ETARiskLevel.AT_RISK,
        ETARiskLevel.LATE,
    )


def test_service_eta_risk_result_contains_reason():
    service = ProductionService()
    order = make_order()

    result = service.calculate_eta_schedule_variance(
        order,
        planned_eta=datetime(
            2026,
            8,
            25,
            16,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            25,
            21,
            0,
        ),
        status=ETAStatus.ON_TRACK,
    )

    assert result.reason
    assert "schedule" in result.reason.lower()