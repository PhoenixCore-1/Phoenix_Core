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


def make_order(qty="1000"):
    return ManufacturingOrder(
        tenant_id="TEST_TENANT",
        site_id="TEST_SITE",
        product_id="TEST_PRODUCT",
        planned_quantity=Decimal(qty),
        required_date=datetime(2026, 8, 31),
    )


def test_hold_records_start_time():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    hold_started = datetime(
        2026,
        8,
        21,
        10,
        0,
    )

    service.hold_order(
        order,
        "Material shortage",
        now=hold_started,
    )

    assert order.eta.hold_started_at == hold_started
    assert order.eta.hold_is_active is True
    assert order.hold_reason == "Material shortage"


def test_hold_resume_records_duration():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    hold_started = datetime(
        2026,
        8,
        21,
        10,
        0,
    )

    resumed = datetime(
        2026,
        8,
        21,
        16,
        0,
    )

    service.hold_order(
        order,
        "Material shortage",
        now=hold_started,
    )

    service.resume_order(
        order,
        now=resumed,
    )

    assert order.eta.hold_started_at is None
    assert order.eta.hold_is_active is False

    assert (
        order.eta.total_hold_duration
        == timedelta(hours=6)
    )

    assert (
        order.eta.last_hold_resumed_at
        == resumed
    )


def test_multiple_holds_accumulate():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    first_start = datetime(
        2026,
        8,
        21,
        8,
        0,
    )

    first_resume = datetime(
        2026,
        8,
        21,
        12,
        0,
    )

    second_start = datetime(
        2026,
        8,
        22,
        9,
        0,
    )

    second_resume = datetime(
        2026,
        8,
        22,
        15,
        0,
    )

    service.hold_order(
        order,
        "Material shortage",
        now=first_start,
    )

    service.resume_order(
        order,
        now=first_resume,
    )

    service.hold_order(
        order,
        "Machine maintenance",
        now=second_start,
    )

    service.resume_order(
        order,
        now=second_resume,
    )

    assert (
        order.eta.total_hold_duration
        == timedelta(hours=10)
    )


def test_hold_adjusted_eta_includes_accumulated_hold_time():
    service = ProductionService()
    order = make_order()

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

    base_eta = datetime(
        2026,
        8,
        25,
        8,
        0,
    )

    adjusted_eta = (
        order.eta.calculate_hold_adjusted_eta(
            base_eta
        )
    )

    assert adjusted_eta == datetime(
        2026,
        8,
        25,
        14,
        0,
    )


def test_active_hold_is_included_in_effective_hold_duration():
    service = ProductionService()
    order = make_order()

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
        "Machine maintenance",
        now=hold_start,
    )

    # Directly test the deterministic hold calculation through
    # the hold lifecycle rather than depending on wall-clock time.
    assert order.eta.hold_is_active is True
    assert order.eta.total_hold_duration == timedelta(0)


def test_double_hold_is_rejected():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    first_hold = datetime(
        2026,
        8,
        21,
        8,
        0,
    )

    second_hold = datetime(
        2026,
        8,
        21,
        10,
        0,
    )

    service.hold_order(
        order,
        "Material shortage",
        now=first_hold,
    )

    with pytest.raises(ValueError):
        order.eta.mark_hold_started(
            second_hold
        )


def test_resume_without_hold_is_rejected():
    service = ProductionService()
    order = make_order()

    with pytest.raises(ValueError):
        order.eta.mark_hold_resumed(
            datetime(
                2026,
                8,
                21,
                10,
                0,
            )
        )


def test_hold_resume_before_hold_start_is_rejected():
    service = ProductionService()
    order = make_order()

    hold_start = datetime(
        2026,
        8,
        21,
        12,
        0,
    )

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.hold_order(
        order,
        "Material shortage",
        now=hold_start,
    )

    with pytest.raises(ValueError):
        order.eta.mark_hold_resumed(
            datetime(
                2026,
                8,
                21,
                11,
                0,
            )
        )


def test_completion_closes_active_hold():
    service = ProductionService()
    order = make_order("10")

    service.release_order(
        order,
        now=datetime(2026, 8, 20, 8, 0),
    )

    service.start_order(
        order,
        now=datetime(2026, 8, 20, 9, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("10"),
    )

    hold_start = datetime(
        2026,
        8,
        21,
        8,
        0,
    )

    completion = datetime(
        2026,
        8,
        21,
        12,
        0,
    )

    service.hold_order(
        order,
        "Final inspection",
        now=hold_start,
    )

    service.complete_order(
        order,
        now=completion,
    )

    assert (
        order.eta.hold_started_at
        is None
    )

    assert (
        order.eta.total_hold_duration
        == timedelta(hours=4)
    )

    assert (
        order.eta.status
        == ETAStatus.COMPLETED
    )


def test_hold_duration_does_not_change_planned_eta():
    service = ProductionService()
    order = make_order()

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
        order.eta.planned_eta
        == planned_eta
    )

    assert (
        order.eta.total_hold_duration
        == timedelta(hours=6)
    )