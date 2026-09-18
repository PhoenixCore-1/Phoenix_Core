from uuid import uuid4

from phoenix_core.ai.audit import AIAuditService
from phoenix_core.audit.service import AuditService
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.security.context import RequestContext


def test_ai_audit_uses_core_audit_authority(tmp_path):
    db_path = tmp_path / "ai_audit_test.db"
    db = SQLiteDatabase(str(db_path))

    db.execute(
        """
        CREATE TABLE organisations (
            id TEXT PRIMARY KEY
        )
        """
    )

    db.execute(
        """
        CREATE TABLE identities (
            id TEXT PRIMARY KEY
        )
        """
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

    core_audit = AuditService(db)
    ai_audit = AIAuditService(core_audit)

    context = RequestContext(
        request_id="ai-audit-request-001",
        identity_id=identity_id,
        organisation_id=organisation_id,
    )

    event = ai_audit.request_started(context)

    assert event.action == "AI_REQUESTED"
    assert event.organisation_id == organisation_id
    assert event.identity_id == identity_id
    assert event.request_id == "ai-audit-request-001"

    stored = core_audit.get(event.id)

    assert stored.id == event.id
    assert stored.action == "AI_REQUESTED"
    assert stored.organisation_id == organisation_id
    assert stored.identity_id == identity_id
    assert stored.target_type == "AI"
    assert stored.request_id == "ai-audit-request-001"
