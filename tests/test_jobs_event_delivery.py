from datetime import datetime, timezone
from uuid import uuid4

from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.jobs.event_delivery import CoreEventDeliveryScheduler
from phoenix_core.jobs.service import JobService
from phoenix_core.services import CoreFoundationService
from phoenix_framework.contracts.delivery import EventDelivery
from phoenix_framework.integration.delivery import EventDeliverySchedule


def make_scheduler(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "test.db"))
    core = CoreFoundationService(db)
    core.initialise()

    return db, core, CoreEventDeliveryScheduler(JobService(db))


def make_organisation(core):
    return core.create_organisation(
        f"ORG-{uuid4().hex[:8].upper()}",
        f"Test Organisation {uuid4().hex[:8]}",
    )


def make_user(core):
    return core.create_user(
        f"user_{uuid4().hex[:8]}",
        "Test User",
        "TestPassword123!",
    )


def make_request(core):
    organisation = make_organisation(core)
    user = make_user(core)

    delivery = EventDelivery(
        event_id="event-001",
        event_type="sales.quote.created",
        publisher_module="sales",
        occurred_at=datetime.now(timezone.utc),
        subscriber_module="crm",
        request_id="req-event-001",
        organisation_id=organisation.id,
        identity_id=user.identity_id,
        session_id=uuid4(),
        permissions=frozenset({"sales.quote.read"}),
        entitlements=frozenset({"sales"}),
    )

    return EventDeliverySchedule(
        delivery=delivery,
        payload={"quote_id": "Q-001"},
    )


def test_scheduler_creates_core_job(tmp_path):
    db, core, scheduler = make_scheduler(tmp_path)

    request = make_request(core)

    job = scheduler.schedule(request)

    assert job.status == "QUEUED"
    assert job.job_type == "framework.event_delivery"
    assert job.request_id == request.request_id
    assert job.organisation_id == request.organisation_id
    assert job.identity_id == request.identity_id

    assert job.payload["event_id"] == request.delivery.event_id
    assert job.payload["event_type"] == request.delivery.event_type
    assert job.payload["publisher_module"] == (
        request.delivery.publisher_module
    )
    assert job.payload["occurred_at"] == (
        request.delivery.occurred_at.isoformat()
    )
    assert job.payload["subscriber_module"] == (
        request.delivery.subscriber_module
    )
    assert job.payload["request_id"] == request.request_id
    assert job.payload["organisation_id"] == str(
        request.organisation_id
    )
    assert job.payload["identity_id"] == str(request.identity_id)
    assert job.payload["session_id"] == str(
        request.delivery.session_id
    )
    assert job.payload["permissions"] == ["sales.quote.read"]
    assert job.payload["entitlements"] == ["sales"]
    assert job.payload["event_payload"] == {"quote_id": "Q-001"}

    assert job.idempotency_key == request.idempotency_key

    db.close()


def test_scheduler_uses_delivery_key_for_idempotency(tmp_path):
    db, core, scheduler = make_scheduler(tmp_path)

    request = make_request(core)

    first = scheduler.schedule(request)
    second = scheduler.schedule(request)

    assert second.id == first.id
    assert second.idempotency_key == first.idempotency_key

    db.close()


def test_different_subscribers_create_different_jobs(tmp_path):
    db, core, scheduler = make_scheduler(tmp_path)

    first_request = make_request(core)

    second_delivery = EventDelivery(
        event_id=first_request.delivery.event_id,
        event_type=first_request.delivery.event_type,
        publisher_module=first_request.delivery.publisher_module,
        occurred_at=first_request.delivery.occurred_at,
        subscriber_module="inventory",
        request_id=first_request.request_id,
        organisation_id=first_request.organisation_id,
        identity_id=first_request.identity_id,
        session_id=first_request.delivery.session_id,
        permissions=first_request.delivery.permissions,
        entitlements=first_request.delivery.entitlements,
    )

    second_request = EventDeliverySchedule(
        delivery=second_delivery,
        payload={"quote_id": "Q-001"},
    )

    first = scheduler.schedule(first_request)
    second = scheduler.schedule(second_request)

    assert first.id != second.id
    assert first.idempotency_key != second.idempotency_key

    db.close()
