from uuid import uuid4

import pytest

from phoenix_framework.context import FrameworkContext
from phoenix_framework.contracts.event import ModuleEvent
from phoenix_framework.contracts.subscription import EventSubscription
from phoenix_framework.integration.events import EventBus


def make_context():
    return FrameworkContext(
        request_id="req-event-001",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        session_id=uuid4(),
        permissions=frozenset(),
        entitlements=frozenset(),
    )


def make_event():
    return ModuleEvent.create(
        event_id=str(uuid4()),
        event_type="sales.quote.created",
        publisher_module="sales",
        context=make_context(),
        payload={"quote_id": "Q-001"},
    )


def test_publish_delivers_event_to_subscriber():
    bus = EventBus()
    received = []

    bus.subscribe(
        EventSubscription(
            subscriber_module="crm",
            event_type="sales.quote.created",
            handler=lambda event: received.append(event),
        )
    )

    event = make_event()

    results = bus.publish(event)

    assert received == [event]
    assert results == [None]


def test_publish_supports_multiple_subscribers():
    bus = EventBus()
    received = []

    bus.subscribe(
        EventSubscription(
            subscriber_module="crm",
            event_type="sales.quote.created",
            handler=lambda event: received.append("crm"),
        )
    )

    bus.subscribe(
        EventSubscription(
            subscriber_module="inventory",
            event_type="sales.quote.created",
            handler=lambda event: received.append("inventory"),
        )
    )

    bus.publish(make_event())

    assert received == ["crm", "inventory"]


def test_duplicate_subscriber_is_rejected():
    bus = EventBus()

    subscription = EventSubscription(
        subscriber_module="crm",
        event_type="sales.quote.created",
        handler=lambda event: None,
    )

    bus.subscribe(subscription)

    with pytest.raises(
        ValueError,
        match="Subscriber already registered",
    ):
        bus.subscribe(subscription)


def test_different_event_types_can_have_same_subscriber():
    bus = EventBus()
    received = []

    bus.subscribe(
        EventSubscription(
            subscriber_module="crm",
            event_type="sales.quote.created",
            handler=lambda event: received.append("created"),
        )
    )

    bus.subscribe(
        EventSubscription(
            subscriber_module="crm",
            event_type="sales.quote.updated",
            handler=lambda event: received.append("updated"),
        )
    )

    event = ModuleEvent.create(
        event_id=str(uuid4()),
        event_type="sales.quote.updated",
        publisher_module="sales",
        context=make_context(),
    )

    bus.publish(event)

    assert received == ["updated"]


def test_unsubscribe_removes_subscriber():
    bus = EventBus()

    bus.subscribe(
        EventSubscription(
            subscriber_module="crm",
            event_type="sales.quote.created",
            handler=lambda event: None,
        )
    )

    assert bus.has_subscribers("sales.quote.created")

    bus.unsubscribe(
        "crm",
        "sales.quote.created",
    )

    assert not bus.has_subscribers("sales.quote.created")


def test_publish_unknown_event_has_no_subscribers():
    bus = EventBus()

    results = bus.publish(make_event())

    assert results == []


def test_subscriber_failure_does_not_stop_other_subscribers():
    bus = EventBus()
    received = []

    def failing_handler(event):
        raise RuntimeError("subscriber failed")

    bus.subscribe(
        EventSubscription(
            subscriber_module="crm",
            event_type="sales.quote.created",
            handler=failing_handler,
        )
    )

    bus.subscribe(
        EventSubscription(
            subscriber_module="inventory",
            event_type="sales.quote.created",
            handler=lambda event: received.append("inventory"),
        )
    )

    results = bus.publish(make_event())

    assert isinstance(results[0], RuntimeError)
    assert received == ["inventory"]


def test_subscribers_returns_copy():
    bus = EventBus()

    subscription = EventSubscription(
        subscriber_module="crm",
        event_type="sales.quote.created",
        handler=lambda event: None,
    )

    bus.subscribe(subscription)

    subscriptions = bus.subscribers("sales.quote.created")
    subscriptions.clear()

    assert bus.has_subscribers("sales.quote.created")


def test_clear_removes_all_subscriptions():
    bus = EventBus()

    bus.subscribe(
        EventSubscription(
            subscriber_module="crm",
            event_type="sales.quote.created",
            handler=lambda event: None,
        )
    )

    bus.clear()

    assert not bus.has_subscribers("sales.quote.created")


def test_deliver_targets_only_requested_subscriber():
    bus = EventBus()
    received = []

    bus.subscribe(
        EventSubscription(
            subscriber_module="crm",
            event_type="sales.quote.created",
            handler=lambda event: received.append("crm"),
        )
    )

    bus.subscribe(
        EventSubscription(
            subscriber_module="inventory",
            event_type="sales.quote.created",
            handler=lambda event: received.append("inventory"),
        )
    )

    event = make_event()

    result = bus.deliver(event, "CRM")

    assert result is None
    assert received == ["crm"]


def test_deliver_raises_when_subscriber_is_not_registered():
    bus = EventBus()

    with pytest.raises(
        ValueError,
        match="Subscriber is not registered",
    ):
        bus.deliver(make_event(), "crm")


def test_deliver_propagates_subscriber_failure():
    bus = EventBus()

    def failing_handler(event):
        raise RuntimeError("subscriber failed")

    bus.subscribe(
        EventSubscription(
            subscriber_module="crm",
            event_type="sales.quote.created",
            handler=failing_handler,
        )
    )

    with pytest.raises(
        RuntimeError,
        match="subscriber failed",
    ):
        bus.deliver(make_event(), "crm")


def test_deliver_requires_subscriber():
    bus = EventBus()

    with pytest.raises(
        ValueError,
        match="Subscriber module is required",
    ):
        bus.deliver(make_event(), "")
