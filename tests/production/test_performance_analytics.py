from datetime import datetime, timezone
from decimal import Decimal

import pytest

from phoenix_production_module.production.performance_analytics import (
    ProductionObservation,
    calculate_performance,
)


def dt(hour: int) -> datetime:
    return datetime(2026, 1, 1, hour, 0, tzinfo=timezone.utc)


def observation(
    order_id: str,
    organisation_id: str,
    planned: str,
    actual: str,
    started: int | None,
    completed: int | None,
) -> ProductionObservation:
    return ProductionObservation(
        order_id=order_id,
        organisation_id=organisation_id,
        planned_quantity=Decimal(planned),
        actual_quantity=Decimal(actual),
        started_at=dt(started) if started is not None else None,
        completed_at=dt(completed) if completed is not None else None,
    )


def test_completed_and_open_orders_are_aggregated():
    result = calculate_performance(
        [
            observation("o1", "org-a", "100", "80", 8, 10),
            observation("o2", "org-a", "50", "0", 11, None),
        ],
        organisation_id="org-a",
    )

    assert result.order_count == 2
    assert result.completed_order_count == 1
    assert result.open_order_count == 1
    assert result.planned_quantity == Decimal("150")
    assert result.actual_quantity == Decimal("80")


def test_completion_ratio_is_actual_over_planned():
    result = calculate_performance(
        [
            observation("o1", "org-a", "100", "75", 8, 10),
        ],
        organisation_id="org-a",
    )

    assert result.completion_ratio == Decimal("0.75")


def test_duration_and_average_rate_are_calculated():
    result = calculate_performance(
        [
            observation("o1", "org-a", "100", "80", 8, 10),
            observation("o2", "org-a", "100", "100", 8, 12),
        ],
        organisation_id="org-a",
    )

    assert result.total_production_seconds == Decimal("21600")
    assert result.average_production_seconds == Decimal("10800")

    expected_rate = (
        Decimal("40") / Decimal("3600")
        + Decimal("100") / Decimal("14400")
    ) / Decimal("2")

    assert result.average_actual_rate == expected_rate


def test_organisation_isolation():
    result = calculate_performance(
        [
            observation("a1", "org-a", "100", "50", 8, 10),
            observation("b1", "org-b", "900", "900", 8, 9),
        ],
        organisation_id="org-a",
    )

    assert result.order_count == 1
    assert result.planned_quantity == Decimal("100")
    assert result.actual_quantity == Decimal("50")


def test_multiple_organisations_require_explicit_scope():
    with pytest.raises(ValueError, match="organisation_id is required"):
        calculate_performance(
            [
                observation("a1", "org-a", "100", "50", 8, 10),
                observation("b1", "org-b", "100", "50", 8, 10),
            ]
        )


def test_time_window_is_start_inclusive_end_exclusive():
    result = calculate_performance(
        [
            observation("o1", "org-a", "100", "50", 8, 10),
            observation("o2", "org-a", "100", "60", 10, 12),
            observation("o3", "org-a", "100", "70", 12, 14),
        ],
        organisation_id="org-a",
        start_at=dt(10),
        end_at=dt(12),
    )

    assert result.order_count == 2
    assert result.actual_quantity == Decimal("110")


def test_negative_quantity_is_rejected():
    with pytest.raises(ValueError, match="planned_quantity"):
        calculate_performance(
            [
                observation("o1", "org-a", "-1", "0", 8, None),
            ],
            organisation_id="org-a",
        )


def test_invalid_duration_is_rejected():
    with pytest.raises(ValueError, match="completed_at"):
        calculate_performance(
            [
                ProductionObservation(
                    order_id="o1",
                    organisation_id="org-a",
                    planned_quantity=Decimal("100"),
                    actual_quantity=Decimal("50"),
                    started_at=dt(12),
                    completed_at=dt(10),
                )
            ],
            organisation_id="org-a",
        )


def test_zero_planned_quantity_has_zero_completion_ratio():
    result = calculate_performance(
        [
            observation("o1", "org-a", "0", "0", 8, 9),
        ],
        organisation_id="org-a",
    )

    assert result.completion_ratio == Decimal("0")

