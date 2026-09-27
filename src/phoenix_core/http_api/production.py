"""Phoenix Production HTTP API.

HTTP transport only. Production business rules remain in the
Production module and persistence remains authoritative in Core.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request

from phoenix_core.http_api.authorization import (
    require_entitlement,
    require_permission,
)
from phoenix_production_module.production.service import ProductionService
from phoenix_production_module.production.integration import (
    _load_domain_order,
    get_eta_operational_snapshot,
)


router = APIRouter(
    prefix="/api/v1/production",
    tags=["Production"],
)


def _db(request: Request):
    return request.app.state.core_api.db


def _organisation(context):
    return context.organisation_id


def _performance_data(result):
    return {
        "organisation_id": result.organisation_id,
        "order_count": result.order_count,
        "open_order_count": result.open_order_count,
        "completed_order_count": result.completed_order_count,
        "planned_quantity": str(result.planned_quantity),
        "actual_quantity": str(result.actual_quantity),
        "completion_ratio": str(result.completion_ratio),
        "total_production_seconds": str(
            result.total_production_seconds
        ),
        "average_production_seconds": (
            str(result.average_production_seconds)
            if result.average_production_seconds is not None
            else None
        ),
        "average_actual_rate": (
            str(result.average_actual_rate)
            if result.average_actual_rate is not None
            else None
        ),
    }


def _operational_orders(
    db,
    *,
    organisation_id,
    start_at: Optional[datetime],
    end_at: Optional[datetime],
):
    sql = """
        SELECT production_order_id
        FROM production_orders
        WHERE organisation_id=?
    """
    params = [str(organisation_id)]

    if start_at is not None:
        sql += " AND required_date >= ?"
        params.append(start_at)

    if end_at is not None:
        sql += " AND required_date <= ?"
        params.append(end_at)

    sql += " ORDER BY production_order_id"

    rows = db.execute(sql, tuple(params)).fetchall()

    orders = []

    for row in rows:
        production_order_id = int(row["production_order_id"])

        order = _load_domain_order(
            db,
            organisation_id=str(organisation_id),
            production_order_id=production_order_id,
        )

        eta = get_eta_operational_snapshot(
            db,
            organisation_id=str(organisation_id),
            production_order_id=production_order_id,
        )

        hold_row = db.execute(
            """
            SELECT COUNT(*) AS active_hold_count
            FROM production_holds
            WHERE organisation_id=?
              AND production_order_id=?
              AND resolved_at IS NULL
            """,
            (
                str(organisation_id),
                production_order_id,
            ),
        ).fetchone()

        orders.append(
            {
                "production_order_id": production_order_id,
                "status": order.state.value,
                "planned_quantity": str(order.planned_quantity),
                "required_date": (
                    order.required_date.isoformat()
                    if order.required_date is not None
                    else None
                ),
                "eta": eta,
                "active_hold_count": int(
                    hold_row["active_hold_count"]
                ),
            }
        )

    return orders


@router.get("/performance")
@require_entitlement("production")
@require_permission("production.view")
async def performance(
    request: Request,
    start_at: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
):
    context = request.state.core_context

    result = ProductionService().calculate_performance(
        _db(request),
        organisation_id=_organisation(context),
        start_at=start_at,
        end_at=end_at,
    )

    return {
        "data": _performance_data(result),
        "request_id": context.request_id,
    }


@router.get("/operational-snapshot")
@require_entitlement("production")
@require_permission("production.view")
async def operational_snapshot(
    request: Request,
    start_at: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
):
    context = request.state.core_context
    organisation_id = _organisation(context)
    db = _db(request)

    performance_result = ProductionService().calculate_performance(
        db,
        organisation_id=organisation_id,
        start_at=start_at,
        end_at=end_at,
    )

    orders = _operational_orders(
        db,
        organisation_id=organisation_id,
        start_at=start_at,
        end_at=end_at,
    )

    return {
        "data": {
            "organisation_id": organisation_id,
            "performance": _performance_data(performance_result),
            "orders": orders,
            "order_count": len(orders),
        },
        "request_id": context.request_id,
    }

