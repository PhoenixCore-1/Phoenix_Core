from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_framework.context import FrameworkContext
from phoenix_framework.contracts.command import ModuleCommand
from phoenix_framework.contracts.event import ModuleEvent
from phoenix_framework.contracts.query import ModuleQuery


def make_context():
    return FrameworkContext(
        request_id="req-001",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        session_id=uuid4(),
        permissions=frozenset(),
        entitlements=frozenset(),
    )


def test_command_contains_expected_fields():
    command = ModuleCommand(
        request_id="req-001",
        source_module="sales",
        target_module="inventory",
        name="stock.reserve",
        context=make_context(),
        payload={"item_id": "123", "quantity": 10},
    )

    assert command.request_id == "req-001"
    assert command.source_module == "sales"
    assert command.target_module == "inventory"
    assert command.name == "stock.reserve"
    assert command.payload["quantity"] == 10


def test_command_is_immutable():
    command = ModuleCommand(
        request_id="req-001",
        source_module="sales",
        target_module="inventory",
        name="stock.reserve",
        context=make_context(),
    )

    with pytest.raises(FrozenInstanceError):
        command.name = "stock.release"


@pytest.mark.parametrize(
    "field",
    [
        "request_id",
        "source_module",
        "target_module",
        "name",
    ],
)
def test_command_rejects_missing_required_fields(field):
    values = {
        "request_id": "req-001",
        "source_module": "sales",
        "target_module": "inventory",
        "name": "stock.reserve",
        "context": make_context(),
    }

    values[field] = ""

    with pytest.raises(ValueError):
        ModuleCommand(**values)


def test_command_rejects_same_source_and_target():
    with pytest.raises(ValueError):
        ModuleCommand(
            request_id="req-001",
            source_module="sales",
            target_module="sales",
            name="something",
            context=make_context(),
        )


def test_query_contains_expected_fields():
    query = ModuleQuery(
        request_id="req-002",
        source_module="sales",
        target_module="crm",
        name="customer.lookup",
        context=make_context(),
        parameters={"customer_id": "123"},
    )

    assert query.request_id == "req-002"
    assert query.source_module == "sales"
    assert query.target_module == "crm"
    assert query.name == "customer.lookup"
    assert query.parameters["customer_id"] == "123"


def test_query_is_immutable():
    query = ModuleQuery(
        request_id="req-002",
        source_module="sales",
        target_module="crm",
        name="customer.lookup",
        context=make_context(),
    )

    with pytest.raises(FrozenInstanceError):
        query.name = "customer.delete"


def test_query_rejects_same_source_and_target():
    with pytest.raises(ValueError):
        ModuleQuery(
            request_id="req-002",
            source_module="crm",
            target_module="crm",
            name="customer.lookup",
            context=make_context(),
        )


def test_event_contains_expected_fields():
    occurred_at = datetime.now(timezone.utc)

    event = ModuleEvent(
        event_id=str(uuid4()),
        event_type="sales.quote.created",
        publisher_module="sales",
        occurred_at=occurred_at,
        context=make_context(),
        payload={"quote_id": "Q-001"},
    )

    assert event.event_type == "sales.quote.created"
    assert event.publisher_module == "sales"
    assert event.occurred_at == occurred_at
    assert event.payload["quote_id"] == "Q-001"
    assert event.request_id == "req-001"
    assert event.organisation_id is not None
    assert event.identity_id is not None
    assert event.session_id is not None


def test_event_requires_timezone_aware_timestamp():
    with pytest.raises(ValueError):
        ModuleEvent(
            event_id=str(uuid4()),
            event_type="sales.quote.created",
            publisher_module="sales",
            occurred_at=datetime.now(),
            context=make_context(),
        )


def test_event_create_generates_timezone_aware_timestamp():
    event = ModuleEvent.create(
        event_id=str(uuid4()),
        event_type="sales.quote.created",
        publisher_module="sales",
        context=make_context(),
        payload={"quote_id": "Q-001"},
    )

    assert event.occurred_at.tzinfo is not None
    assert event.payload["quote_id"] == "Q-001"


def test_event_is_immutable():
    event = ModuleEvent.create(
        event_id=str(uuid4()),
        event_type="sales.quote.created",
        publisher_module="sales",
        context=make_context(),
    )

    with pytest.raises(FrozenInstanceError):
        event.event_type = "sales.quote.updated"


@pytest.mark.parametrize(
    "field",
    [
        "event_id",
        "event_type",
        "publisher_module",
    ],
)
def test_event_rejects_missing_required_fields(field):
    values = {
        "event_id": str(uuid4()),
        "event_type": "sales.quote.created",
        "publisher_module": "sales",
        "occurred_at": datetime.now(timezone.utc),
        "context": make_context(),
    }

    values[field] = ""

    with pytest.raises(ValueError):
        ModuleEvent(**values)


def test_event_rejects_unauthenticated_context():
    context = FrameworkContext(
        request_id="req-unauthenticated",
        identity_id=None,
        organisation_id=uuid4(),
        session_id=None,
        permissions=frozenset(),
        entitlements=frozenset(),
    )

    with pytest.raises(PermissionError):
        ModuleEvent.create(
            event_id=str(uuid4()),
            event_type="sales.quote.created",
            publisher_module="sales",
            context=context,
        )


def test_event_rejects_unbound_context():
    context = FrameworkContext(
        request_id="req-no-tenant",
        identity_id=uuid4(),
        organisation_id=None,
        session_id=uuid4(),
        permissions=frozenset(),
        entitlements=frozenset(),
    )

    with pytest.raises(PermissionError):
        ModuleEvent.create(
            event_id=str(uuid4()),
            event_type="sales.quote.created",
            publisher_module="sales",
            context=context,
        )
