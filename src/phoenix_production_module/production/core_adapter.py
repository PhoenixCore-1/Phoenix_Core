import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from .performance_analytics import (
    ProductionObservation,
    ProductionPerformance,
    calculate_performance,
)

QUANTITY_TYPES = {
    "ACCEPTED",
    "REJECTED",
    "REWORK",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record_quantity(
    db: sqlite3.Connection,
    *,
    organisation_id: str,
    production_order_id: int,
    stage_id: Optional[int],
    quantity_type: str,
    quantity: Decimal,
    uom_code: str,
    recorded_by: str,
    reason_code: Optional[str] = None,
    notes: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> int:
    """
    Persist one immutable Production quantity ledger entry.

    This adapter owns persistence only. Production business rules remain
    in the standalone Production domain layer.
    """

    quantity_type = quantity_type.upper().strip()

    if quantity_type not in QUANTITY_TYPES:
        raise ValueError(
            f"Unsupported quantity_type: {quantity_type}"
        )

    quantity = Decimal(str(quantity))

    if quantity < 0:
        raise ValueError("Quantity cannot be negative")

    if not uom_code or not uom_code.strip():
        raise ValueError("uom_code is required")

    # Confirm the order belongs to the supplied organisation.
    # Confirm the order belongs to the supplied organisation.
    # Confirm the order belongs to the supplied organisation.
    order = db.execute(
        """
        SELECT production_order_id
        FROM production_orders
        WHERE production_order_id=?
          AND organisation_id=?
        """,
        (production_order_id, organisation_id),
    ).fetchone()

    if not order:
        raise ValueError("Production order not found")

    # If a stage is supplied, it must belong to the same order.
    if stage_id is not None:
        stage = db.execute(
            """
            SELECT stage_id
            FROM production_stages
            WHERE stage_id=?
              AND production_order_id=?
            """,
            (stage_id, production_order_id),
        ).fetchone()

        if not stage:
            raise ValueError("Production stage not found")

    # Idempotent retry protection.
    if idempotency_key:
        existing = db.execute(
            """
            SELECT quantity_ledger_id
            FROM production_quantity_ledger
            WHERE organisation_id=?
              AND idempotency_key=?
            """,
            (organisation_id, idempotency_key),
        ).fetchone()

        if existing:
            return int(existing[0])

    cur = db.execute(
        """
        INSERT INTO production_quantity_ledger(
            organisation_id,
            production_order_id,
            stage_id,
            quantity_type,
            quantity,
            uom_code,
            reason_code,
            notes,
            recorded_by,
            recorded_at,
            idempotency_key
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            organisation_id,
            production_order_id,
            stage_id,
            quantity_type,
            str(quantity),
            uom_code.strip(),
            reason_code,
            notes,
            recorded_by,
            utc_now(),
            idempotency_key,
        ),
    )

    return int(cur.lastrowid)




def _parse_core_datetime(value) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed


def load_performance_observations(
    db,
    *,
    organisation_id: str,
) -> list[ProductionObservation]:
    """
    Build Production Performance observations from the
    authoritative Phoenix Core production schema.

    Planned quantity:
        production_orders.quantity_ordered

    Actual quantity:
        accepted + rejected + rework quantity ledger entries

    Production timing:
        stage start/finish timestamps.
    """

    orders = db.execute(
        """
        SELECT
            production_order_id,
            organisation_id,
            quantity_ordered,
            status
        FROM production_orders
        WHERE organisation_id=?
        ORDER BY production_order_id
        """,
        (str(organisation_id),),
    ).fetchall()

    observations = []

    for order in orders:
        order_id = int(order[0])
        org_id = str(order[1])
        planned_quantity = Decimal(str(order[2]))

        quantity_row = db.execute(
            """
            SELECT COALESCE(SUM(quantity), 0)
            FROM production_quantity_ledger
            WHERE organisation_id=?
              AND production_order_id=?
              AND quantity_type IN (
                  'ACCEPTED',
                  'REJECTED',
                  'REWORK'
              )
            """,
            (org_id, order_id),
        ).fetchone()

        actual_quantity = Decimal(
            str(quantity_row[0] or "0")
        )

        timing = db.execute(
            """
            SELECT
                MIN(start_datetime),
                MAX(finish_datetime)
            FROM production_stages
            WHERE production_order_id=?
            """,
            (order_id,),
        ).fetchone()

        started_at = _parse_core_datetime(timing[0])
        completed_at = _parse_core_datetime(timing[1])

        observations.append(
            ProductionObservation(
                order_id=str(order_id),
                organisation_id=org_id,
                planned_quantity=planned_quantity,
                actual_quantity=actual_quantity,
                started_at=started_at,
                completed_at=completed_at,
            )
        )

    return observations


def calculate_core_performance(
    db,
    *,
    organisation_id: str,
    start_at: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
) -> ProductionPerformance:
    observations = load_performance_observations(
        db,
        organisation_id=organisation_id,
    )

    return calculate_performance(
        observations,
        organisation_id=str(organisation_id),
        start_at=start_at,
        end_at=end_at,
    )
