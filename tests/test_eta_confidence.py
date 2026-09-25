from datetime import datetime
from decimal import Decimal

import pytest

from phoenix_production_module.production.models import ManufacturingOrder
from phoenix_production_module.production.service import (
    ProductionService,
    RateConfidence,
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
# Phoenix Production Module 1.3.15
# ETA Confidence & Rate Selection
# ---------------------------------------------------------------------------


def test_rate_selection_is_insufficient_before_production_starts():
    service = ProductionService()
    order = make_order()

    result = service.select_eta_production_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 12, 0),
    )

    assert result.selected_rate is None
    assert result.full_history_rate is None
    assert result.rolling_rate is None
    assert result.confidence == RateConfidence.INSUFFICIENT
    assert result.source == "NONE"
    assert result.history_hours == Decimal("0")


def test_rate_selection_is_insufficient_with_no_effective_history():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    result = service.select_eta_production_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 8, 0),
    )

    assert result.selected_rate is None
    assert result.confidence == RateConfidence.INSUFFICIENT
    assert result.source == "NONE"


def test_rate_selection_is_insufficient_below_minimum_history():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("100"),
    )

    result = service.select_eta_production_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 10, 0),
        minimum_history_hours=Decimal("4"),
        high_confidence_hours=Decimal("8"),
    )

    assert result.confidence == RateConfidence.INSUFFICIENT
    assert result.source == "FULL_HISTORY"
    assert result.selected_rate == Decimal("50")


def test_rate_selection_is_low_confidence_with_moderate_history():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("300"),
    )

    result = service.select_eta_production_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 14, 0),
        rolling_window_hours=Decimal("4"),
        quantity_produced=Decimal("300"),
        minimum_history_hours=Decimal("4"),
        high_confidence_hours=Decimal("8"),
    )

    assert result.confidence == RateConfidence.LOW
    assert result.source == "FULL_HISTORY"
    assert result.selected_rate == Decimal("50")
    assert result.full_history_rate == Decimal("50")


def test_rate_selection_becomes_high_confidence_after_sufficient_history():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("800"),
    )

    result = service.select_eta_production_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 16, 0),
        rolling_window_hours=Decimal("4"),
        quantity_produced=Decimal("400"),
        minimum_history_hours=Decimal("4"),
        high_confidence_hours=Decimal("8"),
    )

    assert result.confidence == RateConfidence.HIGH
    assert result.source == "ROLLING"
    assert result.selected_rate == Decimal("100")
    assert result.rolling_rate == Decimal("100")


def test_high_confidence_prefers_rolling_rate_over_full_history_rate():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("800"),
    )

    result = service.select_eta_production_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 16, 0),
        rolling_window_hours=Decimal("4"),
        quantity_produced=Decimal("600"),
        minimum_history_hours=Decimal("4"),
        high_confidence_hours=Decimal("8"),
    )

    assert result.confidence == RateConfidence.HIGH
    assert result.source == "ROLLING"
    assert result.full_history_rate == Decimal("100")
    assert result.rolling_rate == Decimal("150")
    assert result.selected_rate == Decimal("150")


def test_high_confidence_rolling_rate_can_be_slower_than_full_history_rate():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("800"),
    )

    result = service.select_eta_production_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 16, 0),
        rolling_window_hours=Decimal("4"),
        quantity_produced=Decimal("200"),
        minimum_history_hours=Decimal("4"),
        high_confidence_hours=Decimal("8"),
    )

    assert result.confidence == RateConfidence.HIGH
    assert result.source == "ROLLING"
    assert result.full_history_rate == Decimal("100")
    assert result.rolling_rate == Decimal("50")
    assert result.selected_rate == Decimal("50")


def test_rate_selection_rejects_invalid_minimum_history():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    with pytest.raises(ValueError):
        service.select_eta_production_rate(
            order,
            calculated_at=datetime(2026, 8, 20, 12, 0),
            minimum_history_hours=Decimal("0"),
        )


def test_rate_selection_rejects_high_confidence_below_minimum_history():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    with pytest.raises(ValueError):
        service.select_eta_production_rate(
            order,
            calculated_at=datetime(2026, 8, 20, 12, 0),
            minimum_history_hours=Decimal("8"),
            high_confidence_hours=Decimal("4"),
        )


def test_rate_selection_rejects_invalid_rolling_window():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    with pytest.raises(ValueError):
        service.select_eta_production_rate(
            order,
            calculated_at=datetime(2026, 8, 20, 12, 0),
            rolling_window_hours=Decimal("0"),
        )


def test_rate_selection_requires_minimum_quantity():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("100"),
    )

    result = service.select_eta_production_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 16, 0),
        minimum_quantity=Decimal("200"),
    )

    assert result.selected_rate is None
    assert result.confidence == RateConfidence.INSUFFICIENT
    assert result.source == "NONE"


def test_rate_selection_accepts_quantity_at_minimum():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("100"),
    )

    result = service.select_eta_production_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 16, 0),
        minimum_quantity=Decimal("100"),
        minimum_history_hours=Decimal("4"),
        high_confidence_hours=Decimal("8"),
    )

    assert result.selected_rate is not None
    assert result.confidence == RateConfidence.HIGH


def test_rate_selection_accounts_for_completed_hold_time():
    service = ProductionService()
    order = make_order()

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

    service.record_quantity(
        order,
        accepted=Decimal("600"),
    )

    result = service.select_eta_production_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 16, 0),
        rolling_window_hours=Decimal("4"),
        quantity_produced=Decimal("400"),
        minimum_history_hours=Decimal("4"),
        high_confidence_hours=Decimal("8"),
    )

    assert result.history_hours == Decimal("6")
    assert result.confidence == RateConfidence.LOW
    assert result.source == "FULL_HISTORY"


def test_selected_rate_live_eta_uses_full_history_when_confidence_is_low():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("200"),
    )

    snapshot = service.calculate_live_eta_from_selected_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 12, 0),
        rolling_window_hours=Decimal("4"),
        quantity_produced=Decimal("200"),
        minimum_history_hours=Decimal("4"),
        high_confidence_hours=Decimal("8"),
    )

    assert snapshot is not None

    # Full-history rate:
    # 200 / 4 = 50/hour.
    #
    # Remaining = 800.
    #
    # Remaining time = 16 hours.
    assert snapshot.current_eta == datetime(
        2026,
        8,
        21,
        4,
        0,
    )


def test_selected_rate_live_eta_uses_rolling_rate_when_confidence_is_high():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("800"),
    )

    snapshot = service.calculate_live_eta_from_selected_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 16, 0),
        rolling_window_hours=Decimal("4"),
        quantity_produced=Decimal("600"),
        minimum_history_hours=Decimal("4"),
        high_confidence_hours=Decimal("8"),
    )

    assert snapshot is not None

    # Rolling rate:
    # 600 / 4 = 150/hour.
    #
    # Remaining = 200.
    #
    # Remaining time = 1.333333... hours.
    expected_eta = (
        datetime(2026, 8, 20, 16, 0)
        + (
            __import__("datetime")
            .timedelta(
                hours=float(
                    Decimal("200")
                    / Decimal("150")
                )
            )
        )
    )

    assert snapshot.current_eta == expected_eta


def test_selected_rate_live_eta_returns_none_when_no_rate_is_available():
    service = ProductionService()
    order = make_order()

    snapshot = service.calculate_live_eta_from_selected_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 12, 0),
    )

    assert snapshot is None


def test_selected_rate_live_eta_completes_when_remaining_quantity_is_zero():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("1000"),
    )

    snapshot = service.calculate_live_eta_from_selected_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 16, 0),
        rolling_window_hours=Decimal("4"),
        quantity_produced=Decimal("500"),
        minimum_history_hours=Decimal("4"),
        high_confidence_hours=Decimal("8"),
    )

    assert snapshot is not None

    assert snapshot.current_eta == datetime(
        2026,
        8,
        20,
        16,
        0,
    )


def test_rate_selection_does_not_modify_existing_current_eta():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    original_eta = datetime(
        2026,
        8,
        21,
        12,
        0,
    )

    service.update_current_eta(
        order,
        original_eta,
        calculated_at=datetime(
            2026,
            8,
            20,
            8,
            0,
        ),
        reason="Existing ETA",
    )

    service.record_quantity(
        order,
        accepted=Decimal("800"),
    )

    result = service.select_eta_production_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 16, 0),
        rolling_window_hours=Decimal("4"),
        quantity_produced=Decimal("600"),
    )

    assert result.selected_rate == Decimal("150")

    assert order.eta.current_eta == original_eta


def test_rate_selection_result_contains_both_rate_views():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("800"),
    )

    result = service.select_eta_production_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 16, 0),
        rolling_window_hours=Decimal("4"),
        quantity_produced=Decimal("600"),
    )

    assert result.full_history_rate == Decimal("100")
    assert result.rolling_rate == Decimal("150")
    assert result.selected_rate == Decimal("150")
    assert result.source == "ROLLING"
    assert result.confidence == RateConfidence.HIGH


def test_rate_selection_history_hours_is_decimal():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    service.record_quantity(
        order,
        accepted=Decimal("400"),
    )

    result = service.select_eta_production_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 12, 30),
    )

    assert isinstance(
        result.history_hours,
        Decimal,
    )


def test_rate_selection_reason_is_present():
    service = ProductionService()
    order = make_order()

    service.mark_production_started(
        order,
        datetime(2026, 8, 20, 8, 0),
    )

    result = service.select_eta_production_rate(
        order,
        calculated_at=datetime(2026, 8, 20, 12, 0),
    )

    assert result.reason