from uuid import uuid4

from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.jobs.event_delivery import CoreEventDeliveryScheduler
from phoenix_core.jobs.registry import JobExecutorRegistry
from phoenix_core.jobs.service import JobService
from phoenix_core.jobs.worker import JobWorker
from phoenix_core.services import CoreFoundationService
from phoenix_framework.contracts.delivery import EventDelivery
from phoenix_framework.contracts.event import ModuleEvent
from phoenix_framework.contracts.subscription import EventSubscription
from phoenix_framework.integration.event_executor import EventDeliveryExecutor
from phoenix_framework.integration.events import EventBus
from phoenix_framework.integration.delivery import EventDeliverySchedule


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

    worker = JobWorker(
        job_service,
        registry,
    )

    return (
        db,
        core,
        organisation,
        user,
        scheduler,
        event_bus,
        worker,
    )


def make_request(organisation, user):
    context = {
        "request_id": "req-worker-event-001",
        "identity_id": user.identity_id,
        "organisation_id": organisation.id,
        "session_id": uuid4(),
        "permissions": frozenset(
            {
                "sales.quote.read",
                "crm.quote.create",
            }
        ),
        "entitlements": frozenset(
            {
                "sales",
                "crm",
            }
        ),
    }

    from phoenix_framework.context import FrameworkContext

    framework_context = FrameworkContext(**context)

    event = ModuleEvent.create(
        event_id="event-worker-001",
        event_type="sales.quote.created",
        publisher_module="sales",
        context=framework_context,
        payload={
            "quote_id": "Q-WORKER-001",
            "amount": 2500,
        },
    )

    delivery = EventDelivery.from_event(
        event,
        "crm",
    )

    return EventDeliverySchedule(
        delivery=delivery,
        payload=dict(event.payload),
    )


def test_worker_executes_durable_event_delivery(tmp_path):
    (
        db,
        core,
        organisation,
        user,
        scheduler,
        event_bus,
        worker,
    ) = make_environment(tmp_path)

    received = []

    def handle_event(event):
        received.append(event)
        return {"handled": event.payload["quote_id"]}

    event_bus.subscribe(
        EventSubscription(
            subscriber_module="crm",
            event_type="sales.quote.created",
            handler=handle_event,
        )
    )

    request = make_request(organisation, user)

    job = scheduler.schedule(request)

    assert job.status == "QUEUED"

    result = worker.process(job.id)

    assert result.status == "COMPLETED"
    assert result.job_id == job.id
    assert result.data == {
        "handled": "Q-WORKER-001",
    }

    assert len(received) == 1

    event = received[0]

    assert event.event_id == "event-worker-001"
    assert event.event_type == "sales.quote.created"
    assert event.publisher_module == "sales"
    assert event.payload == {
        "quote_id": "Q-WORKER-001",
        "amount": 2500,
    }

    assert event.context.request_id == request.request_id
    assert event.context.identity_id == user.identity_id
    assert event.context.organisation_id == organisation.id
    assert event.context.session_id == request.delivery.session_id
    assert event.context.permissions == frozenset(
        {
            "sales.quote.read",
            "crm.quote.create",
        }
    )
    assert event.context.entitlements == frozenset(
        {
            "sales",
            "crm",
        }
    )

    db.close()
