from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_framework.context import FrameworkContext
from phoenix_framework.contracts.event import ModuleEvent
from phoenix_framework.contracts.subscription import EventSubscription
from phoenix_framework.integration.event_executor import EventDeliveryExecutor
from phoenix_framework.integration.events import EventBus


def make_context():
    return FrameworkContext(
        request_id="req-executor-001",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        session_id=uuid4(),
        permissions=frozenset(
            {
                "sales.quote.read",
                "crm.quote.create",
            }
        ),
        entitlements=frozenset(
            {
                "sales",
                "crm",
            }
        ),
    )


def make_event():
    return ModuleEvent.create(
        event_id="event-executor-001",
        event_type="sales.quote.created",
        publisher_module="sales",
        context=make_context(),
        payload={
            "quote_id": "Q-001",
            "amount": 1250,
        },
    )


def make_envelope(event, subscriber_module="crm"):
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "publisher_module": event.publisher_module,
        "occurred_at": event.occurred_at.isoformat(),
        "subscriber_module": subscriber_module,
        "request_id": event.request_id,
        "organisation_id": str(event.organisation_id),
        "identity_id": str(event.identity_id),
        "session_id": str(event.session_id),
        "permissions": sorted(event.context.permissions),
        "entitlements": sorted(event.context.entitlements),
        "event_payload": dict(event.payload),
    }


def test_executor_reconstructs_and_delivers_event():
    bus = EventBus()
    received = []

    bus.subscribe(
        EventSubscription(
            subscriber_module="crm",
            event_type="sales.quote.created",
            handler=lambda event: received.append(event),
        )
    )

    original = make_event()
    executor = EventDeliveryExecutor(bus)

    result = executor.execute(
        EventDeliveryExecutor.JOB_TYPE,
        make_envelope(original),
    )

    assert result is None
    assert len(received) == 1

    reconstructed = received[0]

    assert reconstructed.event_id == original.event_id
    assert reconstructed.event_type == original.event_type
    assert reconstructed.publisher_module == original.publisher_module
    assert reconstructed.occurred_at == original.occurred_at
    assert reconstructed.payload == original.payload


def test_executor_preserves_framework_context():
    bus = EventBus()
    received = []

    bus.subscribe(
        EventSubscription(
            subscriber_module="crm",
            event_type="sales.quote.created",
            handler=lambda event: received.append(event),
        )
    )

    original = make_event()
    executor = EventDeliveryExecutor(bus)

    executor.execute(
        EventDeliveryExecutor.JOB_TYPE,
        make_envelope(original),
    )

    context = received[0].context

    assert context.request_id == original.context.request_id
    assert context.identity_id == original.context.identity_id
    assert context.organisation_id == original.context.organisation_id
    assert context.session_id == original.context.session_id
    assert context.permissions == original.context.permissions
    assert context.entitlements == original.context.entitlements


def test_executor_targets_only_requested_subscriber():
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

    original = make_event()
    executor = EventDeliveryExecutor(bus)

    executor.execute(
        EventDeliveryExecutor.JOB_TYPE,
        make_envelope(original, "crm"),
    )

    assert received == ["crm"]


def test_executor_propagates_subscriber_failure():
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

    executor = EventDeliveryExecutor(bus)

    with pytest.raises(
        RuntimeError,
        match="subscriber failed",
    ):
        executor.execute(
            EventDeliveryExecutor.JOB_TYPE,
            make_envelope(make_event()),
        )


def test_executor_rejects_wrong_job_type():
    executor = EventDeliveryExecutor(EventBus())

    with pytest.raises(
        ValueError,
        match="Unsupported event delivery job type",
    ):
        executor.execute(
            "wrong.job.type",
            make_envelope(make_event()),
        )


def test_executor_requires_payload():
    executor = EventDeliveryExecutor(EventBus())

    with pytest.raises(
        ValueError,
        match="job payload is required",
    ):
        executor.execute(
            EventDeliveryExecutor.JOB_TYPE,
            None,
        )


def test_executor_rejects_missing_required_field():
    executor = EventDeliveryExecutor(EventBus())

    envelope = make_envelope(make_event())
    del envelope["publisher_module"]

    with pytest.raises(
        ValueError,
        match="publisher_module",
    ):
        executor.execute(
            EventDeliveryExecutor.JOB_TYPE,
            envelope,
        )


def test_executor_rejects_unauthenticated_context():
    bus = EventBus()
    executor = EventDeliveryExecutor(bus)

    envelope = make_envelope(make_event())
    envelope["identity_id"] = None

    with pytest.raises(
        PermissionError,
        match="Authenticated identity is required",
    ):
        executor.execute(
            EventDeliveryExecutor.JOB_TYPE,
            envelope,
        )


def test_executor_rejects_invalid_organisation_id():
    executor = EventDeliveryExecutor(EventBus())

    envelope = make_envelope(make_event())
    envelope["organisation_id"] = "not-a-uuid"

    with pytest.raises(ValueError):
        executor.execute(
            EventDeliveryExecutor.JOB_TYPE,
            envelope,
        )
