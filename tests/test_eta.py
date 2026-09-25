from datetime import datetime
from decimal import Decimal

import pytest

from phoenix_production_module.production.models import (
    ETAStatus,
    ManufacturingOrder,
    MaterialRequirement,
)
from phoenix_production_module.production.service import (
    ProductionService,
)


def make_order(qty="1000"):
    return ManufacturingOrder(
        tenant_id="TEST_TENANT",
        site_id="TEST_SITE",
        product_id="TEST_PRODUCT",
        planned_quantity=Decimal(qty),
        required_date=datetime(2026, 8, 31),
    )


# ---------------------------------------------------------------------------
# Phoenix Production Module 1.3.10
# ETA Foundation Tests
# ---------------------------------------------------------------------------


def test_material_expected_arrival_uses_supplier_lead_time():
    material = MaterialRequirement(
        material_id="RAW-001",
        required_quantity=Decimal("1000"),
        supplier_lead_time_days=Decimal("10"),
        order_date=datetime(2026, 8, 10),
    )

    assert material.expected_arrival == datetime(
        2026,
        8,
        20,
    )

    assert material.is_ordered is True
    assert material.is_received is False


def test_material_ready_date_uses_latest_material_arrival():
    service = ProductionService()
    order = make_order()

    material_1 = MaterialRequirement(
        material_id="RAW-001",
        required_quantity=Decimal("1000"),
        supplier_lead_time_days=Decimal("5"),
        order_date=datetime(2026, 8, 10),
    )

    material_2 = MaterialRequirement(
        material_id="RAW-002",
        required_quantity=Decimal("500"),
        supplier_lead_time_days=Decimal("10"),
        order_date=datetime(2026, 8, 10),
    )

    service.add_material_requirement(
        order,
        material_1,
    )

    service.add_material_requirement(
        order,
        material_2,
    )

    ready_date = (
        service.calculate_material_ready_date(
            order
        )
    )

    assert ready_date == datetime(
        2026,
        8,
        20,
    )


def test_actual_material_arrival_can_make_material_ready_earlier():
    service = ProductionService()
    order = make_order()

    material_1 = MaterialRequirement(
        material_id="RAW-001",
        required_quantity=Decimal("1000"),
        supplier_lead_time_days=Decimal("10"),
        order_date=datetime(2026, 8, 10),
    )

    material_2 = MaterialRequirement(
        material_id="RAW-002",
        required_quantity=Decimal("500"),
        supplier_lead_time_days=Decimal("10"),
        order_date=datetime(2026, 8, 10),
        actual_arrival=datetime(
            2026,
            8,
            18,
        ),
    )

    service.add_material_requirement(
        order,
        material_1,
    )

    service.add_material_requirement(
        order,
        material_2,
    )

    ready_date = (
        service.calculate_material_ready_date(
            order
        )
    )

    assert ready_date == datetime(
        2026,
        8,
        20,
    )


def test_material_without_expected_or_actual_arrival_prevents_readiness():
    service = ProductionService()
    order = make_order()

    material = MaterialRequirement(
        material_id="RAW-001",
        required_quantity=Decimal("1000"),
        supplier_lead_time_days=Decimal("10"),
    )

    service.add_material_requirement(
        order,
        material,
    )

    ready_date = (
        service.calculate_material_ready_date(
            order
        )
    )

    assert ready_date is None


def test_planned_production_start_uses_material_ready_date():
    service = ProductionService()
    order = make_order()

    material = MaterialRequirement(
        material_id="RAW-001",
        required_quantity=Decimal("1000"),
        supplier_lead_time_days=Decimal("10"),
        order_date=datetime(2026, 8, 10),
    )

    service.add_material_requirement(
        order,
        material,
    )

    planned_start = (
        service.calculate_planned_production_start(
            order
        )
    )

    assert planned_start == datetime(
        2026,
        8,
        20,
    )

    assert (
        order.eta.planned_production_start
        == datetime(2026, 8, 20)
    )


def test_planned_eta_uses_production_duration():
    service = ProductionService()
    order = make_order()

    material = MaterialRequirement(
        material_id="RAW-001",
        required_quantity=Decimal("1000"),
        supplier_lead_time_days=Decimal("10"),
        order_date=datetime(2026, 8, 10),
    )

    service.add_material_requirement(
        order,
        material,
    )

    service.calculate_planned_production_start(
        order
    )

    planned_eta = (
        service.calculate_planned_eta_from_duration(
            order,
            production_duration_hours=Decimal("48"),
        )
    )

    assert planned_eta == datetime(
        2026,
        8,
        22,
    )

    assert order.eta.planned_eta == datetime(
        2026,
        8,
        22,
    )


def test_live_eta_uses_remaining_production_hours():
    service = ProductionService()
    order = make_order()

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

    calculated_at = datetime(
        2026,
        8,
        21,
        8,
        0,
    )

    snapshot = (
        service.calculate_live_eta_from_remaining_work(
            order,
            remaining_production_hours=Decimal("24"),
            calculated_at=calculated_at,
        )
    )

    assert snapshot is not None

    assert snapshot.current_eta == datetime(
        2026,
        8,
        22,
        8,
        0,
    )

    assert (
        order.eta.current_eta
        == datetime(
            2026,
            8,
            22,
            8,
            0,
        )
    )


def test_live_eta_uses_remaining_quantity_and_actual_rate():
    service = ProductionService()
    order = make_order()

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

    calculated_at = datetime(
        2026,
        8,
        21,
        8,
        0,
    )

    snapshot = (
        service.calculate_live_eta_from_rate(
            order,
            remaining_quantity=Decimal("400"),
            production_rate_per_hour=Decimal("100"),
            calculated_at=calculated_at,
        )
    )

    assert snapshot is not None

    assert snapshot.current_eta == datetime(
        2026,
        8,
        21,
        12,
        0,
    )


def test_faster_production_moves_live_eta_earlier():
    service = ProductionService()
    order = make_order()

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

    calculated_at = datetime(
        2026,
        8,
        21,
        8,
        0,
    )

    slower = (
        service.calculate_live_eta_from_rate(
            order,
            remaining_quantity=Decimal("600"),
            production_rate_per_hour=Decimal("100"),
            calculated_at=calculated_at,
        )
    )

    faster = (
        service.calculate_live_eta_from_rate(
            order,
            remaining_quantity=Decimal("600"),
            production_rate_per_hour=Decimal("200"),
            calculated_at=calculated_at,
        )
    )

    assert slower is not None
    assert faster is not None

    assert (
        faster.current_eta
        < slower.current_eta
    )


def test_slower_production_moves_live_eta_later():
    service = ProductionService()
    order = make_order()

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

    calculated_at = datetime(
        2026,
        8,
        21,
        8,
        0,
    )

    faster = (
        service.calculate_live_eta_from_rate(
            order,
            remaining_quantity=Decimal("600"),
            production_rate_per_hour=Decimal("200"),
            calculated_at=calculated_at,
        )
    )

    slower = (
        service.calculate_live_eta_from_rate(
            order,
            remaining_quantity=Decimal("600"),
            production_rate_per_hour=Decimal("100"),
            calculated_at=calculated_at,
        )
    )

    assert faster is not None
    assert slower is not None

    assert (
        slower.current_eta
        > faster.current_eta
    )


def test_zero_production_rate_is_rejected():
    service = ProductionService()
    order = make_order()

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

    with pytest.raises(ValueError):
        service.calculate_live_eta_from_rate(
            order,
            remaining_quantity=Decimal("100"),
            production_rate_per_hour=Decimal("0"),
            calculated_at=datetime(
                2026,
                8,
                21,
                8,
                0,
            ),
        )


def test_negative_remaining_quantity_is_rejected():
    service = ProductionService()
    order = make_order()

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

    with pytest.raises(ValueError):
        service.calculate_live_eta_from_rate(
            order,
            remaining_quantity=Decimal("-1"),
            production_rate_per_hour=Decimal("100"),
            calculated_at=datetime(
                2026,
                8,
                21,
                8,
                0,
            ),
        )


def test_material_wait_status():
    service = ProductionService()
    order = make_order()

    service.mark_material_wait(
        order
    )

    assert (
        service.get_eta_status(order)
        == ETAStatus.MATERIAL_WAIT
    )


def test_completed_order_sets_eta_to_completed():
    service = ProductionService()
    order = make_order()

    completed_at = datetime(
        2026,
        8,
        25,
        16,
        0,
    )

    service.mark_eta_completed(
        order,
        completed_at,
    )

    assert (
        order.eta.actual_completion
        == completed_at
    )

    assert (
        order.eta.current_eta
        == completed_at
    )

    assert (
        service.get_eta_status(order)
        == ETAStatus.COMPLETED
    )


def test_live_eta_can_be_late_against_required_date():
    service = ProductionService()
    order = make_order()

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
        service.calculate_live_eta_from_remaining_work(
            order,
            remaining_production_hours=Decimal("72"),
            calculated_at=datetime(
                2026,
                8,
                30,
                8,
                0,
            ),
        )
    )

    assert snapshot is not None

    assert (
        snapshot.status
        == ETAStatus.LATE
    )

    assert snapshot.is_late is True