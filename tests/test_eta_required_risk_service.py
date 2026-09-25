from datetime import datetime
from decimal import Decimal

import pytest

from phoenix_production_module.production.eta_required_risk import (
    RequiredDateRisk,
    RequiredDateRiskLevel,
    RequiredDateRiskThresholds,
)
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
# Phoenix Production Module 1.3.19
# Required-Date Risk Service Integration
# ---------------------------------------------------------------------------


def make_order(
    *,
    quantity: str = "1000",
) -> ManufacturingOrder:
    return ManufacturingOrder(
        tenant_id="TEST_TENANT",
        site_id="TEST_SITE",
        product_id="TEST_PRODUCT",
        planned_quantity=Decimal(quantity),
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
    )


def test_service_calculate_required_date_risk_reads_order_eta_values():
    service = ProductionService()
    order = make_order()

    required_date = datetime(
        2026,
        8,
        28,
        16,
        0,
    )

    current_eta = datetime(
        2026,
        8,
        26,
        16,
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
        planned_eta=datetime(
            2026,
            8,
            25,
            16,
            0,
        ),
    )

    order.eta.required_date = required_date

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

    result = service.calculate_required_date_risk(
        order,
    )

    assert isinstance(
        result,
        RequiredDateRisk,
    )

    assert result.required_date == required_date
    assert result.current_eta == current_eta
    assert result.variance_hours == Decimal("-48")
    assert result.risk_level == RequiredDateRiskLevel.ON_TIME


def test_service_required_date_risk_can_use_explicit_values():
    service = ProductionService()
    order = make_order()

    result = service.calculate_required_date_risk(
        order,
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            28,
            20,
            0,
        ),
    )

    assert result.variance_hours == Decimal("4")
    assert result.risk_level == RequiredDateRiskLevel.LATE


def test_service_get_required_date_risk_level_returns_level_only():
    service = ProductionService()
    order = make_order()

    order.eta.required_date = datetime(
        2026,
        8,
        28,
        16,
        0,
    )

    service.update_current_eta(
        order,
        datetime(
            2026,
            8,
            28,
            20,
            0,
        ),
        calculated_at=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        reason="Test delay",
    )

    result = service.get_required_date_risk_level(
        order,
    )

    assert result == RequiredDateRiskLevel.LATE


def test_service_can_meet_required_date_returns_true_when_on_time():
    service = ProductionService()
    order = make_order()

    order.eta.required_date = datetime(
        2026,
        8,
        28,
        16,
        0,
    )

    service.update_current_eta(
        order,
        datetime(
            2026,
            8,
            26,
            16,
            0,
        ),
        calculated_at=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        reason="Test ETA",
    )

    assert service.can_meet_required_date(
        order,
    )


def test_service_can_meet_required_date_returns_false_when_late():
    service = ProductionService()
    order = make_order()

    order.eta.required_date = datetime(
        2026,
        8,
        28,
        16,
        0,
    )

    service.update_current_eta(
        order,
        datetime(
            2026,
            8,
            29,
            16,
            0,
        ),
        calculated_at=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        reason="Test late ETA",
    )

    assert not service.can_meet_required_date(
        order,
    )


def test_service_required_date_risk_supports_custom_thresholds():
    service = ProductionService()
    order = make_order()

    result = service.calculate_required_date_risk(
        order,
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            28,
            12,
            0,
        ),
        risk_thresholds=RequiredDateRiskThresholds(
            at_risk_buffer_hours=Decimal("8"),
        ),
    )

    assert result.variance_hours == Decimal("-4")
    assert result.risk_level == RequiredDateRiskLevel.AT_RISK


def test_service_required_date_risk_uses_default_thresholds():
    service = ProductionService()
    order = make_order()

    result = service.calculate_required_date_risk(
        order,
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            28,
            12,
            0,
        ),
    )

    assert result.variance_hours == Decimal("-4")
    assert result.risk_level == RequiredDateRiskLevel.AT_RISK


def test_service_required_date_risk_identifies_missing_required_date():
    service = ProductionService()
    order = make_order()

    order.eta.required_date = None

    result = service.calculate_required_date_risk(
        order,
        current_eta=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
    )

    assert result.risk_level == RequiredDateRiskLevel.UNKNOWN
    assert result.variance is None


def test_service_required_date_risk_identifies_missing_current_eta():
    service = ProductionService()
    order = make_order()

    order.eta.required_date = datetime(
        2026,
        8,
        28,
        16,
        0,
    )

    result = service.calculate_required_date_risk(
        order,
    )

    assert result.risk_level == RequiredDateRiskLevel.UNKNOWN
    assert result.variance is None


def test_service_required_date_risk_identifies_completed_order():
    service = ProductionService()
    order = make_order()

    order.eta.required_date = datetime(
        2026,
        8,
        28,
        16,
        0,
    )

    order.eta.status = ETAStatus.COMPLETED

    result = service.calculate_required_date_risk(
        order,
        current_eta=datetime(
            2026,
            8,
            30,
            16,
            0,
        ),
    )

    assert result.risk_level == RequiredDateRiskLevel.COMPLETED


def test_service_required_date_risk_explicit_completed_overrides_order_state():
    service = ProductionService()
    order = make_order()

    result = service.calculate_required_date_risk(
        order,
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            30,
            16,
            0,
        ),
        completed=True,
    )

    assert result.risk_level == RequiredDateRiskLevel.COMPLETED


def test_service_required_date_risk_explicit_completed_false_is_respected():
    service = ProductionService()
    order = make_order()

    order.eta.status = ETAStatus.COMPLETED

    result = service.calculate_required_date_risk(
        order,
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            30,
            16,
            0,
        ),
        completed=False,
    )

    assert result.risk_level == RequiredDateRiskLevel.LATE


def test_service_required_date_risk_does_not_modify_order():
    service = ProductionService()
    order = make_order()

    required_date = datetime(
        2026,
        8,
        28,
        16,
        0,
    )

    current_eta = datetime(
        2026,
        8,
        26,
        16,
        0,
    )

    order.eta.required_date = required_date

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

    original_required_date = (
        order.eta.required_date
    )

    original_current_eta = (
        order.eta.current_eta
    )

    original_status = (
        order.eta.status
    )

    result = service.calculate_required_date_risk(
        order,
    )

    assert result.risk_level == RequiredDateRiskLevel.ON_TIME

    assert order.eta.required_date == (
        original_required_date
    )

    assert order.eta.current_eta == (
        original_current_eta
    )

    assert order.eta.status == (
        original_status
    )


def test_service_combined_eta_risk_returns_both_risk_views():
    service = ProductionService()
    order = make_order()

    order.eta.required_date = datetime(
        2026,
        8,
        28,
        16,
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
            16,
            0,
        ),
        calculated_at=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        reason="Test live ETA",
    )

    schedule_risk, required_date_risk = (
        service.calculate_combined_eta_risk(
            order,
        )
    )

    assert schedule_risk.risk_level == (
        ETARiskLevel.LATE
    )

    assert required_date_risk.risk_level == (
        RequiredDateRiskLevel.ON_TIME
    )


def test_service_combined_eta_risk_can_show_internal_late_but_customer_on_time():
    service = ProductionService()
    order = make_order()

    order.eta.required_date = datetime(
        2026,
        8,
        28,
        16,
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
            16,
            0,
        ),
        calculated_at=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        reason="Production behind plan",
    )

    schedule_risk, required_date_risk = (
        service.calculate_combined_eta_risk(
            order,
        )
    )

    assert schedule_risk.risk_level == (
        ETARiskLevel.LATE
    )

    assert required_date_risk.risk_level == (
        RequiredDateRiskLevel.ON_TIME
    )

    assert required_date_risk.can_meet_required_date


def test_service_combined_eta_risk_can_show_customer_date_late():
    service = ProductionService()
    order = make_order()

    order.eta.required_date = datetime(
        2026,
        8,
        28,
        16,
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
        planned_eta=datetime(
            2026,
            8,
            27,
            16,
            0,
        ),
    )

    service.update_current_eta(
        order,
        datetime(
            2026,
            8,
            29,
            16,
            0,
        ),
        calculated_at=datetime(
            2026,
            8,
            27,
            12,
            0,
        ),
        reason="Customer date risk",
    )

    schedule_risk, required_date_risk = (
        service.calculate_combined_eta_risk(
            order,
        )
    )

    assert schedule_risk.risk_level == (
        ETARiskLevel.LATE
    )

    assert required_date_risk.risk_level == (
        RequiredDateRiskLevel.LATE
    )

    assert not required_date_risk.can_meet_required_date


def test_service_combined_eta_risk_accepts_separate_thresholds():
    service = ProductionService()
    order = make_order()

    order.eta.required_date = datetime(
        2026,
        8,
        28,
        16,
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
            28,
            8,
            0,
        ),
        calculated_at=datetime(
            2026,
            8,
            27,
            12,
            0,
        ),
        reason="Threshold test",
    )

    schedule_risk, required_date_risk = (
        service.calculate_combined_eta_risk(
            order,
            schedule_risk_thresholds=ETARiskThresholds(
                at_risk_hours=Decimal("4"),
                late_hours=Decimal("8"),
            ),
            required_date_risk_thresholds=(
                RequiredDateRiskThresholds(
                    at_risk_buffer_hours=Decimal("12"),
                )
            ),
        )
    )

    assert schedule_risk.risk_level == (
        ETARiskLevel.LATE
    )

    assert required_date_risk.risk_level == (
        RequiredDateRiskLevel.AT_RISK
    )


def test_service_required_date_risk_result_is_read_only():
    service = ProductionService()
    order = make_order()

    order.eta.required_date = datetime(
        2026,
        8,
        28,
        16,
        0,
    )

    service.update_current_eta(
        order,
        datetime(
            2026,
            8,
            26,
            16,
            0,
        ),
        calculated_at=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        reason="Read-only test",
    )

    result = service.calculate_required_date_risk(
        order,
    )

    assert result.required_date == (
        order.eta.required_date
    )

    assert result.current_eta == (
        order.eta.current_eta
    )

    assert result.variance_hours == Decimal("-48")


def test_service_required_date_risk_supports_exact_required_date():
    service = ProductionService()
    order = make_order()

    result = service.calculate_required_date_risk(
        order,
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
    )

    assert result.variance_hours == Decimal("0")
    assert result.risk_level == (
        RequiredDateRiskLevel.AT_RISK
    )

    assert result.can_meet_required_date


def test_service_required_date_risk_supports_ahead_schedule():
    service = ProductionService()
    order = make_order()

    result = service.calculate_required_date_risk(
        order,
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            20,
            16,
            0,
        ),
    )

    assert result.variance_hours == Decimal("-192")
    assert result.risk_level == (
        RequiredDateRiskLevel.ON_TIME
    )

    assert result.can_meet_required_date


def test_service_required_date_risk_supports_one_minute_late():
    service = ProductionService()
    order = make_order()

    result = service.calculate_required_date_risk(
        order,
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            28,
            16,
            1,
        ),
    )

    assert result.risk_level == (
        RequiredDateRiskLevel.LATE
    )

    assert not result.can_meet_required_date


def test_service_required_date_risk_supports_material_wait_status():
    service = ProductionService()
    order = make_order()

    order.eta.required_date = datetime(
        2026,
        8,
        28,
        16,
        0,
    )

    order.eta.status = ETAStatus.MATERIAL_WAIT

    result = service.calculate_required_date_risk(
        order,
        current_eta=datetime(
            2026,
            8,
            28,
            8,
            0,
        ),
    )

    assert result.risk_level == (
        RequiredDateRiskLevel.AT_RISK
    )


def test_service_required_date_risk_supports_not_started_status():
    service = ProductionService()
    order = make_order()

    order.eta.required_date = datetime(
        2026,
        8,
        28,
        16,
        0,
    )

    order.eta.status = ETAStatus.NOT_STARTED

    result = service.calculate_required_date_risk(
        order,
        current_eta=datetime(
            2026,
            8,
            26,
            16,
            0,
        ),
    )

    assert result.risk_level == (
        RequiredDateRiskLevel.ON_TIME
    )


def test_service_required_date_risk_supports_unknown_status():
    service = ProductionService()
    order = make_order()

    order.eta.required_date = datetime(
        2026,
        8,
        28,
        16,
        0,
    )

    order.eta.status = ETAStatus.UNKNOWN

    result = service.calculate_required_date_risk(
        order,
        current_eta=datetime(
            2026,
            8,
            29,
            16,
            0,
        ),
    )

    assert result.risk_level == (
        RequiredDateRiskLevel.LATE
    )


def test_service_combined_eta_risk_returns_independent_results():
    service = ProductionService()
    order = make_order()

    order.eta.required_date = datetime(
        2026,
        8,
        28,
        16,
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
            27,
            16,
            0,
        ),
        calculated_at=datetime(
            2026,
            8,
            26,
            12,
            0,
        ),
        reason="Independent risk test",
    )

    schedule_risk, required_date_risk = (
        service.calculate_combined_eta_risk(
            order,
        )
    )

    assert schedule_risk is not required_date_risk

    assert schedule_risk.planned_eta == (
        order.eta.planned_eta
    )

    assert required_date_risk.required_date == (
        order.eta.required_date
    )


def test_service_required_date_risk_preserves_reason():
    service = ProductionService()
    order = make_order()

    result = service.calculate_required_date_risk(
        order,
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            26,
            16,
            0,
        ),
    )

    assert result.reason == (
        "Live ETA is sufficiently before the required date"
    )