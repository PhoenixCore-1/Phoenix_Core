from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_framework.contracts.delivery import EventDelivery
from phoenix_framework.integration.delivery import (
    EventDeliverySchedule,
    EventDeliveryScheduler,
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
    )


def test_schedule_preserves_delivery():
    delivery = make_delivery()

    request = EventDeliverySchedule(
        delivery=delivery,
    )

    assert request.delivery == delivery


def test_schedule_exposes_delivery_context():
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
    )

    request = EventDeliverySchedule(
        delivery=delivery,
    )

    assert request.request_id == "req-delivery-001"
    assert request.organisation_id == organisation_id
    assert request.identity_id == identity_id


def test_schedule_exposes_event_metadata():
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

    request = EventDeliverySchedule(
        delivery=delivery,
    )

    assert request.delivery.publisher_module == "sales"
    assert request.delivery.occurred_at == occurred_at


def test_schedule_uses_delivery_key_as_idempotency_key():
    request = EventDeliverySchedule(
        delivery=make_delivery(),
    )

    assert request.idempotency_key == (
        "event:event-001:subscriber:crm"
    )


def test_schedule_supports_payload_and_scheduled_at():
    scheduled_at = datetime.now(timezone.utc)

    request = EventDeliverySchedule(
        delivery=make_delivery(),
        payload={"quote_id": "Q-001"},
        scheduled_at=scheduled_at,
    )

    assert request.payload == {"quote_id": "Q-001"}
    assert request.scheduled_at == scheduled_at


def test_scheduler_defines_framework_independent_port():
    class ExampleScheduler(EventDeliveryScheduler):
        def schedule(self, request):
            return {
                "idempotency_key": request.idempotency_key,
                "organisation_id": request.organisation_id,
            }

    scheduler = ExampleScheduler()
    request = EventDeliverySchedule(
        delivery=make_delivery(),
    )

    result = scheduler.schedule(request)

    assert result["idempotency_key"] == (
        "event:event-001:subscriber:crm"
    )
    assert result["organisation_id"] == request.organisation_id


def test_scheduler_base_contract_requires_implementation():
    scheduler = EventDeliveryScheduler()

    with pytest.raises(NotImplementedError):
        scheduler.schedule(
            EventDeliverySchedule(
                delivery=make_delivery(),
            )
        )


def test_schedule_is_immutable():
    request = EventDeliverySchedule(
        delivery=make_delivery(),
    )

    with pytest.raises(AttributeError):
        request.delivery = make_delivery()
