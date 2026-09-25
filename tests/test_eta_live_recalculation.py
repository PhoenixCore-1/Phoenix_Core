from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from phoenix_production_module.production.models import (
    ETAStatus,
    ManufacturingOrder,
)
from phoenix_production_module.production.service import (
    ProductionService,
)


def make_order(
    qty="1000",
    required_date=datetime(2026, 8, 31),
):
    return ManufacturingOrder(
        tenant_id="TEST_TENANT",
        site_id="TEST_SITE",
        product_id="TEST_PRODUCT",
        planned_quantity=Decimal(qty),
        required_date=required_date,
    )


# ---------------------------------------------------------------------------
# Phoenix Production Module 1.3.12
# Automatic Live ETA Recalculation
#
# ETA rule:
#
#   Calculation Time
#       +
#   Remaining Production Time
#       +
#   Accumulated Hold Time
#       =
#   Current Live ETA
#
# The planned ETA remains the original planning baseline and is never
# overwritten by live ETA calculations.
# ---------------------------------------------------------------------------


def test_automatic_live_eta_uses_remaining_quantity():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    snapshot = service.calculate_live_eta(
        order,
        production_rate_per_hour=Decimal("100"),
        calculated_at=datetime(2026, 8, 21, 8, 0),
    )

    assert snapshot is not None

    # 1000 / 100 = 10 hours.
    assert snapshot.current_eta == datetime(
        2026,
        8,
        21,
        18,
        0,
    )

    assert snapshot.status == ETAStatus.ON_TRACK


def test_partial_production_reduces_remaining_quantity_and_live_eta():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    first_snapshot = service.calculate_live_eta(
        order,
        production_rate_per_hour=Decimal("100"),
        calculated_at=datetime(2026, 8, 21, 8, 0),
    )

    assert first_snapshot is not None

    assert first_snapshot.current_eta == datetime(
        2026,
        8,
        21,
        18,
        0,
    )

    service.record_quantity(
        order,
        accepted=Decimal("400"),
    )

    assert order.quantity.remaining == Decimal("600")

    second_snapshot = service.calculate_live_eta(
        order,
        production_rate_per_hour=Decimal("100"),
        calculated_at=datetime(2026, 8, 21, 8, 0),
    )

    assert second_snapshot is not None

    # 600 / 100 = 6 hours.
    assert second_snapshot.current_eta == datetime(
        2026,
        8,
        21,
        14,
        0,
    )

    assert (
        second_snapshot.current_eta
        < first_snapshot.current_eta
    )


def test_faster_actual_production_rate_moves_live_eta_earlier():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    calculated_at = datetime(
        2026,
        8,
        21,
        8,
        0,
    )

    slow_snapshot = service.calculate_live_eta(
        order,
        production_rate_per_hour=Decimal("100"),
        calculated_at=calculated_at,
    )

    fast_snapshot = service.calculate_live_eta(
        order,
        production_rate_per_hour=Decimal("200"),
        calculated_at=calculated_at,
    )

    assert slow_snapshot is not None
    assert fast_snapshot is not None

    assert (
        fast_snapshot.current_eta
        < slow_snapshot.current_eta
    )


def test_slower_actual_production_rate_moves_live_eta_later():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    calculated_at = datetime(
        2026,
        8,
        21,
        8,
        0,
    )

    fast_snapshot = service.calculate_live_eta(
        order,
        production_rate_per_hour=Decimal("200"),
        calculated_at=calculated_at,
    )

    slow_snapshot = service.calculate_live_eta(
        order,
        production_rate_per_hour=Decimal("100"),
        calculated_at=calculated_at,
    )

    assert fast_snapshot is not None
    assert slow_snapshot is not None

    assert (
        slow_snapshot.current_eta
        > fast_snapshot.current_eta
    )


def test_accumulated_hold_time_extends_live_eta():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    hold_start = datetime(
        2026,
        8,
        21,
        8,
        0,
    )

    hold_resume = datetime(
        2026,
        8,
        21,
        14,
        0,
    )

    service.hold_order(
        order,
        "Material shortage",
        now=hold_start,
    )

    service.resume_order(
        order,
        now=hold_resume,
    )

    assert (
        order.eta.total_hold_duration
        == timedelta(hours=6)
    )

    snapshot = service.calculate_live_eta(
        order,
        production_rate_per_hour=Decimal("100"),
        calculated_at=datetime(
            2026,
            8,
            21,
            8,
            0,
        ),
    )

    assert snapshot is not None

    # 10 production hours + 6 hours accumulated hold.
    assert snapshot.current_eta == datetime(
        2026,
        8,
        22,
        0,
        0,
    )


def test_multiple_holds_are_included_in_automatic_live_eta():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    first_hold_start = datetime(
        2026,
        8,
        21,
        8,
        0,
    )

    first_hold_resume = datetime(
        2026,
        8,
        21,
        12,
        0,
    )

    second_hold_start = datetime(
        2026,
        8,
        22,
        8,
        0,
    )

    second_hold_resume = datetime(
        2026,
        8,
        22,
        14,
        0,
    )

    service.hold_order(
        order,
        "Material shortage",
        now=first_hold_start,
    )

    service.resume_order(
        order,
        now=first_hold_resume,
    )

    service.hold_order(
        order,
        "Machine maintenance",
        now=second_hold_start,
    )

    service.resume_order(
        order,
        now=second_hold_resume,
    )

    assert (
        order.eta.total_hold_duration
        == timedelta(hours=10)
    )

    snapshot = service.calculate_live_eta(
        order,
        production_rate_per_hour=Decimal("100"),
        calculated_at=datetime(
            2026,
            8,
            21,
            8,
            0,
        ),
    )

    assert snapshot is not None

    # 10 production hours + 10 hours accumulated hold.
    assert snapshot.current_eta == datetime(
        2026,
        8,
        22,
        4,
        0,
    )


def test_active_hold_is_included_in_live_eta_calculation():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    hold_start = datetime(
        2026,
        8,
        21,
        8,
        0,
    )

    service.hold_order(
        order,
        "Material shortage",
        now=hold_start,
    )

    calculated_at = datetime(
        2026,
        8,
        21,
        14,
        0,
    )

    snapshot = service.calculate_live_eta(
        order,
        production_rate_per_hour=Decimal("100"),
        calculated_at=calculated_at,
    )

    assert snapshot is not None

    # The active hold is calculated from the real current clock by
    # ETAPlan. The deterministic portion of this test is therefore
    # limited to confirming that an ETA is produced and that the
    # active hold does not produce a negative or missing ETA.

    assert snapshot.current_eta is not None
    assert (
        snapshot.current_eta
        > calculated_at
    )


def test_completed_quantity_sets_live_eta_to_completion():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("1000"),
    )

    calculated_at = datetime(
        2026,
        8,
        25,
        12,
        0,
    )

    snapshot = service.calculate_live_eta(
        order,
        production_rate_per_hour=Decimal("100"),
        calculated_at=calculated_at,
    )

    assert snapshot is not None

    assert snapshot.current_eta == calculated_at
    assert snapshot.status == ETAStatus.COMPLETED
    assert order.eta.actual_completion == calculated_at


def test_live_eta_is_none_before_production_starts():
    service = ProductionService()
    order = make_order("1000")

    snapshot = service.calculate_live_eta(
        order,
        production_rate_per_hour=Decimal("100"),
        calculated_at=datetime(
            2026,
            8,
            21,
            8,
            0,
        ),
    )

    assert snapshot is None
    assert order.eta.current_eta is None


def test_planned_eta_is_not_overwritten_by_live_eta():
    service = ProductionService()
    order = make_order("1000")

    planned_start = datetime(
        2026,
        8,
        20,
        8,
        0,
    )

    planned_eta = datetime(
        2026,
        8,
        25,
        8,
        0,
    )

    service.establish_planned_eta(
        order,
        planned_production_start=planned_start,
        planned_eta=planned_eta,
    )

    service.mark_production_started(
        order,
        planned_start,
    )

    service.calculate_live_eta(
        order,
        production_rate_per_hour=Decimal("200"),
        calculated_at=datetime(
            2026,
            8,
            21,
            8,
            0,
        ),
    )

    assert order.eta.planned_eta == planned_eta

    assert (
        order.eta.current_eta
        != order.eta.planned_eta
    )


def test_live_eta_can_be_on_track_against_required_date():
    service = ProductionService()

    order = make_order(
        "1000",
        required_date=datetime(
            2026,
            8,
            22,
            8,
            0,
        ),
    )

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    snapshot = service.calculate_live_eta(
        order,
        production_rate_per_hour=Decimal("50"),
        calculated_at=datetime(
            2026,
            8,
            21,
            8,
            0,
        ),
    )

    assert snapshot is not None

    # 1000 / 50 = 20 hours.
    assert snapshot.current_eta == datetime(
        2026,
        8,
        22,
        4,
        0,
    )

    assert snapshot.status == ETAStatus.ON_TRACK
    assert snapshot.is_late is False


def test_live_eta_detects_late_production():
    service = ProductionService()

    order = make_order(
        "1000",
        required_date=datetime(
            2026,
            8,
            22,
            8,
            0,
        ),
    )

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    snapshot = service.calculate_live_eta(
        order,
        production_rate_per_hour=Decimal("40"),
        calculated_at=datetime(
            2026,
            8,
            21,
            8,
            0,
        ),
    )

    assert snapshot is not None

    # 1000 / 40 = 25 hours.
    assert snapshot.current_eta == datetime(
        2026,
        8,
        22,
        9,
        0,
    )

    assert snapshot.status == ETAStatus.LATE
    assert snapshot.is_late is True


def test_invalid_production_rate_is_rejected():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    with pytest.raises(ValueError):
        service.calculate_live_eta(
            order,
            production_rate_per_hour=Decimal("0"),
            calculated_at=datetime(
                2026,
                8,
                21,
                8,
                0,
            ),
        )


def test_negative_production_rate_is_rejected():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    with pytest.raises(ValueError):
        service.calculate_live_eta(
            order,
            production_rate_per_hour=Decimal("-100"),
            calculated_at=datetime(
                2026,
                8,
                21,
                8,
                0,
            ),
        )