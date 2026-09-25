from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from phoenix_production_module.production.eta_risk import (
    ETARiskCalculator,
    ETARiskLevel,
    ETARiskThresholds,
)
from phoenix_production_module.production.models import ETAStatus


# ---------------------------------------------------------------------------
# Phoenix Production Module 1.3.16
# ETA Risk & Schedule Variance
# ---------------------------------------------------------------------------


def test_exactly_on_planned_eta_is_on_track():
    calculator = ETARiskCalculator()

    planned = datetime(2026, 8, 25, 16, 0)
    current = datetime(2026, 8, 25, 16, 0)

    result = calculator.calculate_variance(
        planned_eta=planned,
        current_eta=current,
        status=ETAStatus.ON_TRACK,
    )

    assert result.variance == timedelta(0)
    assert result.variance_hours == Decimal("0")
    assert result.risk_level == ETARiskLevel.ON_TRACK
    assert result.status == ETAStatus.ON_TRACK
    assert result.is_on_schedule
    assert not result.is_ahead
    assert not result.is_behind


def test_early_live_eta_is_on_track():
    calculator = ETARiskCalculator()

    planned = datetime(2026, 8, 25, 16, 0)
    current = datetime(2026, 8, 25, 12, 0)

    result = calculator.calculate_variance(
        planned_eta=planned,
        current_eta=current,
        status=ETAStatus.ON_TRACK,
    )

    assert result.variance == timedelta(hours=-4)
    assert result.variance_hours == Decimal("-4")
    assert result.risk_level == ETARiskLevel.ON_TRACK
    assert result.status == ETAStatus.ON_TRACK
    assert result.is_ahead
    assert not result.is_on_schedule
    assert not result.is_behind


def test_four_hours_late_is_still_on_track_by_default():
    calculator = ETARiskCalculator()

    planned = datetime(2026, 8, 25, 16, 0)
    current = datetime(2026, 8, 25, 20, 0)

    result = calculator.calculate_variance(
        planned_eta=planned,
        current_eta=current,
        status=ETAStatus.ON_TRACK,
    )

    assert result.variance == timedelta(hours=4)
    assert result.variance_hours == Decimal("4")
    assert result.risk_level == ETARiskLevel.ON_TRACK
    assert result.status == ETAStatus.ON_TRACK
    assert result.is_behind


def test_more_than_four_hours_late_is_at_risk():
    calculator = ETARiskCalculator()

    planned = datetime(2026, 8, 25, 16, 0)
    current = datetime(2026, 8, 25, 21, 0)

    result = calculator.calculate_variance(
        planned_eta=planned,
        current_eta=current,
        status=ETAStatus.ON_TRACK,
    )

    assert result.variance == timedelta(hours=5)
    assert result.variance_hours == Decimal("5")
    assert result.risk_level == ETARiskLevel.AT_RISK
    assert result.status == ETAStatus.AT_RISK
    assert result.is_behind


def test_eight_hours_late_is_at_risk_by_default():
    calculator = ETARiskCalculator()

    planned = datetime(2026, 8, 25, 16, 0)
    current = datetime(2026, 8, 26, 0, 0)

    result = calculator.calculate_variance(
        planned_eta=planned,
        current_eta=current,
        status=ETAStatus.ON_TRACK,
    )

    assert result.variance == timedelta(hours=8)
    assert result.variance_hours == Decimal("8")
    assert result.risk_level == ETARiskLevel.AT_RISK
    assert result.status == ETAStatus.AT_RISK


def test_more_than_eight_hours_late_is_late():
    calculator = ETARiskCalculator()

    planned = datetime(2026, 8, 25, 16, 0)
    current = datetime(2026, 8, 26, 1, 0)

    result = calculator.calculate_variance(
        planned_eta=planned,
        current_eta=current,
        status=ETAStatus.ON_TRACK,
    )

    assert result.variance == timedelta(hours=9)
    assert result.variance_hours == Decimal("9")
    assert result.risk_level == ETARiskLevel.LATE
    assert result.status == ETAStatus.LATE
    assert result.is_behind


def test_custom_risk_thresholds_are_respected():
    calculator = ETARiskCalculator(
        ETARiskThresholds(
            at_risk_hours=Decimal("2"),
            late_hours=Decimal("6"),
        )
    )

    planned = datetime(2026, 8, 25, 16, 0)
    current = datetime(2026, 8, 25, 19, 0)

    result = calculator.calculate_variance(
        planned_eta=planned,
        current_eta=current,
        status=ETAStatus.ON_TRACK,
    )

    assert result.variance_hours == Decimal("3")
    assert result.risk_level == ETARiskLevel.AT_RISK
    assert result.status == ETAStatus.AT_RISK


def test_custom_threshold_can_classify_same_variance_as_late():
    calculator = ETARiskCalculator(
        ETARiskThresholds(
            at_risk_hours=Decimal("2"),
            late_hours=Decimal("4"),
        )
    )

    planned = datetime(2026, 8, 25, 16, 0)
    current = datetime(2026, 8, 25, 21, 0)

    result = calculator.calculate_variance(
        planned_eta=planned,
        current_eta=current,
        status=ETAStatus.ON_TRACK,
    )

    assert result.variance_hours == Decimal("5")
    assert result.risk_level == ETARiskLevel.LATE
    assert result.status == ETAStatus.LATE


def test_missing_planned_eta_returns_unknown():
    calculator = ETARiskCalculator()

    result = calculator.calculate_variance(
        planned_eta=None,
        current_eta=datetime(2026, 8, 25, 16, 0),
        status=ETAStatus.ON_TRACK,
    )

    assert result.variance is None
    assert result.variance_hours is None
    assert result.risk_level == ETARiskLevel.UNKNOWN
    assert result.status == ETAStatus.ON_TRACK
    assert not result.is_ahead
    assert not result.is_on_schedule
    assert not result.is_behind


def test_missing_current_eta_returns_unknown():
    calculator = ETARiskCalculator()

    result = calculator.calculate_variance(
        planned_eta=datetime(2026, 8, 25, 16, 0),
        current_eta=None,
        status=ETAStatus.ON_TRACK,
    )

    assert result.variance is None
    assert result.variance_hours is None
    assert result.risk_level == ETARiskLevel.UNKNOWN
    assert result.status == ETAStatus.ON_TRACK


def test_both_eta_values_missing_returns_unknown():
    calculator = ETARiskCalculator()

    result = calculator.calculate_variance(
        planned_eta=None,
        current_eta=None,
        status=ETAStatus.UNKNOWN,
    )

    assert result.variance is None
    assert result.variance_hours is None
    assert result.risk_level == ETARiskLevel.UNKNOWN
    assert result.status == ETAStatus.UNKNOWN


def test_completed_order_has_completed_risk_level():
    calculator = ETARiskCalculator()

    planned = datetime(2026, 8, 25, 16, 0)
    current = datetime(2026, 8, 25, 20, 0)

    result = calculator.calculate_variance(
        planned_eta=planned,
        current_eta=current,
        status=ETAStatus.COMPLETED,
    )

    assert result.risk_level == ETARiskLevel.COMPLETED
    assert result.status == ETAStatus.COMPLETED
    assert result.variance == timedelta(hours=4)
    assert result.variance_hours == Decimal("4")


def test_material_wait_status_is_preserved():
    calculator = ETARiskCalculator()

    planned = datetime(2026, 8, 25, 16, 0)
    current = datetime(2026, 8, 25, 22, 0)

    result = calculator.calculate_variance(
        planned_eta=planned,
        current_eta=current,
        status=ETAStatus.MATERIAL_WAIT,
    )

    assert result.risk_level == ETARiskLevel.AT_RISK
    assert result.status == ETAStatus.MATERIAL_WAIT


def test_not_started_status_is_preserved():
    calculator = ETARiskCalculator()

    planned = datetime(2026, 8, 25, 16, 0)
    current = datetime(2026, 8, 25, 22, 0)

    result = calculator.calculate_variance(
        planned_eta=planned,
        current_eta=current,
        status=ETAStatus.NOT_STARTED,
    )

    assert result.risk_level == ETARiskLevel.AT_RISK
    assert result.status == ETAStatus.NOT_STARTED


def test_unknown_status_is_preserved():
    calculator = ETARiskCalculator()

    planned = datetime(2026, 8, 25, 16, 0)
    current = datetime(2026, 8, 25, 22, 0)

    result = calculator.calculate_variance(
        planned_eta=planned,
        current_eta=current,
        status=ETAStatus.UNKNOWN,
    )

    assert result.risk_level == ETARiskLevel.AT_RISK
    assert result.status == ETAStatus.UNKNOWN


def test_classify_returns_only_risk_level():
    calculator = ETARiskCalculator()

    risk = calculator.classify(
        planned_eta=datetime(2026, 8, 25, 16, 0),
        current_eta=datetime(2026, 8, 25, 22, 0),
        status=ETAStatus.ON_TRACK,
    )

    assert risk == ETARiskLevel.AT_RISK


def test_variance_is_positive_when_late():
    calculator = ETARiskCalculator()

    result = calculator.calculate_variance(
        planned_eta=datetime(2026, 8, 25, 16, 0),
        current_eta=datetime(2026, 8, 25, 18, 30),
        status=ETAStatus.ON_TRACK,
    )

    assert result.variance_hours == Decimal("2.5")
    assert result.is_behind
    assert not result.is_ahead


def test_variance_is_negative_when_ahead():
    calculator = ETARiskCalculator()

    result = calculator.calculate_variance(
        planned_eta=datetime(2026, 8, 25, 16, 0),
        current_eta=datetime(2026, 8, 25, 13, 30),
        status=ETAStatus.ON_TRACK,
    )

    assert result.variance_hours == Decimal("-2.5")
    assert result.is_ahead
    assert not result.is_behind


def test_reason_is_present_for_on_schedule():
    calculator = ETARiskCalculator()

    result = calculator.calculate_variance(
        planned_eta=datetime(2026, 8, 25, 16, 0),
        current_eta=datetime(2026, 8, 25, 16, 0),
        status=ETAStatus.ON_TRACK,
    )

    assert result.reason == (
        "Live ETA matches the planned ETA"
    )


def test_reason_is_present_when_ahead():
    calculator = ETARiskCalculator()

    result = calculator.calculate_variance(
        planned_eta=datetime(2026, 8, 25, 16, 0),
        current_eta=datetime(2026, 8, 25, 12, 0),
        status=ETAStatus.ON_TRACK,
    )

    assert result.reason == (
        "Live ETA is ahead of the planned ETA"
    )


def test_reason_is_present_when_at_risk():
    calculator = ETARiskCalculator()

    result = calculator.calculate_variance(
        planned_eta=datetime(2026, 8, 25, 16, 0),
        current_eta=datetime(2026, 8, 25, 21, 0),
        status=ETAStatus.ON_TRACK,
    )

    assert result.reason == (
        "Live ETA has moved beyond the normal "
        "schedule variance threshold"
    )


def test_reason_is_present_when_late():
    calculator = ETARiskCalculator()

    result = calculator.calculate_variance(
        planned_eta=datetime(2026, 8, 25, 16, 0),
        current_eta=datetime(2026, 8, 26, 2, 0),
        status=ETAStatus.ON_TRACK,
    )

    assert result.reason == (
        "Live ETA has exceeded the late schedule "
        "variance threshold"
    )


def test_completed_reason_is_present():
    calculator = ETARiskCalculator()

    result = calculator.calculate_variance(
        planned_eta=datetime(2026, 8, 25, 16, 0),
        current_eta=datetime(2026, 8, 25, 18, 0),
        status=ETAStatus.COMPLETED,
    )

    assert result.reason == (
        "Manufacturing Order is completed"
    )


def test_missing_eta_reason_is_present():
    calculator = ETARiskCalculator()

    result = calculator.calculate_variance(
        planned_eta=None,
        current_eta=None,
        status=ETAStatus.UNKNOWN,
    )

    assert result.reason == (
        "Planned ETA or current ETA is not available"
    )


def test_default_thresholds_are_correct():
    thresholds = ETARiskThresholds()

    assert thresholds.at_risk_hours == Decimal("4")
    assert thresholds.late_hours == Decimal("8")


def test_negative_at_risk_threshold_is_rejected():
    with pytest.raises(ValueError):
        ETARiskThresholds(
            at_risk_hours=Decimal("-1"),
            late_hours=Decimal("8"),
        )


def test_zero_late_threshold_is_rejected():
    with pytest.raises(ValueError):
        ETARiskThresholds(
            at_risk_hours=Decimal("0"),
            late_hours=Decimal("0"),
        )


def test_late_threshold_equal_to_at_risk_is_rejected():
    with pytest.raises(ValueError):
        ETARiskThresholds(
            at_risk_hours=Decimal("4"),
            late_hours=Decimal("4"),
        )


def test_late_threshold_below_at_risk_is_rejected():
    with pytest.raises(ValueError):
        ETARiskThresholds(
            at_risk_hours=Decimal("8"),
            late_hours=Decimal("4"),
        )


def test_variance_hours_uses_decimal_precision():
    calculator = ETARiskCalculator()

    result = calculator.calculate_variance(
        planned_eta=datetime(2026, 8, 25, 16, 0),
        current_eta=datetime(2026, 8, 25, 17, 15),
        status=ETAStatus.ON_TRACK,
    )

    assert isinstance(
        result.variance_hours,
        Decimal,
    )

    assert result.variance_hours == Decimal("1.25")


def test_risk_calculator_does_not_modify_input_values():
    calculator = ETARiskCalculator()

    planned = datetime(2026, 8, 25, 16, 0)
    current = datetime(2026, 8, 25, 20, 0)

    result = calculator.calculate_variance(
        planned_eta=planned,
        current_eta=current,
        status=ETAStatus.ON_TRACK,
    )

    assert result.planned_eta == planned
    assert result.current_eta == current


def test_zero_delay_is_not_at_risk():
    calculator = ETARiskCalculator(
        ETARiskThresholds(
            at_risk_hours=Decimal("1"),
            late_hours=Decimal("4"),
        )
    )

    result = calculator.calculate_variance(
        planned_eta=datetime(2026, 8, 25, 16, 0),
        current_eta=datetime(2026, 8, 25, 16, 0),
        status=ETAStatus.ON_TRACK,
    )

    assert result.risk_level == ETARiskLevel.ON_TRACK


def test_one_hour_delay_at_custom_threshold_is_on_track():
    calculator = ETARiskCalculator(
        ETARiskThresholds(
            at_risk_hours=Decimal("1"),
            late_hours=Decimal("4"),
        )
    )

    result = calculator.calculate_variance(
        planned_eta=datetime(2026, 8, 25, 16, 0),
        current_eta=datetime(2026, 8, 25, 17, 0),
        status=ETAStatus.ON_TRACK,
    )

    assert result.risk_level == ETARiskLevel.ON_TRACK


def test_more_than_custom_at_risk_threshold_is_at_risk():
    calculator = ETARiskCalculator(
        ETARiskThresholds(
            at_risk_hours=Decimal("1"),
            late_hours=Decimal("4"),
        )
    )

    result = calculator.calculate_variance(
        planned_eta=datetime(2026, 8, 25, 16, 0),
        current_eta=datetime(2026, 8, 25, 18, 0),
        status=ETAStatus.ON_TRACK,
    )

    assert result.risk_level == ETARiskLevel.AT_RISK


def test_more_than_custom_late_threshold_is_late():
    calculator = ETARiskCalculator(
        ETARiskThresholds(
            at_risk_hours=Decimal("1"),
            late_hours=Decimal("4"),
        )
    )

    result = calculator.calculate_variance(
        planned_eta=datetime(2026, 8, 25, 16, 0),
        current_eta=datetime(2026, 8, 25, 21, 0),
        status=ETAStatus.ON_TRACK,
    )

    assert result.risk_level == ETARiskLevel.LATE