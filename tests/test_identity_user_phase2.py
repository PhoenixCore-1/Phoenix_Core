from uuid import UUID

import pytest

from phoenix_core.errors import ConflictError, NotFoundError, ValidationError


def make_service(tmp_path):
    from phoenix_core.infrastructure import SQLiteDatabase
    from phoenix_core.services import CoreFoundationService
    db = SQLiteDatabase(tmp_path / "test.db")
    service = CoreFoundationService(db)
    service.initialise()
    return db, service


def test_user_can_be_read_and_updated(tmp_path):
    db, service = make_service(tmp_path)
    user = service.create_user("alice", "Alice Smith", "StrongPass123!")
    loaded = service.get_user(user.id)
    assert loaded.identity_id == user.identity_id
    assert loaded.display_name == "Alice Smith"
    updated = service.update_user(user.id, display_name="Alice Jones")
    assert updated.display_name == "Alice Jones"
    assert updated.username == "alice"
    db.close()


def test_user_username_change_respects_uniqueness(tmp_path):
    db, service = make_service(tmp_path)
    first = service.create_user("alice", "Alice", "StrongPass123!")
    service.create_user("bob", "Bob", "StrongPass123!")
    with pytest.raises(ConflictError):
        service.update_user(first.id, username="bob")
    db.close()


def test_user_lifecycle_syncs_identity_and_revokes_sessions(tmp_path):
    db, service = make_service(tmp_path)
    user = service.create_user("alice", "Alice", "StrongPass123!")
    session, token = service.authenticate("alice", "StrongPass123!")
    service.suspend_user(user.id)
    assert service.get_user(user.id).status == "SUSPENDED"
    assert service.get_identity(user.identity_id).status == "SUSPENDED"
    row = db.execute("SELECT status FROM sessions WHERE id=?", (str(session.id),)).fetchone()
    assert row["status"] == "REVOKED"
    with pytest.raises(Exception):
        service.authenticate("alice", "StrongPass123!")
    service.reactivate_user(user.id)
    assert service.get_user(user.id).status == "ACTIVE"
    assert service.get_identity(user.identity_id).status == "ACTIVE"
    db.close()


def test_missing_user_is_rejected(tmp_path):
    db, service = make_service(tmp_path)
    with pytest.raises(NotFoundError):
        service.get_user(UUID("00000000-0000-0000-0000-000000000000"))
    db.close()


def test_blank_user_update_is_rejected(tmp_path):
    db, service = make_service(tmp_path)
    user = service.create_user("alice", "Alice", "StrongPass123!")
    with pytest.raises(ValidationError):
        service.update_user(user.id, display_name="   ")
    db.close()
