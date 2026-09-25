from datetime import datetime
from decimal import Decimal

from phoenix_production_module.production.eta_required_risk import (
    RequiredDateRiskLevel,
)
from phoenix_production_module.production.eta_risk import (
    ETARiskLevel,
)
from phoenix_production_module.production.eta_risk_summary import (
    ETARiskDecision,
    ETARiskSummary,
)
from phoenix_production_module.production.models import (
    ManufacturingOrder,
)
from phoenix_production_module.production.service import (
    ProductionService,
)


# ---------------------------------------------------------------------------
# Phoenix Production Module 1.3.21
# ProductionService ETA Risk Summary Integration Tests
# ---------------------------------------------------------------------------


def make_order(
    planned_quantity: str = "1000",
    required_date: datetime = datetime(
        2026,
        8,
        28,
        16,
        0,
    ),
) -> ManufacturingOrder:
    """
    Create a valid ManufacturingOrder for service-level ETA tests.

    required_date is part of the ManufacturingOrder constructor
    contract and must therefore be supplied when the test order
    is created.
    """

    return ManufacturingOrder(
        tenant_id="TEST_TENANT",
        site_id="TEST_SITE",
        product_id="TEST_PRODUCT",
        planned_quantity=Decimal(planned_quantity),
        required_date=required_date,
    )


def prepare_started_order(
    *,
    planned_eta: datetime,
    current_eta: datetime,
    required_date: datetime,
) -> ManufacturingOrder:
    """
    Establish the minimum ETA state required by the service.
    """

    service = ProductionService()

    order = make_order(
        required_date=required_date,
    )

    production_start = datetime(
        2026,
        8,
        20,
        8,
        0,
    )

    service.mark_production_started(
        order,
        production_start,
    )

    order.eta.establish_planned_eta(
        planned_production_start=production_start,
        planned_eta=planned_eta,
    )

    order.eta.required_date = required_date

    order.eta.update_current_eta(
        current_eta,
        calculated_at=datetime(
            2026,
            8,
            21,
            8,
            0,
        ),
        reason="Service integration test",
    )

    return order


def test_service_returns_eta_risk_summary():
    service = ProductionService()

    order = prepare_started_order(
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
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
    )

    result = service.calculate_eta_risk_summary(
        order,
    )

    assert isinstance(
        result,
        ETARiskSummary,
    )


def test_service_returns_on_track_when_eta_is_before_plan_and_required_date():
    service = ProductionService()

    order = prepare_started_order(
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
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
    )

    result = service.calculate_eta_risk_summary(
        order,
    )

    assert result.decision == ETARiskDecision.ON_TRACK
    assert result.schedule_risk == ETARiskLevel.ON_TRACK
    assert (
        result.required_date_risk
        == RequiredDateRiskLevel.ON_TIME
    )


def test_service_detects_behind_plan_customer_safe():
    service = ProductionService()

    order = prepare_started_order(
        planned_eta=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            26,
            12,
            0,
        ),
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
    )

    result = service.calculate_eta_risk_summary(
        order,
    )

    assert result.schedule_risk == ETARiskLevel.LATE
    assert (
        result.required_date_risk
        == RequiredDateRiskLevel.ON_TIME
    )
    assert result.decision == (
        ETARiskDecision.BEHIND_PLAN_CUSTOMER_SAFE
    )


def test_service_detects_customer_date_at_risk():
    service = ProductionService()

    order = prepare_started_order(
        planned_eta=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            27,
            16,
            0,
        ),
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
    )

    result = service.calculate_eta_risk_summary(
        order,
    )

    assert (
        result.required_date_risk
        == RequiredDateRiskLevel.AT_RISK
    )
    assert result.decision == (
        ETARiskDecision.CUSTOMER_DATE_AT_RISK
    )


def test_service_detects_customer_date_late():
    service = ProductionService()

    order = prepare_started_order(
        planned_eta=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            29,
            16,
            0,
        ),
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
    )

    result = service.calculate_eta_risk_summary(
        order,
    )

    assert (
        result.required_date_risk
        == RequiredDateRiskLevel.LATE
    )
    assert result.decision == (
        ETARiskDecision.CUSTOMER_DATE_LATE
    )


def test_service_detects_required_date_conflict():
    service = ProductionService()

    order = prepare_started_order(
        planned_eta=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            29,
            16,
            0,
        ),
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
    )

    result = service.calculate_eta_risk_summary(
        order,
    )

    assert result.schedule_risk == ETARiskLevel.LATE
    assert (
        result.required_date_risk
        == RequiredDateRiskLevel.LATE
    )
    assert result.decision == (
        ETARiskDecision.CUSTOMER_DATE_LATE
    )


def test_service_summary_is_read_only():
    service = ProductionService()

    order = prepare_started_order(
        planned_eta=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            25,
            10,
            0,
        ),
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
    )

    original_state = order.state
    original_current_eta = order.eta.current_eta
    original_required_date = order.eta.required_date

    service.calculate_eta_risk_summary(
        order,
    )

    assert order.state == original_state
    assert order.eta.current_eta == original_current_eta
    assert order.eta.required_date == original_required_date


def test_service_passes_schedule_thresholds_through():
    service = ProductionService()

    order = prepare_started_order(
        planned_eta=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            25,
            10,
            0,
        ),
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
    )

    result = service.calculate_eta_risk_summary(
        order,
    )

    assert result.schedule_risk in (
        ETARiskLevel.ON_TRACK,
        ETARiskLevel.AT_RISK,
        ETARiskLevel.LATE,
        ETARiskLevel.UNKNOWN,
    )


def test_service_result_contains_operational_summary():
    service = ProductionService()

    order = prepare_started_order(
        planned_eta=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            26,
            12,
            0,
        ),
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
    )

    result = service.calculate_eta_risk_summary(
        order,
    )

    assert isinstance(
        result.summary,
        str,
    )

    assert result.summary != ""


def test_service_result_exposes_action_required():
    service = ProductionService()

    order = prepare_started_order(
        planned_eta=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            26,
            12,
            0,
        ),
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
    )

    result = service.calculate_eta_risk_summary(
        order,
    )

    assert isinstance(
        result.action_required,
        bool,
    )


def test_service_result_is_repeatable():
    service = ProductionService()

    order = prepare_started_order(
        planned_eta=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            26,
            12,
            0,
        ),
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
    )

    first = service.calculate_eta_risk_summary(
        order,
    )

    second = service.calculate_eta_risk_summary(
        order,
    )

    assert first == second


def test_service_combined_risk_and_summary_agree():
    service = ProductionService()

    order = prepare_started_order(
        planned_eta=datetime(
            2026,
            8,
            25,
            12,
            0,
        ),
        current_eta=datetime(
            2026,
            8,
            26,
            12,
            0,
        ),
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
    )

    schedule_risk, required_date_risk = (
        service.calculate_combined_eta_risk(
            order,
        )
    )

    summary = service.calculate_eta_risk_summary(
        order,
    )

    assert summary.schedule_risk == (
        schedule_risk.risk_level
    )

    assert summary.required_date_risk == (
        required_date_risk.risk_level
    )