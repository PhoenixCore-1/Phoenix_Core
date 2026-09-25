from datetime import datetime
from decimal import Decimal

import pytest

from phoenix_production_module.production.eta_operational_snapshot import (
    ETAOperationalSnapshot,
)
from phoenix_production_module.production.eta_required_risk import (
    RequiredDateRiskLevel,
    RequiredDateRiskThresholds,
)
from phoenix_production_module.production.eta_risk import (
    ETARiskLevel,
    ETARiskThresholds,
)
from phoenix_production_module.production.eta_risk_summary import (
    ETARiskDecision,
)
from phoenix_production_module.production.models import (
    ManufacturingOrder,
)
from phoenix_production_module.production.service import (
    ProductionService,
)


# ---------------------------------------------------------------------------
# Phoenix Production Module 1.3.23
# ProductionService Operational ETA Snapshot Integration Tests
# ---------------------------------------------------------------------------


def make_order(
    *,
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
    Create a valid ManufacturingOrder using the existing
    production model constructor contract.
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
    Establish the minimum production and ETA state required
    by ProductionService.
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
        reason="1.3.23 integration test",
    )

    return order


# ---------------------------------------------------------------------------
# Basic service integration
# ---------------------------------------------------------------------------


def test_service_returns_operational_eta_snapshot():
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

    result = service.calculate_eta_operational_snapshot(
        order,
    )

    assert isinstance(
        result,
        ETAOperationalSnapshot,
    )


def test_service_snapshot_contains_planned_eta():
    service = ProductionService()

    planned_eta = datetime(
        2026,
        8,
        25,
        16,
        0,
    )

    order = prepare_started_order(
        planned_eta=planned_eta,
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

    result = service.calculate_eta_operational_snapshot(
        order,
    )

    assert result.planned_eta == planned_eta


def test_service_snapshot_contains_current_eta():
    service = ProductionService()

    current_eta = datetime(
        2026,
        8,
        26,
        12,
        0,
    )

    order = prepare_started_order(
        planned_eta=datetime(
            2026,
            8,
            25,
            16,
            0,
        ),
        current_eta=current_eta,
        required_date=datetime(
            2026,
            8,
            28,
            16,
            0,
        ),
    )

    result = service.calculate_eta_operational_snapshot(
        order,
    )

    assert result.current_eta == current_eta


def test_service_snapshot_contains_required_date():
    service = ProductionService()

    required_date = datetime(
        2026,
        8,
        28,
        16,
        0,
    )

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
        required_date=required_date,
    )

    result = service.calculate_eta_operational_snapshot(
        order,
    )

    assert result.required_date == required_date


# ---------------------------------------------------------------------------
# ON TRACK
# ---------------------------------------------------------------------------


def test_service_snapshot_on_track():
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

    result = service.calculate_eta_operational_snapshot(
        order,
    )

    assert result.decision == ETARiskDecision.ON_TRACK
    assert result.schedule_risk == ETARiskLevel.ON_TRACK
    assert (
        result.required_date_risk
        == RequiredDateRiskLevel.ON_TIME
    )
    assert result.action_required is False
    assert result.is_on_track is True


# ---------------------------------------------------------------------------
# BEHIND PLAN / CUSTOMER SAFE
# ---------------------------------------------------------------------------


def test_service_snapshot_behind_plan_customer_safe():
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

    result = service.calculate_eta_operational_snapshot(
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

    assert result.action_required is True
    assert result.is_customer_safe is True


# ---------------------------------------------------------------------------
# CUSTOMER DATE AT RISK
# ---------------------------------------------------------------------------


def test_service_snapshot_customer_date_at_risk():
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

    result = service.calculate_eta_operational_snapshot(
        order,
    )

    assert (
        result.required_date_risk
        == RequiredDateRiskLevel.AT_RISK
    )

    assert result.decision == (
        ETARiskDecision.CUSTOMER_DATE_AT_RISK
    )

    assert result.action_required is True
    assert result.is_customer_at_risk is True


# ---------------------------------------------------------------------------
# CUSTOMER DATE LATE
# ---------------------------------------------------------------------------


def test_service_snapshot_customer_date_late():
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

    result = service.calculate_eta_operational_snapshot(
        order,
    )

    assert (
        result.required_date_risk
        == RequiredDateRiskLevel.LATE
    )

    assert result.decision == (
        ETARiskDecision.CUSTOMER_DATE_LATE
    )

    assert result.action_required is True
    assert result.is_customer_late is True
    assert result.is_customer_safe is False


# ---------------------------------------------------------------------------
# REQUIRED-DATE CONFLICT
# ---------------------------------------------------------------------------


def test_service_snapshot_required_date_conflict():
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

    result = service.calculate_eta_operational_snapshot(
        order,
    )

    assert result.decision in (
        ETARiskDecision.CUSTOMER_DATE_LATE,
        ETARiskDecision.REQUIRED_DATE_CONFLICT,
    )

    assert result.action_required is True


# ---------------------------------------------------------------------------
# Summary consistency
# ---------------------------------------------------------------------------


def test_service_snapshot_matches_risk_summary():
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

    summary = service.calculate_eta_risk_summary(
        order,
    )

    snapshot = service.calculate_eta_operational_snapshot(
        order,
    )

    assert snapshot.schedule_risk == (
        summary.schedule_risk
    )

    assert snapshot.required_date_risk == (
        summary.required_date_risk
    )

    assert snapshot.decision == (
        summary.decision
    )

    assert snapshot.action_required == (
        summary.action_required
    )

    assert snapshot.summary == (
        summary.summary
    )


# ---------------------------------------------------------------------------
# Read-only behaviour
# ---------------------------------------------------------------------------


def test_service_snapshot_is_read_only():
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

    original_state = order.state
    original_planned_eta = order.eta.planned_eta
    original_current_eta = order.eta.current_eta
    original_required_date = order.eta.required_date
    original_status = order.eta.status

    service.calculate_eta_operational_snapshot(
        order,
    )

    assert order.state == original_state
    assert order.eta.planned_eta == original_planned_eta
    assert order.eta.current_eta == original_current_eta
    assert order.eta.required_date == original_required_date
    assert order.eta.status == original_status


# ---------------------------------------------------------------------------
# Repeatability
# ---------------------------------------------------------------------------


def test_service_snapshot_is_repeatable():
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

    first = service.calculate_eta_operational_snapshot(
        order,
    )

    second = service.calculate_eta_operational_snapshot(
        order,
    )

    assert first == second


# ---------------------------------------------------------------------------
# Threshold forwarding
# ---------------------------------------------------------------------------


def test_service_snapshot_accepts_schedule_thresholds():
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
            18,
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

    thresholds = ETARiskThresholds(
        at_risk_hours=Decimal("1"),
        late_hours=Decimal("2"),
    )

    result = service.calculate_eta_operational_snapshot(
        order,
        schedule_risk_thresholds=thresholds,
    )

    assert isinstance(
        result,
        ETAOperationalSnapshot,
    )


def test_service_snapshot_accepts_required_date_thresholds():
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

    # Use the existing constructor contract.
    # No assumptions are made about custom threshold field names.
    thresholds = RequiredDateRiskThresholds()

    result = service.calculate_eta_operational_snapshot(
        order,
        required_date_risk_thresholds=thresholds,
    )

    assert isinstance(
        result,
        ETAOperationalSnapshot,
    )


# ---------------------------------------------------------------------------
# Missing ETA information
# ---------------------------------------------------------------------------


def test_service_snapshot_supports_missing_current_eta():
    service = ProductionService()

    order = make_order()

    result = service.calculate_eta_operational_snapshot(
        order,
    )

    assert isinstance(
        result,
        ETAOperationalSnapshot,
    )

    assert result.current_eta is None


def test_service_snapshot_supports_missing_planned_eta():
    service = ProductionService()

    order = make_order()

    result = service.calculate_eta_operational_snapshot(
        order,
    )

    assert result.planned_eta is None


# ---------------------------------------------------------------------------
# Operational convenience properties
# ---------------------------------------------------------------------------


def test_service_snapshot_requires_action_matches_action_required():
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

    result = service.calculate_eta_operational_snapshot(
        order,
    )

    assert result.requires_action == (
        result.action_required
    )


def test_service_snapshot_summary_is_present():
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

    result = service.calculate_eta_operational_snapshot(
        order,
    )

    assert isinstance(
        result.summary,
        str,
    )

    assert result.summary != ""


# ---------------------------------------------------------------------------
# Frozen/read-only snapshot
# ---------------------------------------------------------------------------


def test_service_returns_frozen_snapshot():
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

    result = service.calculate_eta_operational_snapshot(
        order,
    )

    with pytest.raises(Exception):
        result.decision = (
            ETARiskDecision.CUSTOMER_DATE_LATE
        )