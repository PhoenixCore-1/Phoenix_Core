"""
Phoenix Production 360 — Production Performance Analytics.

WP5 Slice 1
-----------

Pure analytics over production-order observations.

This module intentionally contains no persistence, HTTP, authentication,
or Core-DB access. Those concerns remain at the integration/service boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable, Optional


@dataclass(frozen=True)
class ProductionObservation:
    """Normalized production observation used by the analytics layer."""

    order_id: str
    organisation_id: str
    planned_quantity: Decimal
    actual_quantity: Decimal
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


@dataclass(frozen=True)
class ProductionPerformance:
    """Aggregated production-performance metrics."""

    organisation_id: str
    order_count: int
    open_order_count: int
    completed_order_count: int
    planned_quantity: Decimal
    actual_quantity: Decimal
    completion_ratio: Decimal
    total_production_seconds: Decimal
    average_production_seconds: Optional[Decimal]
    average_actual_rate: Optional[Decimal]


def _validate_observation(observation: ProductionObservation) -> None:
    if not observation.order_id:
        raise ValueError("order_id is required")

    if not observation.organisation_id:
        raise ValueError("organisation_id is required")

    if observation.planned_quantity < 0:
        raise ValueError("planned_quantity cannot be negative")

    if observation.actual_quantity < 0:
        raise ValueError("actual_quantity cannot be negative")

    if (
        observation.started_at is not None
        and observation.completed_at is not None
        and observation.completed_at < observation.started_at
    ):
        raise ValueError("completed_at cannot be earlier than started_at")


def _duration_seconds(
    started_at: Optional[datetime],
    completed_at: Optional[datetime],
) -> Optional[Decimal]:
    if started_at is None or completed_at is None:
        return None

    return Decimal(str((completed_at - started_at).total_seconds()))


def calculate_performance(
    observations: Iterable[ProductionObservation],
    *,
    organisation_id: Optional[str] = None,
    start_at: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
) -> ProductionPerformance:
    """
    Calculate production-performance metrics for one organisation.

    Time-window semantics:
      - start_at is inclusive
      - end_at is exclusive

    An observation is included when its production activity intersects the
    requested window. Orders without timestamps remain eligible when no
    time window is requested.
    """

    rows = list(observations)

    for observation in rows:
        _validate_observation(observation)

    if start_at is not None and end_at is not None and end_at < start_at:
        raise ValueError("end_at cannot be earlier than start_at")

    if organisation_id is None:
        organisation_ids = {row.organisation_id for row in rows}

        if len(organisation_ids) != 1:
            raise ValueError(
                "organisation_id is required when observations contain "
                "multiple organisations"
            )

        organisation_id = next(iter(organisation_ids))

    # Explicit tenant boundary.
    rows = [
        row
        for row in rows
        if row.organisation_id == organisation_id
    ]

    if start_at is not None or end_at is not None:
        def intersects(row: ProductionObservation) -> bool:
            activity_start = row.started_at or row.completed_at
            activity_end = row.completed_at or row.started_at

            if activity_start is None and activity_end is None:
                return False

            if start_at is not None and activity_end is not None:
                if activity_end < start_at:
                    return False

            if end_at is not None and activity_start is not None:
                if activity_start >= end_at:
                    return False

            return True

        rows = [row for row in rows if intersects(row)]

    completed = [
        row
        for row in rows
        if row.completed_at is not None
    ]

    planned_quantity = sum(
        (row.planned_quantity for row in rows),
        Decimal("0"),
    )

    actual_quantity = sum(
        (row.actual_quantity for row in rows),
        Decimal("0"),
    )

    durations = [
        duration
        for row in completed
        if (duration := _duration_seconds(
            row.started_at,
            row.completed_at,
        )) is not None
    ]

    total_seconds = sum(
        durations,
        Decimal("0"),
    )

    completion_ratio = (
        actual_quantity / planned_quantity
        if planned_quantity > 0
        else Decimal("0")
    )

    average_duration = (
        total_seconds / Decimal(len(durations))
        if durations
        else None
    )

    rates = [
        row.actual_quantity / duration
        for row, duration in (
            (row, _duration_seconds(row.started_at, row.completed_at))
            for row in completed
        )
        if duration is not None and duration > 0
    ]

    average_rate = (
        sum(rates, Decimal("0")) / Decimal(len(rates))
        if rates
        else None
    )

    return ProductionPerformance(
        organisation_id=organisation_id,
        order_count=len(rows),
        open_order_count=len(rows) - len(completed),
        completed_order_count=len(completed),
        planned_quantity=planned_quantity,
        actual_quantity=actual_quantity,
        completion_ratio=completion_ratio,
        total_production_seconds=total_seconds,
        average_production_seconds=average_duration,
        average_actual_rate=average_rate,
    )
