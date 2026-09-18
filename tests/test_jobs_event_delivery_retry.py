from uuid import uuid4

import pytest

from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.jobs.event_delivery import CoreEventDeliveryScheduler
from phoenix_core.jobs.registry import JobExecutorRegistry
from phoenix_core.jobs.service import JobService
from phoenix_core.jobs.worker import JobWorker
from phoenix_core.services import CoreFoundationService
from phoenix_framework.context import FrameworkContext
from phoenix_framework.contracts.delivery import EventDelivery
from phoenix_framework.contracts.event import ModuleEvent
from phoenix_framework.contracts.subscription import EventSubscription
from phoenix_framework.integration.delivery import EventDeliverySchedule
from phoenix_framework.integration.event_executor import EventDeliveryExecutor
from phoenix_framework.integration.events import EventBus


def make_environment(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "test.db"))
    core = CoreFoundationService(db)
    core.initialise()

    organisation = core.create_organisation(
        f"ORG-{uuid4().hex[:8].upper()}",
        f"Test Organisation {uuid4().hex[:8]}",
    )

    user = core.create_user(
        f"user_{uuid4().hex[:8]}",
        "Test User",
        "TestPassword123!",
    )

    job_service = JobService(db)
    scheduler = CoreEventDeliveryScheduler(job_service)

    event_bus = EventBus()
    executor = EventDeliveryExecutor(event_bus)

    registry = JobExecutorRegistry()
    registry.register(
        EventDeliveryExecutor.JOB_TYPE,
        executor,
    )

    worker = JobWorker(job_service, registry)

    return (
        db,
        organisation,
        user,
        job_service,
        scheduler,
        event_bus,
        worker,
    )


def make_request(organisation, user):
    context = FrameworkContext(
        request_id="req-retry-001",
        identity_id=user.identity_id,
        organisation_id=organisation.id,
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

    event = ModuleEvent.create(
        event_id="event-retry-001",
        event_type="sales.quote.created",
        publisher_module="sales",
        context=context,
        payload={
            "quote_id": "Q-RETRY-001",
        },
    )

    delivery = EventDelivery.from_event(event, "crm")

    return EventDeliverySchedule(
        delivery=delivery,
        payload=dict(event.payload),
    )


def test_failed_event_delivery_can_be_retried(tmp_path):
    (
        db,
        organisation,
        user,
        job_service,
        scheduler,
        event_bus,
        worker,
    ) = make_environment(tmp_path)

    attempts = []

    def failing_handler(event):
        attempts.append(event.event_id)
        raise RuntimeError("Temporary subscriber failure.")

    event_bus.subscribe(
        EventSubscription(
            subscriber_module="crm",
            event_type="sales.quote.created",
            handler=failing_handler,
        )
    )

    request = make_request(organisation, user)

    job = scheduler.schedule(request)

    with pytest.raises(RuntimeError, match="Temporary subscriber failure"):
        worker.process(job.id)

    failed = job_service.get(job.id)

    assert failed.status == "FAILED"
    assert failed.attempt_count == 1
    assert failed.error_code == "RuntimeError"
    assert failed.error_message == "Temporary subscriber failure."
    assert attempts == ["event-retry-001"]

    job_service.retry(job.id)

    retried = job_service.get(job.id)

    assert retried.status == "QUEUED"
    assert retried.attempt_count == 1
    assert retried.failed_at is None
    assert retried.error_code is None
    assert retried.error_message is None

    def successful_handler(event):
        attempts.append(event.event_id)
        return {"processed": event.event_id}

    event_bus.unsubscribe("crm", "sales.quote.created")
    event_bus.subscribe(
        EventSubscription(
            subscriber_module="crm",
            event_type="sales.quote.created",
            handler=successful_handler,
        )
    )

    result = worker.process(job.id)

    assert result.status == "COMPLETED"
    assert result.data == {"processed": "event-retry-001"}

    completed = job_service.get(job.id)

    assert completed.status == "COMPLETED"
    assert completed.attempt_count == 2
    assert attempts == [
        "event-retry-001",
        "event-retry-001",
    ]

    db.close()


def test_event_delivery_idempotency_is_organisation_scoped(tmp_path):
    (
        db,
        organisation,
        user,
        job_service,
        scheduler,
        event_bus,
        worker,
    ) = make_environment(tmp_path)

    request = make_request(organisation, user)

    first = scheduler.schedule(request)
    second = scheduler.schedule(request)

    assert first.id == second.id
    assert first.idempotency_key == second.idempotency_key

    jobs = job_service.list(
        organisation_id=organisation.id,
        job_type=CoreEventDeliveryScheduler.EVENT_DELIVERY_JOB_TYPE,
    )

    assert len(jobs) == 1

    db.close()


def test_retry_cannot_exceed_maximum_attempts(tmp_path):
    (
        db,
        organisation,
        user,
        job_service,
        scheduler,
        event_bus,
        worker,
    ) = make_environment(tmp_path)

    context = FrameworkContext(
        request_id="req-retry-exhausted-001",
        identity_id=user.identity_id,
        organisation_id=organisation.id,
        session_id=uuid4(),
        permissions=frozenset({"crm.quote.create"}),
        entitlements=frozenset({"crm"}),
    )

    event = ModuleEvent.create(
        event_id="event-retry-exhausted-001",
        event_type="sales.quote.created",
        publisher_module="sales",
        context=context,
        payload={
            "quote_id": "Q-RETRY-EXHAUSTED-001",
        },
    )

    delivery = EventDelivery.from_event(event, "crm")

    request = EventDeliverySchedule(
        delivery=delivery,
        payload=dict(event.payload),
    )

    attempts = []

    def failing_handler(event):
        attempts.append(event.event_id)
        raise RuntimeError("Permanent subscriber failure.")

    event_bus.subscribe(
        EventSubscription(
            subscriber_module="crm",
            event_type="sales.quote.created",
            handler=failing_handler,
        )
    )

    job = scheduler.schedule(request)

    with pytest.raises(RuntimeError, match="Permanent subscriber failure"):
        worker.process(job.id)

    failed = job_service.get(job.id)

    assert failed.status == "FAILED"
    assert failed.attempt_count == 1
    assert failed.max_attempts == 3

    job_service.retry(job.id)

    with pytest.raises(RuntimeError, match="Permanent subscriber failure"):
        worker.process(job.id)

    failed = job_service.get(job.id)

    assert failed.status == "FAILED"
    assert failed.attempt_count == 2

    job_service.retry(job.id)

    with pytest.raises(RuntimeError, match="Permanent subscriber failure"):
        worker.process(job.id)

    failed = job_service.get(job.id)

    assert failed.status == "FAILED"
    assert failed.attempt_count == 3

    with pytest.raises(
        Exception,
        match="maximum attempts have been reached",
    ):
        job_service.retry(job.id)

    final_job = job_service.get(job.id)

    assert final_job.status == "FAILED"
    assert final_job.attempt_count == 3
    assert attempts == [
        "event-retry-exhausted-001",
        "event-retry-exhausted-001",
        "event-retry-exhausted-001",
    ]

    db.close()
