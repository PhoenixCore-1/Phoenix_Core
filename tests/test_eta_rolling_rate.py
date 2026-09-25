from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from phoenix_production_module.production.service import ProductionService
from phoenix_production_module.production.models import ManufacturingOrder


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
# Phoenix Production Module 1.3.14
# Rolling Production Rate
# ---------------------------------------------------------------------------


def test_rolling_rate_uses_recent_production_window():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    rate = service.calculate_rolling_production_rate(
        order,
        window_hours=Decimal("4"),
        calculated_at=datetime(2026, 8, 20, 12, 0),
        quantity_produced=Decimal("400"),
    )

    assert rate == Decimal("100")


def test_rolling_rate_can_use_shorter_actual_window():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    rate = service.calculate_rolling_production_rate(
        order,
        window_hours=Decimal("8"),
        calculated_at=datetime(2026, 8, 20, 10, 0),
        quantity_produced=Decimal("200"),
    )

    # Only 2 actual production hours have elapsed because the
    # requested 8-hour window extends before production started.
    assert rate == Decimal("100")


def test_rolling_rate_returns_none_before_production_starts():
    service = ProductionService()
    order = make_order("1000")

    rate = service.calculate_rolling_production_rate(
        order,
        window_hours=Decimal("4"),
        calculated_at=datetime(2026, 8, 20, 12, 0),
        quantity_produced=Decimal("400"),
    )

    assert rate is None


def test_rolling_rate_rejects_zero_window():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    with pytest.raises(ValueError):
        service.calculate_rolling_production_rate(
            order,
            window_hours=Decimal("0"),
            calculated_at=datetime(2026, 8, 20, 12, 0),
            quantity_produced=Decimal("400"),
        )


def test_rolling_rate_rejects_negative_window():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    with pytest.raises(ValueError):
        service.calculate_rolling_production_rate(
            order,
            window_hours=Decimal("-4"),
            calculated_at=datetime(2026, 8, 20, 12, 0),
            quantity_produced=Decimal("400"),
        )


def test_rolling_rate_rejects_calculation_before_production_start():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 12, 0),
    )

    with pytest.raises(ValueError):
        service.calculate_rolling_production_rate(
            order,
            window_hours=Decimal("4"),
            calculated_at=datetime(2026, 8, 20, 11, 59),
            quantity_produced=Decimal("100"),
        )


def test_rolling_rate_returns_zero_when_window_has_zero_quantity():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    rate = service.calculate_rolling_production_rate(
        order,
        window_hours=Decimal("4"),
        calculated_at=datetime(2026, 8, 20, 12, 0),
        quantity_produced=Decimal("0"),
    )

    assert rate == Decimal("0")


def test_rolling_rate_rejects_negative_quantity():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    with pytest.raises(ValueError):
        service.calculate_rolling_production_rate(
            order,
            window_hours=Decimal("4"),
            calculated_at=datetime(2026, 8, 20, 12, 0),
            quantity_produced=Decimal("-1"),
        )


def test_rolling_rate_excludes_completed_hold_time():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.hold_order(
        order,
        "Material shortage",
        now=datetime(2026, 8, 20, 10, 0),
    )

    service.resume_order(
        order,
        now=datetime(2026, 8, 20, 12, 0),
    )

    rate = service.calculate_rolling_production_rate(
        order,
        window_hours=Decimal("8"),
        calculated_at=datetime(2026, 8, 20, 16, 0),
        quantity_produced=Decimal("400"),
    )

    # Window = 8 hours.
    # Hold = 2 hours.
    # Effective production = 6 hours.
    # 400 / 6 = 66.666...
    assert rate == (
        Decimal("400")
        / Decimal("6")
    )


def test_rolling_rate_reacts_to_faster_recent_production():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    historical_rate = service.calculate_actual_production_rate_from_window(
        order,
        window_start=datetime(2026, 8, 20, 8, 0),
        window_end=datetime(2026, 8, 20, 16, 0),
        quantity_produced=Decimal("400"),
    )

    rolling_rate = service.calculate_rolling_production_rate(
        order,
        window_hours=Decimal("4"),
        calculated_at=datetime(2026, 8, 20, 16, 0),
        quantity_produced=Decimal("600"),
    )

    assert historical_rate == Decimal("50")
    assert rolling_rate == Decimal("150")
    assert rolling_rate > historical_rate


def test_rolling_rate_reacts_to_slower_recent_production():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    historical_rate = service.calculate_actual_production_rate_from_window(
        order,
        window_start=datetime(2026, 8, 20, 8, 0),
        window_end=datetime(2026, 8, 20, 16, 0),
        quantity_produced=Decimal("800"),
    )

    rolling_rate = service.calculate_rolling_production_rate(
        order,
        window_hours=Decimal("4"),
        calculated_at=datetime(2026, 8, 20, 16, 0),
        quantity_produced=Decimal("200"),
    )

    assert historical_rate == Decimal("100")
    assert rolling_rate == Decimal("50")
    assert rolling_rate < historical_rate


def test_live_eta_from_rolling_rate_uses_remaining_quantity():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("400"),
    )

    snapshot = service.calculate_live_eta_from_rolling_rate(
        order,
        window_hours=Decimal("4"),
        calculated_at=datetime(2026, 8, 20, 12, 0),
        quantity_produced=Decimal("400"),
    )

    assert snapshot is not None

    # Rolling rate = 400 / 4 = 100/hour.
    # Remaining quantity = 600.
    # Remaining time = 6 hours.
    assert snapshot.current_eta == datetime(
        2026,
        8,
        20,
        18,
        0,
    )


def test_faster_rolling_rate_moves_live_eta_earlier():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("400"),
    )

    slow_snapshot = service.calculate_live_eta_from_rolling_rate(
        order,
        window_hours=Decimal("4"),
        calculated_at=datetime(2026, 8, 20, 12, 0),
        quantity_produced=Decimal("200"),
    )

    fast_snapshot = service.calculate_live_eta_from_rolling_rate(
        order,
        window_hours=Decimal("4"),
        calculated_at=datetime(2026, 8, 20, 12, 0),
        quantity_produced=Decimal("400"),
    )

    assert slow_snapshot is not None
    assert fast_snapshot is not None

    assert (
        fast_snapshot.current_eta
        < slow_snapshot.current_eta
    )


def test_slower_rolling_rate_moves_live_eta_later():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("400"),
    )

    fast_snapshot = service.calculate_live_eta_from_rolling_rate(
        order,
        window_hours=Decimal("4"),
        calculated_at=datetime(2026, 8, 20, 12, 0),
        quantity_produced=Decimal("400"),
    )

    slow_snapshot = service.calculate_live_eta_from_rolling_rate(
        order,
        window_hours=Decimal("4"),
        calculated_at=datetime(2026, 8, 20, 12, 0),
        quantity_produced=Decimal("200"),
    )

    assert fast_snapshot is not None
    assert slow_snapshot is not None

    assert (
        slow_snapshot.current_eta
        > fast_snapshot.current_eta
    )


def test_rolling_live_eta_returns_none_when_no_rate_exists():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    snapshot = service.calculate_live_eta_from_rolling_rate(
        order,
        window_hours=Decimal("4"),
        calculated_at=datetime(2026, 8, 20, 12, 0),
        quantity_produced=Decimal("0"),
    )

    assert snapshot is None


def test_rolling_live_eta_completes_when_remaining_quantity_is_zero():
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

    snapshot = service.calculate_live_eta_from_rolling_rate(
        order,
        window_hours=Decimal("4"),
        calculated_at=datetime(2026, 8, 20, 12, 0),
        quantity_produced=Decimal("400"),
    )

    assert snapshot is not None

    assert snapshot.current_eta == datetime(
        2026,
        8,
        20,
        12,
        0,
    )


def test_rolling_rate_is_decimal():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    rate = service.calculate_rolling_production_rate(
        order,
        window_hours=Decimal("4"),
        calculated_at=datetime(2026, 8, 20, 12, 0),
        quantity_produced=Decimal("400"),
    )

    assert isinstance(
        rate,
        Decimal,
    )


def test_rolling_rate_does_not_change_full_history_rate():
    service = ProductionService()
    order = make_order("1000")

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("400"),
    )

    full_history_rate = (
        service.calculate_actual_production_rate(
            order,
            calculated_at=datetime(
                2026,
                8,
                20,
                16,
                0,
            ),
        )
    )

    rolling_rate = (
        service.calculate_rolling_production_rate(
            order,
            window_hours=Decimal("4"),
            calculated_at=datetime(
                2026,
                8,
                20,
                16,
                0,
            ),
            quantity_produced=Decimal("600"),
        )
    )

    assert full_history_rate == Decimal("50")
    assert rolling_rate == Decimal("150")

    # The two calculations remain independent.
    assert full_history_rate != rolling_rate