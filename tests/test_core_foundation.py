import sqlite3
from pathlib import Path
from uuid import UUID

import pytest

from phoenix_core.audit.domain import AuditEvent
from phoenix_core.errors import AuthenticationError, AuthorizationError, ConflictError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.api.application import CoreApi

def make_service(tmp_path):
    db = SQLiteDatabase(tmp_path / "test.db")
    service = CoreApi(db)
    db.initialise_schema()
    return db, service

def test_schema_integrity(tmp_path):
    db, service = make_service(tmp_path)
    assert db.integrity_check()
    db.close()

def test_create_organisation_and_user_membership(tmp_path):
    db, service = make_service(tmp_path)
    org = service.organisation_service.create_organisation("ACME", "Acme Ltd")
    user = service.user_service.create_user(username="admin", display_name="System Administrator", password="Correct-Horse-Battery")
    membership = service.company_membership_service.add_membership(user.identity_id, org.id)

    assert membership.organisation_id == org.id
    assert membership.identity_id == user.identity_id
    db.close()

def test_duplicate_membership_rejected(tmp_path):
    db, service = make_service(tmp_path)
    org = service.organisation_service.create_organisation("ACME", "Acme Ltd")
    user = service.user_service.create_user(username="admin", display_name="Admin", password="Correct-Horse-Battery")
    service.company_membership_service.add_membership(user.identity_id, org.id)

    with pytest.raises(ConflictError):
        service.company_membership_service.add_membership(user.identity_id, org.id)
    db.close()

def test_role_cannot_cross_tenant_boundary(tmp_path):
    db, service = make_service(tmp_path)
    org_a = service.organisation_service.create_organisation("A", "Tenant A")
    org_b = service.organisation_service.create_organisation("B", "Tenant B")
    user = service.user_service.create_user(username="admin", display_name="Admin", password="Correct-Horse-Battery")
    membership = service.company_membership_service.add_membership(user.identity_id, org_a.id)
    role = service.role_service.create_role(org_b.id, "ADMIN", "Administrator")

    with pytest.raises(AuthorizationError):
        service.role_service.assign_role(membership.id, role.id)
    db.close()

def test_authentication_creates_session_and_revoke_works(tmp_path):
    db, service = make_service(tmp_path)
    service.organisation_service.create_organisation("ACME", "Acme Ltd")
    service.user_service.create_user(username="admin", display_name="Admin", password="Correct-Horse-Battery")

    session, token = service.authentication_service.authenticate("admin", "Correct-Horse-Battery")
    assert session.status == "ACTIVE"
    assert token
    assert service.authentication_service.revoke_session(token)
    assert not service.authentication_service.revoke_session(token)
    db.close()

def test_bad_password_is_rejected(tmp_path):
    db, service = make_service(tmp_path)
    service.user_service.create_user(username="admin", display_name="Admin", password="Correct-Horse-Battery")

    with pytest.raises(AuthenticationError):
        service.authentication_service.authenticate("admin", "wrong")
    db.close()

def test_audit_event_can_be_recorded(tmp_path):
    db, service = make_service(tmp_path)
    event = AuditEvent.create("identity.created")
    service.audit_service.record(event)
    row = db.execute("SELECT action FROM audit_events WHERE id=?", (str(event.id),)).fetchone()
    assert row["action"] == "identity.created"
    db.close()
