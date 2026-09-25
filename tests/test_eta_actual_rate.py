from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from phoenix_production_module.production.models import (
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
# Phoenix Production Module 1.3.13
# Actual Production Rate from Production History
# ---------------------------------------------------------------------------


def test_actual_rate_is_calculated_from_processed_quantity_and_time():
    service = ProductionService()
    order = make_order("1000")

    production_start = datetime(2026, 8, 20, 8, 0)
    calculation_time = datetime(2026, 8, 20, 18, 0)

    service.mark_production_started(
        order,
        production_start,
    )

    service.record_quantity(
        order,
        accepted=Decimal("500"),
    )

    rate = service.calculate_actual_production_rate(
        order,
        calculated_at=calculation_time,
    )

    assert rate == Decimal("50")


def test_actual_rate_is_none_before_production_starts():
    service = ProductionService()
    order = make_order("1000")

    rate = service.calculate_actual_production_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 18, 0),
    )

    assert rate is None


def test_actual_rate_is_none_when_no_quantity_has_been_processed():
    service = ProductionService()
    order = make_order("1000")

    production_start = datetime(2026, 8, 20, 8, 0)
    calculation_time = datetime(2026, 8, 20, 18, 0)

    service.mark_production_started(
        order,
        production_start,
    )

    rate = service.calculate_actual_production_rate(
        order,
        calculated_at=calculation_time,
    )

    assert rate is None


def test_actual_rate_excludes_completed_hold_time():
    service = ProductionService()
    order = make_order("1000")

    production_start = datetime(2026, 8, 20, 8, 0)
    hold_start = datetime(2026, 8, 20, 12, 0)
    hold_resume = datetime(2026, 8, 20, 14, 0)
    calculation_time = datetime(2026, 8, 20, 18, 0)

    service.mark_production_started(
        order,
        production_start,
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

    service.record_quantity(
        order,
        accepted=Decimal("600"),
    )

    rate = service.calculate_actual_production_rate(
        order,
        calculated_at=calculation_time,
    )

    # 10 elapsed hours - 2 hold hours = 8 productive hours.
    # 600 / 8 = 75 units/hour.
    assert rate == Decimal("75")


def test_actual_rate_changes_as_production_progresses():
    service = ProductionService()
    order = make_order("1000")

    production_start = datetime(
        2026,
        8,
        20,
        8,
        0,
    )

    first_calculation = datetime(
        2026,
        8,
        20,
        18,
        0,
    )

    second_calculation = datetime(
        2026,
        8,
        21,
        8,
        0,
    )

    service.mark_production_started(
        order,
        production_start,
    )

    # First production result.
    service.record_quantity(
        order,
        accepted=Decimal("500"),
    )

    first_rate = service.calculate_actual_production_rate(
        order,
        calculated_at=first_calculation,
    )

    assert first_rate == Decimal("50")

    # Additional production.
    #
    # Total processed quantity becomes:
    #
    # 500 + 200 = 700
    #
    # Total elapsed production time:
    #
    # 24 hours
    #
    # Actual rate:
    #
    # 700 / 24 = 29.166666...
    service.record_quantity(
        order,
        accepted=Decimal("200"),
    )

    second_rate = service.calculate_actual_production_rate(
        order,
        calculated_at=second_calculation,
    )

    assert second_rate == (
        Decimal("700")
        / Decimal("24")
    )

    assert second_rate != first_rate


def test_actual_rate_rejects_calculation_before_production_start():
    service = ProductionService()
    order = make_order("1000")

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

    with pytest.raises(ValueError):
        service.calculate_actual_production_rate(
            order,
            calculated_at=datetime(
                2026,
                8,
                20,
                7,
                59,
            ),
        )


def test_actual_rate_can_be_calculated_from_a_defined_window():
    service = ProductionService()
    order = make_order("1000")

    window_start = datetime(
        2026,
        8,
        20,
        8,
        0,
    )

    window_end = datetime(
        2026,
        8,
        20,
        16,
        0,
    )

    rate = (
        service.calculate_actual_production_rate_from_window(
            order,
            window_start=window_start,
            window_end=window_end,
            quantity_produced=Decimal("800"),
        )
    )

    assert rate == Decimal("100")


def test_defined_window_rejects_reversed_times():
    service = ProductionService()
    order = make_order("1000")

    window_start = datetime(
        2026,
        8,
        20,
        16,
        0,
    )

    window_end = datetime(
        2026,
        8,
        20,
        8,
        0,
    )

    with pytest.raises(ValueError):
        service.calculate_actual_production_rate_from_window(
            order,
            window_start=window_start,
            window_end=window_end,
            quantity_produced=Decimal("800"),
        )


def test_defined_window_rejects_negative_quantity():
    service = ProductionService()
    order = make_order("1000")

    window_start = datetime(
        2026,
        8,
        20,
        8,
        0,
    )

    window_end = datetime(
        2026,
        8,
        20,
        16,
        0,
    )

    with pytest.raises(ValueError):
        service.calculate_actual_production_rate_from_window(
            order,
            window_start=window_start,
            window_end=window_end,
            quantity_produced=Decimal("-1"),
        )


def test_live_eta_uses_actual_production_rate():
    service = ProductionService()
    order = make_order("1000")

    production_start = datetime(
        2026,
        8,
        20,
        8,
        0,
    )

    calculation_time = datetime(
        2026,
        8,
        20,
        18,
        0,
    )

    service.mark_production_started(
        order,
        production_start,
    )

    service.record_quantity(
        order,
        accepted=Decimal("500"),
    )

    snapshot = (
        service.calculate_live_eta_from_actual_rate(
            order,
            calculated_at=calculation_time,
        )
    )

    assert snapshot is not None

    # 500 / 10 hours = 50 units/hour.
    #
    # Remaining = 500.
    #
    # 500 / 50 = 10 remaining hours.
    #
    # 18:00 + 10 hours = next day 04:00.
    assert snapshot.current_eta == datetime(
        2026,
        8,
        21,
        4,
        0,
    )


def test_live_eta_moves_as_more_quantity_is_completed():
    service = ProductionService()
    order = make_order("1000")

    production_start = datetime(
        2026,
        8,
        20,
        8,
        0,
    )

    calculation_time = datetime(
        2026,
        8,
        20,
        18,
        0,
    )

    service.mark_production_started(
        order,
        production_start,
    )

    service.record_quantity(
        order,
        accepted=Decimal("500"),
    )

    first_snapshot = (
        service.calculate_live_eta_from_actual_rate(
            order,
            calculated_at=calculation_time,
        )
    )

    assert first_snapshot is not None

    service.record_quantity(
        order,
        accepted=Decimal("200"),
    )

    second_snapshot = (
        service.calculate_live_eta_from_actual_rate(
            order,
            calculated_at=calculation_time,
        )
    )

    assert second_snapshot is not None

    assert (
        second_snapshot.current_eta
        < first_snapshot.current_eta
    )


def test_live_eta_returns_none_when_actual_rate_is_unavailable():
    service = ProductionService()
    order = make_order("1000")

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

    snapshot = (
        service.calculate_live_eta_from_actual_rate(
            order,
            calculated_at=datetime(
                2026,
                8,
                20,
                8,
                0,
            ),
        )
    )

    assert snapshot is None


def test_live_eta_completes_when_remaining_quantity_is_zero():
    service = ProductionService()
    order = make_order("1000")

    production_start = datetime(
        2026,
        8,
        20,
        8,
        0,
    )

    completion_time = datetime(
        2026,
        8,
        21,
        8,
        0,
    )

    service.mark_production_started(
        order,
        production_start,
    )

    service.record_quantity(
        order,
        accepted=Decimal("1000"),
    )

    snapshot = (
        service.calculate_live_eta_from_actual_rate(
            order,
            calculated_at=completion_time,
        )
    )

    assert snapshot is not None

    assert (
        snapshot.current_eta
        == completion_time
    )


def test_actual_rate_is_decimal():
    service = ProductionService()
    order = make_order("1000")

    production_start = datetime(
        2026,
        8,
        20,
        8,
        0,
    )

    calculation_time = datetime(
        2026,
        8,
        20,
        12,
        0,
    )

    service.mark_production_started(
        order,
        production_start,
    )

    service.record_quantity(
        order,
        accepted=Decimal("300"),
    )

    rate = service.calculate_actual_production_rate(
        order,
        calculated_at=calculation_time,
    )

    assert isinstance(
        rate,
        Decimal,
    )


def test_actual_rate_accounts_for_rejected_and_rework_quantity():
    service = ProductionService()
    order = make_order("1000")

    production_start = datetime(
        2026,
        8,
        20,
        8,
        0,
    )

    calculation_time = datetime(
        2026,
        8,
        20,
        18,
        0,
    )

    service.mark_production_started(
        order,
        production_start,
    )

    service.record_quantity(
        order,
        accepted=Decimal("400"),
        rejected=Decimal("50"),
        rework=Decimal("50"),
    )

    rate = service.calculate_actual_production_rate(
        order,
        calculated_at=calculation_time,
    )

    # 400 + 50 + 50 = 500 processed.
    # 500 / 10 hours = 50 units/hour.
    assert rate == Decimal("50")