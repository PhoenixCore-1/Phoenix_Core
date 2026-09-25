from datetime import datetime

import pytest

from phoenix_production_module.production.eta_operational_snapshot import (
    ETAOperationalSnapshot,
)
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


# ---------------------------------------------------------------------------
# Phoenix Production Module 1.3.22
# Operational ETA Snapshot Tests
# ---------------------------------------------------------------------------


def _schedule_is_safe_for(
    schedule_risk: ETARiskLevel,
) -> bool:
    """
    Derive the existing ETARiskSummary schedule safety flag.

    ON_TRACK is safe.
    AT_RISK, LATE and UNKNOWN are not safe.
    """

    return schedule_risk == ETARiskLevel.ON_TRACK


def _customer_date_safe_for(
    required_date_risk: RequiredDateRiskLevel,
) -> bool:
    """
    Derive the existing ETARiskSummary customer-date safety flag.

    ON_TIME and AT_RISK remain before the required date.
    LATE and UNKNOWN are not considered safe.
    """

    return required_date_risk in (
        RequiredDateRiskLevel.ON_TIME,
        RequiredDateRiskLevel.AT_RISK,
        RequiredDateRiskLevel.COMPLETED,
    )


def make_summary(
    *,
    schedule_risk=ETARiskLevel.ON_TRACK,
    required_date_risk=RequiredDateRiskLevel.ON_TIME,
    decision=ETARiskDecision.ON_TRACK,
    action_required=False,
    summary="Production is on track and the required date is safe",
    customer_date_safe=None,
    schedule_is_safe=None,
):
    """
    Create a valid ETARiskSummary using the existing production
    contract.
    """

    if schedule_is_safe is None:
        schedule_is_safe = _schedule_is_safe_for(
            schedule_risk,
        )

    if customer_date_safe is None:
        customer_date_safe = _customer_date_safe_for(
            required_date_risk,
        )

    return ETARiskSummary(
        schedule_risk=schedule_risk,
        required_date_risk=required_date_risk,
        decision=decision,
        action_required=action_required,
        summary=summary,
        customer_date_safe=customer_date_safe,
        schedule_is_safe=schedule_is_safe,
    )


def make_snapshot(
    *,
    planned_eta=datetime(2026, 8, 25, 16, 0),
    current_eta=datetime(2026, 8, 25, 12, 0),
    required_date=datetime(2026, 8, 28, 16, 0),
    schedule_risk=ETARiskLevel.ON_TRACK,
    required_date_risk=RequiredDateRiskLevel.ON_TIME,
    decision=ETARiskDecision.ON_TRACK,
    action_required=False,
    summary="Production is on track and the required date is safe",
    customer_date_safe=None,
    schedule_is_safe=None,
):
    risk_summary = make_summary(
        schedule_risk=schedule_risk,
        required_date_risk=required_date_risk,
        decision=decision,
        action_required=action_required,
        summary=summary,
        customer_date_safe=customer_date_safe,
        schedule_is_safe=schedule_is_safe,
    )

    return ETAOperationalSnapshot.from_risk_summary(
        planned_eta=planned_eta,
        current_eta=current_eta,
        required_date=required_date,
        summary=risk_summary,
    )


def test_snapshot_can_be_created():
    snapshot = make_snapshot()

    assert isinstance(
        snapshot,
        ETAOperationalSnapshot,
    )


def test_snapshot_preserves_planned_eta():
    planned_eta = datetime(
        2026,
        8,
        25,
        16,
        0,
    )

    snapshot = make_snapshot(
        planned_eta=planned_eta,
    )

    assert snapshot.planned_eta == planned_eta


def test_snapshot_preserves_current_eta():
    current_eta = datetime(
        2026,
        8,
        26,
        12,
        0,
    )

    snapshot = make_snapshot(
        current_eta=current_eta,
    )

    assert snapshot.current_eta == current_eta


def test_snapshot_preserves_required_date():
    required_date = datetime(
        2026,
        8,
        28,
        16,
        0,
    )

    snapshot = make_snapshot(
        required_date=required_date,
    )

    assert snapshot.required_date == required_date


def test_snapshot_preserves_schedule_risk():
    snapshot = make_snapshot(
        schedule_risk=ETARiskLevel.LATE,
        decision=ETARiskDecision.BEHIND_PLAN_CUSTOMER_SAFE,
        action_required=True,
    )

    assert snapshot.schedule_risk == ETARiskLevel.LATE


def test_snapshot_preserves_required_date_risk():
    snapshot = make_snapshot(
        required_date_risk=RequiredDateRiskLevel.AT_RISK,
        decision=ETARiskDecision.CUSTOMER_DATE_AT_RISK,
        action_required=True,
    )

    assert (
        snapshot.required_date_risk
        == RequiredDateRiskLevel.AT_RISK
    )


def test_snapshot_preserves_decision():
    snapshot = make_snapshot(
        decision=ETARiskDecision.CUSTOMER_DATE_LATE,
        required_date_risk=RequiredDateRiskLevel.LATE,
        action_required=True,
    )

    assert (
        snapshot.decision
        == ETARiskDecision.CUSTOMER_DATE_LATE
    )


def test_snapshot_preserves_action_required():
    snapshot = make_snapshot(
        action_required=True,
        decision=ETARiskDecision.CUSTOMER_DATE_AT_RISK,
        required_date_risk=RequiredDateRiskLevel.AT_RISK,
    )

    assert snapshot.action_required is True


def test_snapshot_preserves_summary():
    summary_text = (
        "The required date is expected to be missed"
    )

    snapshot = make_snapshot(
        summary=summary_text,
        decision=ETARiskDecision.CUSTOMER_DATE_LATE,
        required_date_risk=RequiredDateRiskLevel.LATE,
        action_required=True,
    )

    assert snapshot.summary == summary_text


def test_snapshot_is_on_track_when_decision_is_on_track():
    snapshot = make_snapshot(
        decision=ETARiskDecision.ON_TRACK,
    )

    assert snapshot.is_on_track is True


def test_snapshot_is_not_on_track_when_schedule_is_late():
    snapshot = make_snapshot(
        schedule_risk=ETARiskLevel.LATE,
        decision=ETARiskDecision.BEHIND_PLAN_CUSTOMER_SAFE,
        action_required=True,
    )

    assert snapshot.is_on_track is False


def test_customer_on_time_is_customer_safe():
    snapshot = make_snapshot(
        required_date_risk=RequiredDateRiskLevel.ON_TIME,
    )

    assert snapshot.is_customer_safe is True


def test_customer_at_risk_is_customer_safe():
    snapshot = make_snapshot(
        required_date_risk=RequiredDateRiskLevel.AT_RISK,
        decision=ETARiskDecision.CUSTOMER_DATE_AT_RISK,
        action_required=True,
    )

    assert snapshot.is_customer_safe is True


def test_customer_late_is_not_customer_safe():
    snapshot = make_snapshot(
        required_date_risk=RequiredDateRiskLevel.LATE,
        decision=ETARiskDecision.CUSTOMER_DATE_LATE,
        action_required=True,
    )

    assert snapshot.is_customer_safe is False


def test_customer_at_risk_property():
    snapshot = make_snapshot(
        required_date_risk=RequiredDateRiskLevel.AT_RISK,
        decision=ETARiskDecision.CUSTOMER_DATE_AT_RISK,
        action_required=True,
    )

    assert snapshot.is_customer_at_risk is True


def test_customer_on_time_is_not_at_risk():
    snapshot = make_snapshot(
        required_date_risk=RequiredDateRiskLevel.ON_TIME,
    )

    assert snapshot.is_customer_at_risk is False


def test_customer_late_property():
    snapshot = make_snapshot(
        required_date_risk=RequiredDateRiskLevel.LATE,
        decision=ETARiskDecision.CUSTOMER_DATE_LATE,
        action_required=True,
    )

    assert snapshot.is_customer_late is True


def test_customer_at_risk_is_not_customer_late():
    snapshot = make_snapshot(
        required_date_risk=RequiredDateRiskLevel.AT_RISK,
        decision=ETARiskDecision.CUSTOMER_DATE_AT_RISK,
        action_required=True,
    )

    assert snapshot.is_customer_late is False


def test_requires_action_matches_action_required():
    snapshot = make_snapshot(
        action_required=True,
        decision=ETARiskDecision.CUSTOMER_DATE_AT_RISK,
        required_date_risk=RequiredDateRiskLevel.AT_RISK,
    )

    assert snapshot.requires_action is True
    assert snapshot.requires_action == (
        snapshot.action_required
    )


def test_requires_action_false_when_no_action_required():
    snapshot = make_snapshot(
        action_required=False,
        decision=ETARiskDecision.ON_TRACK,
    )

    assert snapshot.requires_action is False


def test_snapshot_is_frozen():
    snapshot = make_snapshot()

    with pytest.raises(Exception):
        snapshot.decision = (
            ETARiskDecision.CUSTOMER_DATE_LATE
        )


def test_snapshot_is_read_only_projection():
    summary = make_summary(
        schedule_risk=ETARiskLevel.LATE,
        required_date_risk=RequiredDateRiskLevel.AT_RISK,
        decision=ETARiskDecision.CUSTOMER_DATE_AT_RISK,
        action_required=True,
        summary="The required date is at risk",
        customer_date_safe=True,
        schedule_is_safe=False,
    )

    snapshot = ETAOperationalSnapshot.from_risk_summary(
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
        summary=summary,
    )

    assert snapshot.schedule_risk == summary.schedule_risk

    assert (
        snapshot.required_date_risk
        == summary.required_date_risk
    )

    assert snapshot.decision == summary.decision

    assert snapshot.action_required == (
        summary.action_required
    )

    assert snapshot.summary == summary.summary


def test_snapshot_does_not_recalculate_risk():
    summary = make_summary(
        schedule_risk=ETARiskLevel.LATE,
        required_date_risk=RequiredDateRiskLevel.ON_TIME,
        decision=ETARiskDecision.BEHIND_PLAN_CUSTOMER_SAFE,
        action_required=True,
        summary=(
            "Production is behind plan but the "
            "required date remains safe"
        ),
        customer_date_safe=True,
        schedule_is_safe=False,
    )

    snapshot = ETAOperationalSnapshot.from_risk_summary(
        planned_eta=None,
        current_eta=None,
        required_date=None,
        summary=summary,
    )

    assert snapshot.schedule_risk == ETARiskLevel.LATE

    assert (
        snapshot.required_date_risk
        == RequiredDateRiskLevel.ON_TIME
    )

    assert snapshot.decision == (
        ETARiskDecision.BEHIND_PLAN_CUSTOMER_SAFE
    )


def test_snapshot_supports_missing_planned_eta():
    snapshot = make_snapshot(
        planned_eta=None,
    )

    assert snapshot.planned_eta is None


def test_snapshot_supports_missing_current_eta():
    snapshot = make_snapshot(
        current_eta=None,
    )

    assert snapshot.current_eta is None


def test_snapshot_supports_missing_required_date():
    snapshot = make_snapshot(
        required_date=None,
    )

    assert snapshot.required_date is None


def test_completed_snapshot():
    snapshot = make_snapshot(
        schedule_risk=ETARiskLevel.UNKNOWN,
        required_date_risk=RequiredDateRiskLevel.COMPLETED,
        decision=ETARiskDecision.COMPLETED,
        action_required=False,
        summary="Production is completed",
        customer_date_safe=True,
        schedule_is_safe=False,
    )

    assert snapshot.decision == (
        ETARiskDecision.COMPLETED
    )

    assert (
        snapshot.required_date_risk
        == RequiredDateRiskLevel.COMPLETED
    )

    assert snapshot.action_required is False


def test_unknown_snapshot():
    snapshot = make_snapshot(
        schedule_risk=ETARiskLevel.UNKNOWN,
        required_date_risk=RequiredDateRiskLevel.UNKNOWN,
        decision=ETARiskDecision.UNKNOWN,
        action_required=False,
        summary=(
            "ETA risk cannot be determined because "
            "required risk information is incomplete"
        ),
        customer_date_safe=False,
        schedule_is_safe=False,
    )

    assert snapshot.decision == (
        ETARiskDecision.UNKNOWN
    )

    assert snapshot.action_required is False


def test_customer_date_late_snapshot():
    snapshot = make_snapshot(
        schedule_risk=ETARiskLevel.LATE,
        required_date_risk=RequiredDateRiskLevel.LATE,
        decision=ETARiskDecision.CUSTOMER_DATE_LATE,
        action_required=True,
        summary=(
            "The required date is expected to be missed"
        ),
        customer_date_safe=False,
        schedule_is_safe=False,
    )

    assert snapshot.is_customer_late is True
    assert snapshot.is_customer_safe is False
    assert snapshot.requires_action is True


def test_customer_date_at_risk_snapshot():
    snapshot = make_snapshot(
        schedule_risk=ETARiskLevel.ON_TRACK,
        required_date_risk=RequiredDateRiskLevel.AT_RISK,
        decision=ETARiskDecision.CUSTOMER_DATE_AT_RISK,
        action_required=True,
        summary="The required date is at risk",
        customer_date_safe=True,
        schedule_is_safe=True,
    )

    assert snapshot.is_customer_at_risk is True
    assert snapshot.is_customer_safe is True
    assert snapshot.requires_action is True


def test_behind_plan_customer_safe_snapshot():
    snapshot = make_snapshot(
        schedule_risk=ETARiskLevel.LATE,
        required_date_risk=RequiredDateRiskLevel.ON_TIME,
        decision=ETARiskDecision.BEHIND_PLAN_CUSTOMER_SAFE,
        action_required=True,
        summary=(
            "Production is behind plan but the "
            "required date remains safe"
        ),
        customer_date_safe=True,
        schedule_is_safe=False,
    )

    assert snapshot.schedule_risk == ETARiskLevel.LATE
    assert snapshot.is_customer_safe is True
    assert snapshot.is_on_track is False
    assert snapshot.requires_action is True


def test_schedule_at_risk_customer_safe_snapshot():
    snapshot = make_snapshot(
        schedule_risk=ETARiskLevel.AT_RISK,
        required_date_risk=RequiredDateRiskLevel.ON_TIME,
        decision=(
            ETARiskDecision.SCHEDULE_AT_RISK_CUSTOMER_SAFE
        ),
        action_required=True,
        summary=(
            "Production schedule is at risk but the "
            "required date remains safe"
        ),
        customer_date_safe=True,
        schedule_is_safe=False,
    )

    assert snapshot.schedule_risk == ETARiskLevel.AT_RISK
    assert snapshot.is_customer_safe is True
    assert snapshot.requires_action is True


def test_required_date_conflict_snapshot():
    snapshot = make_snapshot(
        schedule_risk=ETARiskLevel.ON_TRACK,
        required_date_risk=RequiredDateRiskLevel.LATE,
        decision=ETARiskDecision.REQUIRED_DATE_CONFLICT,
        action_required=True,
        summary=(
            "The current ETA conflicts with the "
            "required date despite the internal "
            "schedule appearing on track"
        ),
        customer_date_safe=False,
        schedule_is_safe=True,
    )

    assert snapshot.is_on_track is False
    assert snapshot.is_customer_safe is False
    assert snapshot.is_customer_late is True
    assert snapshot.requires_action is True


def test_snapshot_equality_is_value_based():
    first = make_snapshot()

    second = make_snapshot()

    assert first == second


def test_snapshot_changes_when_decision_changes():
    first = make_snapshot()

    second = make_snapshot(
        decision=ETARiskDecision.BEHIND_PLAN_CUSTOMER_SAFE,
        schedule_risk=ETARiskLevel.LATE,
        action_required=True,
        summary=(
            "Production is behind plan but the "
            "required date remains safe"
        ),
        customer_date_safe=True,
        schedule_is_safe=False,
    )

    assert first != second


def test_snapshot_from_risk_summary_preserves_all_fields():
    summary = make_summary(
        schedule_risk=ETARiskLevel.AT_RISK,
        required_date_risk=RequiredDateRiskLevel.AT_RISK,
        decision=ETARiskDecision.CUSTOMER_DATE_AT_RISK,
        action_required=True,
        summary="The required date is at risk",
        customer_date_safe=True,
        schedule_is_safe=False,
    )

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
        27,
        16,
        0,
    )

    required_date = datetime(
        2026,
        8,
        28,
        16,
        0,
    )

    snapshot = ETAOperationalSnapshot.from_risk_summary(
        planned_eta=planned_eta,
        current_eta=current_eta,
        required_date=required_date,
        summary=summary,
    )

    assert snapshot.planned_eta == planned_eta
    assert snapshot.current_eta == current_eta
    assert snapshot.required_date == required_date

    assert snapshot.schedule_risk == (
        ETARiskLevel.AT_RISK
    )

    assert snapshot.required_date_risk == (
        RequiredDateRiskLevel.AT_RISK
    )

    assert snapshot.decision == (
        ETARiskDecision.CUSTOMER_DATE_AT_RISK
    )

    assert snapshot.action_required is True

    assert snapshot.summary == (
        "The required date is at risk"
    )


def test_snapshot_properties_are_consistent():
    snapshot = make_snapshot(
        schedule_risk=ETARiskLevel.AT_RISK,
        required_date_risk=RequiredDateRiskLevel.AT_RISK,
        decision=ETARiskDecision.CUSTOMER_DATE_AT_RISK,
        action_required=True,
        customer_date_safe=True,
        schedule_is_safe=False,
    )

    assert snapshot.requires_action == (
        snapshot.action_required
    )

    assert snapshot.is_customer_at_risk is True

    assert snapshot.is_customer_late is False

    assert snapshot.is_customer_safe is True

    assert snapshot.is_on_track is False