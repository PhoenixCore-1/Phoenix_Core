from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_core.audit.domain import AuditEvent
from phoenix_core.errors import NotFoundError, ValidationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.services import CoreFoundationService


def make_service(tmp_path):
    db = SQLiteDatabase(tmp_path / "audit_phase2_6.db")
    service = CoreFoundationService(db)
    service.initialise()
    return db, service


def test_record_and_get_audit_event(tmp_path):
    db, service = make_service(tmp_path)
    org = service.create_organisation("ORG1", "Organisation One")
    user = service.create_user("alice", "Alice", "StrongPass123!")
    event = AuditEvent(
        id=uuid4(),
        organisation_id=org.id,
        identity_id=user.identity_id,
        action="USER.CREATED",
        target_type="USER",
        target_id=user.id,
        request_id="req-001",
        created_at=datetime.now(timezone.utc),
    )

    recorded = service.record_audit(event)
    loaded = service.get_audit_event(event.id)

    assert recorded == event
    assert loaded == event
    db.close()


def test_list_audit_events_filters_by_organisation_and_identity(tmp_path):
    db, service = make_service(tmp_path)
    org1 = service.create_organisation("ORG1", "Organisation One")
    org2 = service.create_organisation("ORG2", "Organisation Two")
    user1 = service.create_user("alice", "Alice", "StrongPass123!")
    user2 = service.create_user("bob", "Bob", "StrongPass123!")

    for org, user, action in [
        (org1, user1, "CUSTOMER.CREATED"),
        (org1, user2, "CUSTOMER.UPDATED"),
        (org2, user2, "CUSTOMER.CREATED"),
    ]:
        service.record_audit(AuditEvent(
            id=uuid4(), organisation_id=org.id, identity_id=user.identity_id,
            action=action, target_type="CUSTOMER", target_id=uuid4(),
            request_id=uuid4().hex, created_at=datetime.now(timezone.utc),
        ))

    org1_events = service.list_audit_events(organisation_id=org1.id)
    user2_events = service.list_audit_events(identity_id=user2.identity_id)

    assert len(org1_events) == 2
    assert all(e.organisation_id == org1.id for e in org1_events)
    assert len(user2_events) == 2
    assert all(e.identity_id == user2.identity_id for e in user2_events)
    db.close()


def test_list_audit_events_supports_action_target_and_request_filters(tmp_path):
    db, service = make_service(tmp_path)
    org = service.create_organisation("ORG1", "Organisation One")
    user = service.create_user("alice", "Alice", "StrongPass123!")
    target = uuid4()
    event = AuditEvent(
        id=uuid4(), organisation_id=org.id, identity_id=user.identity_id,
        action="SESSION.REVOKED", target_type="SESSION", target_id=target,
        request_id="request-42", created_at=datetime.now(timezone.utc),
    )
    service.record_audit(event)

    result = service.list_audit_events(
        organisation_id=org.id,
        action="SESSION.REVOKED",
        target_type="SESSION",
        target_id=target,
        request_id="request-42",
    )
    assert result == [event]
    db.close()


def test_audit_events_are_append_only(tmp_path):
    db, service = make_service(tmp_path)
    org = service.create_organisation("ORG1", "Organisation One")
    user = service.create_user("alice", "Alice", "StrongPass123!")
    event = AuditEvent(
        id=uuid4(), organisation_id=org.id, identity_id=user.identity_id,
        action="USER.CREATED", target_type="USER", target_id=user.id,
        request_id="req-append", created_at=datetime.now(timezone.utc),
    )
    service.record_audit(event)

    assert not hasattr(service.audit_service, "update")
    assert not hasattr(service.audit_service, "delete")
    assert service.get_audit_event(event.id).action == "USER.CREATED"
    db.close()


def test_audit_rejects_unknown_organisation_or_identity(tmp_path):
    db, service = make_service(tmp_path)
    event = AuditEvent(
        id=uuid4(), organisation_id=uuid4(), identity_id=uuid4(),
        action="TEST", target_type="TEST", target_id=None,
        request_id=None, created_at=datetime.now(timezone.utc),
    )
    with pytest.raises(ValidationError):
        service.record_audit(event)
    db.close()


def test_audit_tenant_filter_does_not_leak_other_organisation_events(tmp_path):
    db, service = make_service(tmp_path)
    org1 = service.create_organisation("ORG1", "Organisation One")
    org2 = service.create_organisation("ORG2", "Organisation Two")
    for org in (org1, org2):
        service.record_audit(AuditEvent(
            id=uuid4(), organisation_id=org.id, identity_id=None,
            action="TEST.EVENT", target_type="TEST", target_id=None,
            request_id=None, created_at=datetime.now(timezone.utc),
        ))

    events = service.list_audit_events(organisation_id=org1.id)
    assert len(events) == 1
    assert events[0].organisation_id == org1.id
    assert events[0].organisation_id != org2.id
    db.close()


def test_audit_pagination_is_bounded(tmp_path):
    db, service = make_service(tmp_path)
    org = service.create_organisation("ORG1", "Organisation One")
    for i in range(3):
        service.record_audit(AuditEvent(
            id=uuid4(), organisation_id=org.id, identity_id=None,
            action=f"TEST.{i}", target_type="TEST", target_id=None,
            request_id=str(i), created_at=datetime.now(timezone.utc),
        ))

    assert len(service.list_audit_events(organisation_id=org.id, limit=2)) == 2
    with pytest.raises(ValidationError):
        service.list_audit_events(limit=501)
    with pytest.raises(ValidationError):
        service.list_audit_events(offset=-1)
    db.close()


def test_get_missing_audit_event_fails(tmp_path):
    db, service = make_service(tmp_path)
    with pytest.raises(NotFoundError):
        service.get_audit_event(uuid4())
    db.close()
