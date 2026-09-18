from uuid import UUID

import pytest

from phoenix_core.errors import AuthorizationError, ConflictError, ValidationError


def make_service(tmp_path):
    from phoenix_core.infrastructure import SQLiteDatabase
    from phoenix_core.services import CoreFoundationService
    db = SQLiteDatabase(tmp_path / "test.db")
    service = CoreFoundationService(db)
    service.initialise()
    return db, service


def test_organisation_can_be_read_updated_and_lifecycle_managed(tmp_path):
    db, service = make_service(tmp_path)
    org = service.create_organisation(" acme ", "Acme")
    assert service.get_organisation(org.id).code == "ACME"
    updated = service.update_organisation(org.id, name="Acme Holdings")
    assert updated.name == "Acme Holdings"
    assert service.suspend_organisation(org.id).status == "SUSPENDED"
    assert service.activate_organisation(org.id).status == "ACTIVE"
    assert service.close_organisation(org.id).status == "CLOSED"
    with pytest.raises(ValidationError):
        service.activate_organisation(org.id)
    db.close()


def test_membership_is_created_listed_and_restored(tmp_path):
    db, service = make_service(tmp_path)
    org = service.create_organisation("ACME", "Acme")
    user = service.create_user("alice", "Alice", "StrongPass123!")
    membership = service.add_membership(user.identity_id, org.id)
    assert service.get_membership(membership.id).identity_id == user.identity_id
    assert len(service.list_memberships(org.id, status="ACTIVE")) == 1
    service.suspend_membership(membership.id)
    assert service.list_memberships(org.id, status="SUSPENDED")[0].id == membership.id
    service.restore_membership(membership.id)
    assert service.get_membership(membership.id).status == "ACTIVE"
    db.close()


def test_duplicate_membership_is_rejected(tmp_path):
    db, service = make_service(tmp_path)
    org = service.create_organisation("ACME", "Acme")
    user = service.create_user("alice", "Alice", "StrongPass123!")
    service.add_membership(user.identity_id, org.id)
    with pytest.raises(ConflictError):
        service.add_membership(user.identity_id, org.id)
    db.close()


def test_suspended_organisation_suspends_memberships_and_blocks_new_members(tmp_path):
    db, service = make_service(tmp_path)
    org = service.create_organisation("ACME", "Acme")
    user1 = service.create_user("alice", "Alice", "StrongPass123!")
    service.add_membership(user1.identity_id, org.id)
    service.suspend_organisation(org.id)
    assert service.get_membership(service.list_memberships(org.id)[0].id).status == "SUSPENDED"
    user2 = service.create_user("bob", "Bob", "StrongPass123!")
    with pytest.raises(AuthorizationError):
        service.add_membership(user2.identity_id, org.id)
    db.close()


def test_identity_can_belong_to_multiple_organisations_without_cross_tenant_membership(tmp_path):
    db, service = make_service(tmp_path)
    org1 = service.create_organisation("ONE", "Organisation One")
    org2 = service.create_organisation("TWO", "Organisation Two")
    user = service.create_user("alice", "Alice", "StrongPass123!")
    m1 = service.add_membership(user.identity_id, org1.id)
    m2 = service.add_membership(user.identity_id, org2.id)
    assert m1.organisation_id != m2.organisation_id
    assert {m.organisation_id for m in service.list_memberships(org1.id)} == {org1.id}
    assert {m.organisation_id for m in service.list_memberships(org2.id)} == {org2.id}
    db.close()


def test_removed_membership_is_terminal(tmp_path):
    db, service = make_service(tmp_path)
    org = service.create_organisation("ACME", "Acme")
    user = service.create_user("alice", "Alice", "StrongPass123!")
    membership = service.add_membership(user.identity_id, org.id)
    service.remove_membership(membership.id)
    with pytest.raises(ValidationError):
        service.restore_membership(membership.id)
    db.close()
