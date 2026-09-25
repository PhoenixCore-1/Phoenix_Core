from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from phoenix_production_module.production.eta_required_risk import (
    RequiredDateRisk,
    RequiredDateRiskLevel,
)
from phoenix_production_module.production.eta_risk import (
    ETARiskLevel,
    ETAScheduleVariance,
)
from phoenix_production_module.production.eta_risk_summary import (
    ETARiskDecision,
    ETARiskSummary,
    ETARiskSummaryCalculator,
)


# ---------------------------------------------------------------------------
# Phoenix Production Module 1.3.20
# ETA Risk Summary / Decision Layer
# ---------------------------------------------------------------------------


def make_schedule_risk(
    risk_level: ETARiskLevel,
) -> ETAScheduleVariance:
    """
    Build a valid ETAScheduleVariance using the current
    Production Module ETA model contract.
    """

    planned_eta = datetime(
        2026,
        8,
        25,
        16,
        0,
    )

    current_eta = datetime(
        2026,
        8,
        25,
        18,
        0,
    )

    variance = current_eta - planned_eta

    return ETAScheduleVariance(
        planned_eta=planned_eta,
        current_eta=current_eta,
        variance=variance,
        variance_hours=Decimal("2"),
        risk_level=risk_level,
        status=None,
        reason="Test schedule risk",
    )


def make_required_date_risk(
    risk_level: RequiredDateRiskLevel,
) -> RequiredDateRisk:
    """
    Build a valid RequiredDateRisk using the current
    Production Module model contract.
    """

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
        25,
        18,
        0,
    )

    variance = current_eta - required_date

    return RequiredDateRisk(
        required_date=required_date,
        current_eta=current_eta,
        variance=variance,
        variance_hours=Decimal("-70"),
        risk_level=risk_level,
        reason="Test required-date risk",
    )


def test_on_track_when_both_risks_are_safe():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.ON_TRACK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert isinstance(result, ETARiskSummary)
    assert result.schedule_risk == ETARiskLevel.ON_TRACK
    assert result.required_date_risk == RequiredDateRiskLevel.ON_TIME
    assert result.decision == ETARiskDecision.ON_TRACK
    assert result.action_required is False
    assert result.customer_date_safe is True
    assert result.schedule_is_safe is True


def test_late_schedule_but_customer_date_safe():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.LATE,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result.decision == (
        ETARiskDecision.BEHIND_PLAN_CUSTOMER_SAFE
    )
    assert result.customer_date_safe is True
    assert result.schedule_is_safe is False
    assert result.action_required is True


def test_schedule_at_risk_but_customer_date_safe():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.AT_RISK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result.decision == (
        ETARiskDecision.SCHEDULE_AT_RISK_CUSTOMER_SAFE
    )
    assert result.customer_date_safe is True
    assert result.schedule_is_safe is False
    assert result.action_required is True


def test_customer_date_at_risk_takes_priority():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.ON_TRACK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.AT_RISK,
        ),
    )

    assert result.decision == (
        ETARiskDecision.CUSTOMER_DATE_AT_RISK
    )
    assert result.customer_date_safe is True
    assert result.action_required is True


def test_customer_date_at_risk_with_late_schedule():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.LATE,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.AT_RISK,
        ),
    )

    assert result.decision == (
        ETARiskDecision.CUSTOMER_DATE_AT_RISK
    )
    assert result.action_required is True


def test_customer_date_late_with_on_track_schedule_is_conflict():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.ON_TRACK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.LATE,
        ),
    )

    assert result.decision == (
        ETARiskDecision.REQUIRED_DATE_CONFLICT
    )
    assert result.customer_date_safe is False
    assert result.action_required is True


def test_customer_date_late_with_at_risk_schedule():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.AT_RISK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.LATE,
        ),
    )

    assert result.decision == (
        ETARiskDecision.CUSTOMER_DATE_LATE
    )
    assert result.customer_date_safe is False
    assert result.action_required is True


def test_customer_date_late_with_late_schedule():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.LATE,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.LATE,
        ),
    )

    assert result.decision == (
        ETARiskDecision.CUSTOMER_DATE_LATE
    )
    assert result.customer_date_safe is False
    assert result.action_required is True


def test_unknown_schedule_risk_produces_unknown_decision():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.UNKNOWN,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result.decision == ETARiskDecision.UNKNOWN
    assert result.action_required is False


def test_unknown_required_date_risk_produces_unknown_decision():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.ON_TRACK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.UNKNOWN,
        ),
    )

    assert result.decision == ETARiskDecision.UNKNOWN
    assert result.action_required is False


def test_unknown_either_risk_produces_unknown_decision():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.UNKNOWN,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.UNKNOWN,
        ),
    )

    assert result.decision == ETARiskDecision.UNKNOWN


def test_completed_required_date_risk_produces_completed():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.LATE,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.COMPLETED,
        ),
    )

    assert result.decision == ETARiskDecision.COMPLETED
    assert result.action_required is False


def test_summary_text_for_on_track():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.ON_TRACK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result.summary == (
        "Production is on track and the "
        "required date is safe"
    )


def test_summary_text_for_behind_plan_customer_safe():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.LATE,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result.summary == (
        "Production is behind plan but the "
        "required date remains safe"
    )


def test_summary_text_for_schedule_at_risk_customer_safe():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.AT_RISK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result.summary == (
        "Production schedule is at risk but the "
        "required date remains safe"
    )


def test_summary_text_for_customer_date_at_risk():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.LATE,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.AT_RISK,
        ),
    )

    assert result.summary == (
        "The required date is at risk"
    )


def test_summary_text_for_customer_date_late():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.LATE,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.LATE,
        ),
    )

    assert result.summary == (
        "The required date is expected to be missed"
    )


def test_summary_text_for_required_date_conflict():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.ON_TRACK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.LATE,
        ),
    )

    assert result.summary == (
        "The current ETA conflicts with the "
        "required date despite the internal "
        "schedule appearing on track"
    )


def test_summary_text_for_unknown():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.UNKNOWN,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result.summary == (
        "ETA risk cannot be determined because "
        "required risk information is incomplete"
    )


def test_summary_text_for_completed():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.LATE,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.COMPLETED,
        ),
    )

    assert result.summary == (
        "Production is completed"
    )


def test_decision_convenience_method():
    calculator = ETARiskSummaryCalculator()

    result = calculator.decision(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.LATE,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result == (
        ETARiskDecision.BEHIND_PLAN_CUSTOMER_SAFE
    )


def test_summary_convenience_method():
    calculator = ETARiskSummaryCalculator()

    result = calculator.summary(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.ON_TRACK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result == (
        "Production is on track and the "
        "required date is safe"
    )


def test_action_required_convenience_method():
    calculator = ETARiskSummaryCalculator()

    result = calculator.action_required(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.LATE,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result is True


def test_summary_on_track_properties():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.ON_TRACK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result.is_on_track
    assert result.is_customer_safe
    assert not result.is_customer_at_risk
    assert not result.is_customer_late
    assert not result.requires_action


def test_summary_customer_at_risk_properties():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.ON_TRACK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.AT_RISK,
        ),
    )

    assert not result.is_on_track
    assert result.is_customer_safe
    assert result.is_customer_at_risk
    assert not result.is_customer_late
    assert result.requires_action


def test_summary_customer_late_properties():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.LATE,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.LATE,
        ),
    )

    assert not result.is_on_track
    assert not result.is_customer_safe
    assert not result.is_customer_at_risk
    assert result.is_customer_late
    assert result.requires_action


def test_summary_result_is_immutable():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.ON_TRACK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    with pytest.raises(Exception):
        result.decision = ETARiskDecision.CUSTOMER_DATE_LATE


def test_summary_result_preserves_underlying_risk_levels():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.AT_RISK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.AT_RISK,
        ),
    )

    assert result.schedule_risk == ETARiskLevel.AT_RISK
    assert result.required_date_risk == (
        RequiredDateRiskLevel.AT_RISK
    )


def test_customer_date_at_risk_has_priority_over_schedule_at_risk():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.AT_RISK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.AT_RISK,
        ),
    )

    assert result.decision == (
        ETARiskDecision.CUSTOMER_DATE_AT_RISK
    )


def test_customer_date_late_has_priority_over_schedule_at_risk():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.AT_RISK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.LATE,
        ),
    )

    assert result.decision == (
        ETARiskDecision.CUSTOMER_DATE_LATE
    )


def test_customer_date_late_has_priority_over_schedule_late():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.LATE,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.LATE,
        ),
    )

    assert result.decision == (
        ETARiskDecision.CUSTOMER_DATE_LATE
    )


def test_completed_has_priority_over_schedule_risk():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.UNKNOWN,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.COMPLETED,
        ),
    )

    assert result.decision == (
        ETARiskDecision.COMPLETED
    )


def test_unknown_required_date_is_not_marked_customer_safe():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.ON_TRACK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.UNKNOWN,
        ),
    )

    assert result.customer_date_safe is False
    assert result.decision == (
        ETARiskDecision.UNKNOWN
    )


def test_unknown_schedule_does_not_trigger_action_by_itself():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.UNKNOWN,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result.action_required is False


def test_customer_date_at_risk_triggers_action():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.ON_TRACK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.AT_RISK,
        ),
    )

    assert result.action_required is True


def test_customer_date_late_triggers_action():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.ON_TRACK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.LATE,
        ),
    )

    assert result.action_required is True


def test_behind_plan_customer_safe_triggers_action():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.LATE,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result.action_required is True


def test_schedule_at_risk_customer_safe_triggers_action():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.AT_RISK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result.action_required is True


def test_completed_does_not_require_action():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.LATE,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.COMPLETED,
        ),
    )

    assert result.action_required is False


def test_on_track_customer_safe_means_schedule_is_safe():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.ON_TRACK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result.schedule_is_safe is True


def test_schedule_at_risk_means_schedule_is_not_safe():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.AT_RISK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result.schedule_is_safe is False


def test_late_schedule_means_schedule_is_not_safe():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.LATE,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result.schedule_is_safe is False


def test_customer_date_at_risk_is_still_customer_safe():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.ON_TRACK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.AT_RISK,
        ),
    )

    assert result.customer_date_safe is True


def test_customer_date_late_is_not_customer_safe():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.ON_TRACK,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.LATE,
        ),
    )

    assert result.customer_date_safe is False


def test_completed_is_customer_safe():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.LATE,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.COMPLETED,
        ),
    )

    assert result.customer_date_safe is True


def test_decision_enum_values_are_stable():
    assert ETARiskDecision.UNKNOWN.value == "UNKNOWN"
    assert ETARiskDecision.ON_TRACK.value == "ON_TRACK"
    assert (
        ETARiskDecision.BEHIND_PLAN_CUSTOMER_SAFE.value
        == "BEHIND_PLAN_CUSTOMER_SAFE"
    )
    assert (
        ETARiskDecision.SCHEDULE_AT_RISK_CUSTOMER_SAFE.value
        == "SCHEDULE_AT_RISK_CUSTOMER_SAFE"
    )
    assert (
        ETARiskDecision.CUSTOMER_DATE_AT_RISK.value
        == "CUSTOMER_DATE_AT_RISK"
    )
    assert (
        ETARiskDecision.CUSTOMER_DATE_LATE.value
        == "CUSTOMER_DATE_LATE"
    )
    assert (
        ETARiskDecision.REQUIRED_DATE_CONFLICT.value
        == "REQUIRED_DATE_CONFLICT"
    )
    assert (
        ETARiskDecision.COMPLETED.value
        == "COMPLETED"
    )


def test_summary_contains_both_risk_levels():
    calculator = ETARiskSummaryCalculator()

    result = calculator.calculate(
        schedule_risk=make_schedule_risk(
            ETARiskLevel.LATE,
        ),
        required_date_risk=make_required_date_risk(
            RequiredDateRiskLevel.ON_TIME,
        ),
    )

    assert result.schedule_risk == ETARiskLevel.LATE
    assert result.required_date_risk == (
        RequiredDateRiskLevel.ON_TIME
    )


def test_summary_calculation_is_repeatable():
    calculator = ETARiskSummaryCalculator()

    schedule_risk = make_schedule_risk(
        ETARiskLevel.LATE,
    )

    required_date_risk = make_required_date_risk(
        RequiredDateRiskLevel.ON_TIME,
    )

    first = calculator.calculate(
        schedule_risk=schedule_risk,
        required_date_risk=required_date_risk,
    )

    second = calculator.calculate(
        schedule_risk=schedule_risk,
        required_date_risk=required_date_risk,
    )

    assert first == second


def test_summary_does_not_modify_schedule_risk():
    calculator = ETARiskSummaryCalculator()

    schedule_risk = make_schedule_risk(
        ETARiskLevel.LATE,
    )

    required_date_risk = make_required_date_risk(
        RequiredDateRiskLevel.ON_TIME,
    )

    original = schedule_risk

    calculator.calculate(
        schedule_risk=schedule_risk,
        required_date_risk=required_date_risk,
    )

    assert schedule_risk == original


def test_summary_does_not_modify_required_date_risk():
    calculator = ETARiskSummaryCalculator()

    schedule_risk = make_schedule_risk(
        ETARiskLevel.LATE,
    )

    required_date_risk = make_required_date_risk(
        RequiredDateRiskLevel.ON_TIME,
    )

    original = required_date_risk

    calculator.calculate(
        schedule_risk=schedule_risk,
        required_date_risk=required_date_risk,
    )

    assert required_date_risk == original