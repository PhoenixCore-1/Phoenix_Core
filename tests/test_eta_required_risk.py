from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from phoenix_production_module.production.eta_required_risk import (
    RequiredDateRisk,
    RequiredDateRiskCalculator,
    RequiredDateRiskLevel,
    RequiredDateRiskThresholds,
)


# ---------------------------------------------------------------------------
# Phoenix Production Module 1.3.18
# Required-Date Risk
# ---------------------------------------------------------------------------


def test_live_eta_well_before_required_date_is_on_time():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 25, 16, 0),
    )

    assert result.variance == timedelta(hours=-72)
    assert result.variance_hours == Decimal("-72")
    assert result.risk_level == RequiredDateRiskLevel.ON_TIME
    assert result.can_meet_required_date
    assert result.is_before_required_date
    assert not result.is_exactly_required_date
    assert not result.is_after_required_date


def test_live_eta_inside_required_date_buffer_is_at_risk():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 28, 8, 0),
    )

    assert result.variance == timedelta(hours=-8)
    assert result.variance_hours == Decimal("-8")
    assert result.risk_level == RequiredDateRiskLevel.AT_RISK
    assert result.can_meet_required_date
    assert result.is_before_required_date


def test_live_eta_exactly_on_required_date_is_at_risk_by_default():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 28, 16, 0),
    )

    assert result.variance == timedelta(0)
    assert result.variance_hours == Decimal("0")
    assert result.risk_level == RequiredDateRiskLevel.AT_RISK
    assert result.can_meet_required_date
    assert result.is_exactly_required_date


def test_live_eta_after_required_date_is_late():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 28, 20, 0),
    )

    assert result.variance == timedelta(hours=4)
    assert result.variance_hours == Decimal("4")
    assert result.risk_level == RequiredDateRiskLevel.LATE
    assert not result.can_meet_required_date
    assert result.is_after_required_date


def test_custom_buffer_allows_exact_required_date_to_be_on_time():
    calculator = RequiredDateRiskCalculator(
        RequiredDateRiskThresholds(
            at_risk_buffer_hours=Decimal("0"),
        )
    )

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 28, 16, 0),
    )

    assert result.risk_level == RequiredDateRiskLevel.AT_RISK
    assert result.can_meet_required_date


def test_custom_buffer_classifies_one_hour_before_required_date():
    calculator = RequiredDateRiskCalculator(
        RequiredDateRiskThresholds(
            at_risk_buffer_hours=Decimal("4"),
        )
    )

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 28, 15, 0),
    )

    assert result.variance_hours == Decimal("-1")
    assert result.risk_level == RequiredDateRiskLevel.AT_RISK


def test_custom_buffer_classifies_beyond_buffer_as_on_time():
    calculator = RequiredDateRiskCalculator(
        RequiredDateRiskThresholds(
            at_risk_buffer_hours=Decimal("4"),
        )
    )

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 28, 10, 0),
    )

    assert result.variance_hours == Decimal("-6")
    assert result.risk_level == RequiredDateRiskLevel.ON_TIME


def test_zero_buffer_makes_positive_variance_late():
    calculator = RequiredDateRiskCalculator(
        RequiredDateRiskThresholds(
            at_risk_buffer_hours=Decimal("0"),
        )
    )

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 28, 16, 1),
    )

    assert result.variance_hours == Decimal(
        "0.01666666666666666666666666667"
    )
    assert result.risk_level == RequiredDateRiskLevel.LATE


def test_missing_required_date_returns_unknown():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=None,
        current_eta=datetime(2026, 8, 28, 16, 0),
    )

    assert result.variance is None
    assert result.variance_hours is None
    assert result.risk_level == RequiredDateRiskLevel.UNKNOWN
    assert not result.can_meet_required_date


def test_missing_current_eta_returns_unknown():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=None,
    )

    assert result.variance is None
    assert result.variance_hours is None
    assert result.risk_level == RequiredDateRiskLevel.UNKNOWN


def test_both_dates_missing_returns_unknown():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=None,
        current_eta=None,
    )

    assert result.variance is None
    assert result.variance_hours is None
    assert result.risk_level == RequiredDateRiskLevel.UNKNOWN


def test_completed_order_returns_completed():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 30, 16, 0),
        completed=True,
    )

    assert result.variance == timedelta(hours=48)
    assert result.variance_hours == Decimal("48")
    assert result.risk_level == RequiredDateRiskLevel.COMPLETED


def test_completed_order_without_dates_still_returns_completed():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=None,
        current_eta=None,
        completed=True,
    )

    assert result.variance is None
    assert result.variance_hours is None
    assert result.risk_level == RequiredDateRiskLevel.COMPLETED


def test_classify_returns_only_required_date_risk():
    calculator = RequiredDateRiskCalculator()

    result = calculator.classify(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 28, 20, 0),
    )

    assert result == RequiredDateRiskLevel.LATE


def test_required_date_risk_is_before_when_eta_is_earlier():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 27, 16, 0),
    )

    assert result.is_before_required_date
    assert not result.is_after_required_date
    assert not result.is_exactly_required_date


def test_required_date_risk_is_exactly_on_date():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 28, 16, 0),
    )

    assert result.is_exactly_required_date
    assert not result.is_before_required_date
    assert not result.is_after_required_date


def test_required_date_risk_is_after_when_eta_is_later():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 28, 17, 0),
    )

    assert result.is_after_required_date
    assert not result.is_before_required_date
    assert not result.is_exactly_required_date


def test_required_date_variance_uses_decimal_hours():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 28, 18, 30),
    )

    assert isinstance(
        result.variance_hours,
        Decimal,
    )

    assert result.variance_hours == Decimal("2.5")


def test_required_date_reason_for_on_time():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 26, 16, 0),
    )

    assert result.risk_level == RequiredDateRiskLevel.ON_TIME

    assert result.reason == (
        "Live ETA is sufficiently before the required date"
    )


def test_required_date_reason_for_at_risk():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 28, 8, 0),
    )

    assert result.reason == (
        "Live ETA is before the required date but "
        "inside the required-date risk buffer"
    )


def test_required_date_reason_for_exact_date():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 28, 16, 0),
    )

    assert result.reason == (
        "Live ETA falls exactly on the required date"
    )


def test_required_date_reason_for_late_eta():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 28, 20, 0),
    )

    assert result.reason == (
        "Live ETA is later than the required date"
    )


def test_required_date_reason_for_completed_order():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=datetime(2026, 8, 28, 16, 0),
        current_eta=datetime(2026, 8, 28, 20, 0),
        completed=True,
    )

    assert result.reason == (
        "Manufacturing Order is completed"
    )


def test_required_date_reason_for_missing_values():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
        required_date=None,
        current_eta=None,
    )

    assert result.reason == (
        "Required date or current ETA is not available"
    )


def test_default_required_date_buffer_is_24_hours():
    thresholds = RequiredDateRiskThresholds()

    assert thresholds.at_risk_buffer_hours == Decimal("24")


def test_negative_required_date_buffer_is_rejected():
    with pytest.raises(ValueError):
        RequiredDateRiskThresholds(
            at_risk_buffer_hours=Decimal("-1"),
        )


def test_required_date_risk_does_not_modify_input_values():
    calculator = RequiredDateRiskCalculator()

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
        28,
        20,
        0,
    )

    result = calculator.calculate(
        required_date=required_date,
        current_eta=current_eta,
    )

    assert result.required_date == required_date
    assert result.current_eta == current_eta


def test_required_date_risk_dataclass_is_immutable():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
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

    with pytest.raises(Exception):
        result.risk_level = RequiredDateRiskLevel.ON_TIME


def test_required_date_risk_result_has_expected_type():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
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

    assert isinstance(
        result,
        RequiredDateRisk,
    )


def test_required_date_threshold_is_decimal():
    thresholds = RequiredDateRiskThresholds(
        at_risk_buffer_hours=Decimal("12.5"),
    )

    assert isinstance(
        thresholds.at_risk_buffer_hours,
        Decimal,
    )


def test_required_date_risk_with_large_buffer():
    calculator = RequiredDateRiskCalculator(
        RequiredDateRiskThresholds(
            at_risk_buffer_hours=Decimal("72"),
        )
    )

    result = calculator.calculate(
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

    assert result.variance_hours == Decimal("-48")
    assert result.risk_level == RequiredDateRiskLevel.AT_RISK


def test_required_date_risk_far_ahead_with_large_buffer():
    calculator = RequiredDateRiskCalculator(
        RequiredDateRiskThresholds(
            at_risk_buffer_hours=Decimal("24"),
        )
    )

    result = calculator.calculate(
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
    assert result.risk_level == RequiredDateRiskLevel.ON_TIME


def test_required_date_risk_one_minute_late_is_late():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
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

    assert result.risk_level == RequiredDateRiskLevel.LATE
    assert result.is_after_required_date
    assert not result.can_meet_required_date


def test_required_date_risk_one_minute_before_date_is_at_risk():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
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
            15,
            59,
        ),
    )

    assert result.risk_level == RequiredDateRiskLevel.AT_RISK
    assert result.can_meet_required_date


def test_required_date_risk_twenty_four_hours_before_date_is_at_risk():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
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
            27,
            16,
            0,
        ),
    )

    assert result.variance_hours == Decimal("-24")
    assert result.risk_level == RequiredDateRiskLevel.AT_RISK


def test_required_date_risk_more_than_twenty_four_hours_before_date_is_on_time():
    calculator = RequiredDateRiskCalculator()

    result = calculator.calculate(
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
            27,
            15,
            59,
        ),
    )

    assert result.variance_hours == Decimal(
        "-24.01666666666666666666666667"
    )
    assert result.risk_level == RequiredDateRiskLevel.ON_TIME