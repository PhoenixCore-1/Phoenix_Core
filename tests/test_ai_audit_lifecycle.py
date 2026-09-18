from uuid import uuid4

from phoenix_core.ai.audit import AIAuditService
from phoenix_core.ai.contracts import AIActionRequest
from phoenix_core.audit.service import AuditService
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.security.context import RequestContext


def setup():
    db = SQLiteDatabase(":memory:")

    db.execute(
        "CREATE TABLE organisations (id TEXT PRIMARY KEY)"
    )
    db.execute(
        "CREATE TABLE identities (id TEXT PRIMARY KEY)"
    )
    db.execute(
        """
        CREATE TABLE audit_events (
            id TEXT PRIMARY KEY,
            organisation_id TEXT,
            identity_id TEXT,
            action TEXT NOT NULL,
            target_type TEXT,
            target_id TEXT,
            request_id TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    organisation_id = uuid4()
    identity_id = uuid4()

    db.execute(
        "INSERT INTO organisations (id) VALUES (?)",
        (str(organisation_id),),
    )
    db.execute(
        "INSERT INTO identities (id) VALUES (?)",
        (str(identity_id),),
    )
    db.commit()

    context = RequestContext(
        request_id="ai-lifecycle-test",
        identity_id=identity_id,
        organisation_id=organisation_id,
    )

    return AIAuditService(AuditService(db)), context


def test_ai_lifecycle_events():
    service, context = setup()

    service.request_started(context)
    service.request_completed(context)
    service.request_failed(context)
    service.quota_exceeded(context)
    service.rate_limited(context)

    events = [
        service.audit_service.get(event.id)
        for event in service.audit_service.list(
            organisation_id=context.organisation_id
        )
    ]

    actions = {event.action for event in events}

    assert actions == {
        "AI_REQUESTED",
        "AI_COMPLETED",
        "AI_FAILED",
        "AI_QUOTA_EXCEEDED",
        "AI_RATE_LIMITED",
    }


def test_ai_action_lifecycle():
    service, context = setup()

    target_id = uuid4()

    action = AIActionRequest(
        action_type="create_production_order",
        target_type="production_order",
        target_id=str(target_id),
    )

    proposed = service.action_proposed(context, action)
    authorized = service.action_authorized(context, action)
    executed = service.action_executed(context, action)

    assert proposed.action == "AI_ACTION_PROPOSED"
    assert authorized.action == "AI_ACTION_AUTHORIZED"
    assert executed.action == "AI_ACTION_EXECUTED"

    assert proposed.target_id == target_id
    assert authorized.target_id == target_id
    assert executed.target_id == target_id

    assert proposed.organisation_id == context.organisation_id
    assert authorized.organisation_id == context.organisation_id
    assert executed.organisation_id == context.organisation_id
