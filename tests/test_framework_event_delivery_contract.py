from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_framework.context import FrameworkContext
from phoenix_framework.contracts.delivery import EventDelivery
from phoenix_framework.contracts.event import ModuleEvent


def make_context():
    return FrameworkContext(
        request_id="req-delivery-001",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        session_id=uuid4(),
        permissions=frozenset({"sales.quote.read"}),
        entitlements=frozenset({"sales"}),
    )


def make_event():
    return ModuleEvent.create(
        event_id="event-001",
        event_type="sales.quote.created",
        publisher_module="sales",
        context=make_context(),
        payload={"quote_id": "Q-001"},
    )


def make_delivery():
    return EventDelivery(
        event_id="event-001",
        event_type="sales.quote.created",
        publisher_module="sales",
        occurred_at=datetime.now(timezone.utc),
        subscriber_module="crm",
        request_id="req-delivery-001",
        organisation_id=uuid4(),
        identity_id=uuid4(),
        session_id=uuid4(),
        permissions=frozenset({"sales.quote.read"}),
        entitlements=frozenset({"sales"}),
    )


def test_event_delivery_is_immutable():
    delivery = make_delivery()

    with pytest.raises(AttributeError):
        delivery.event_id = "changed"


def test_event_delivery_preserves_event_metadata():
    occurred_at = datetime.now(timezone.utc)

    delivery = EventDelivery(
        event_id="event-001",
        event_type="sales.quote.created",
        publisher_module="sales",
        occurred_at=occurred_at,
        subscriber_module="crm",
        request_id="req-delivery-001",
        organisation_id=uuid4(),
    )

    assert delivery.event_id == "event-001"
    assert delivery.event_type == "sales.quote.created"
    assert delivery.publisher_module == "sales"
    assert delivery.occurred_at == occurred_at


def test_event_delivery_preserves_event_context():
    organisation_id = uuid4()
    identity_id = uuid4()
    session_id = uuid4()

    delivery = EventDelivery(
        event_id="event-001",
        event_type="sales.quote.created",
        publisher_module="sales",
        occurred_at=datetime.now(timezone.utc),
        subscriber_module="crm",
        request_id="req-delivery-001",
        organisation_id=organisation_id,
        identity_id=identity_id,
        session_id=session_id,
        permissions=frozenset({"sales.quote.read"}),
        entitlements=frozenset({"sales"}),
    )

    assert delivery.request_id == "req-delivery-001"
    assert delivery.organisation_id == organisation_id
    assert delivery.identity_id == identity_id
    assert delivery.session_id == session_id
    assert delivery.permissions == frozenset({"sales.quote.read"})
    assert delivery.entitlements == frozenset({"sales"})


def test_delivery_key_is_stable_for_same_event_and_subscriber():
    organisation_id = uuid4()
    occurred_at = datetime.now(timezone.utc)

    first = EventDelivery(
        event_id="event-001",
        event_type="sales.quote.created",
        publisher_module="sales",
        occurred_at=occurred_at,
        subscriber_module="CRM",
        request_id="req-001",
        organisation_id=organisation_id,
    )

    second = EventDelivery(
        event_id="event-001",
        event_type="sales.quote.created",
        publisher_module="sales",
        occurred_at=occurred_at,
        subscriber_module="crm",
        request_id="req-002",
        organisation_id=organisation_id,
    )

    assert first.delivery_key == second.delivery_key
    assert first.delivery_key == "event:event-001:subscriber:crm"


def test_different_subscribers_have_different_delivery_keys():
    organisation_id = uuid4()
    occurred_at = datetime.now(timezone.utc)

    crm_delivery = EventDelivery(
        event_id="event-001",
        event_type="sales.quote.created",
        publisher_module="sales",
        occurred_at=occurred_at,
        subscriber_module="crm",
        request_id="req-001",
        organisation_id=organisation_id,
    )

    inventory_delivery = EventDelivery(
        event_id="event-001",
        event_type="sales.quote.created",
        publisher_module="sales",
        occurred_at=occurred_at,
        subscriber_module="inventory",
        request_id="req-001",
        organisation_id=organisation_id,
    )

    assert crm_delivery.delivery_key != inventory_delivery.delivery_key


def test_different_events_have_different_delivery_keys():
    organisation_id = uuid4()
    occurred_at = datetime.now(timezone.utc)

    first = EventDelivery(
        event_id="event-001",
        event_type="sales.quote.created",
        publisher_module="sales",
        occurred_at=occurred_at,
        subscriber_module="crm",
        request_id="req-001",
        organisation_id=organisation_id,
    )

    second = EventDelivery(
        event_id="event-002",
        event_type="sales.quote.created",
        publisher_module="sales",
        occurred_at=occurred_at,
        subscriber_module="crm",
        request_id="req-001",
        organisation_id=organisation_id,
    )

    assert first.delivery_key != second.delivery_key


def test_delivery_requires_event_id():
    with pytest.raises(ValueError, match="event_id is required"):
        EventDelivery(
            event_id="",
            event_type="sales.quote.created",
            publisher_module="sales",
            occurred_at=datetime.now(timezone.utc),
            subscriber_module="crm",
            request_id="req-001",
            organisation_id=uuid4(),
        )


def test_delivery_requires_event_type():
    with pytest.raises(ValueError, match="event_type is required"):
        EventDelivery(
            event_id="event-001",
            event_type="",
            publisher_module="sales",
            occurred_at=datetime.now(timezone.utc),
            subscriber_module="crm",
            request_id="req-001",
            organisation_id=uuid4(),
        )


def test_delivery_requires_publisher():
    with pytest.raises(ValueError, match="publisher_module is required"):
        EventDelivery(
            event_id="event-001",
            event_type="sales.quote.created",
            publisher_module="",
            occurred_at=datetime.now(timezone.utc),
            subscriber_module="crm",
            request_id="req-001",
            organisation_id=uuid4(),
        )


def test_delivery_requires_timezone_aware_timestamp():
    with pytest.raises(
        ValueError,
        match="occurred_at must be timezone-aware",
    ):
        EventDelivery(
            event_id="event-001",
            event_type="sales.quote.created",
            publisher_module="sales",
            occurred_at=datetime.now(),
            subscriber_module="crm",
            request_id="req-001",
            organisation_id=uuid4(),
        )


def test_delivery_requires_subscriber():
    with pytest.raises(ValueError, match="subscriber_module is required"):
        EventDelivery(
            event_id="event-001",
            event_type="sales.quote.created",
            publisher_module="sales",
            occurred_at=datetime.now(timezone.utc),
            subscriber_module="",
            request_id="req-001",
            organisation_id=uuid4(),
        )


def test_delivery_requires_request_id():
    with pytest.raises(ValueError, match="request_id is required"):
        EventDelivery(
            event_id="event-001",
            event_type="sales.quote.created",
            publisher_module="sales",
            occurred_at=datetime.now(timezone.utc),
            subscriber_module="crm",
            request_id="",
            organisation_id=uuid4(),
        )


def test_delivery_requires_organisation():
    with pytest.raises(ValueError, match="organisation_id is required"):
        EventDelivery(
            event_id="event-001",
            event_type="sales.quote.created",
            publisher_module="sales",
            occurred_at=datetime.now(timezone.utc),
            subscriber_module="crm",
            request_id="req-001",
            organisation_id=None,
        )


def test_from_event_preserves_delivery_context_and_event_metadata():
    event = make_event()

    delivery = EventDelivery.from_event(
        event,
        "crm",
    )

    assert delivery.event_id == event.event_id
    assert delivery.event_type == event.event_type
    assert delivery.publisher_module == event.publisher_module
    assert delivery.occurred_at == event.occurred_at
    assert delivery.subscriber_module == "crm"
    assert delivery.request_id == event.request_id
    assert delivery.organisation_id == event.organisation_id
    assert delivery.identity_id == event.identity_id
    assert delivery.session_id == event.session_id
    assert delivery.permissions == event.context.permissions
    assert delivery.entitlements == event.context.entitlements


def test_from_event_generates_expected_delivery_key():
    delivery = EventDelivery.from_event(
        make_event(),
        "CRM",
    )

    assert delivery.delivery_key == "event:event-001:subscriber:crm"
