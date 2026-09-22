from uuid import UUID

import pytest

from phoenix_core.errors import AuthorizationError, ConflictError, ValidationError


def make_services(tmp_path):
    from phoenix_core.api.application import CoreApi
    from phoenix_core.infrastructure import SQLiteDatabase

    db = SQLiteDatabase(tmp_path / "test.db")
    db.initialise_schema()

    api = CoreApi(db)

    return (
        db,
        api.organisation_service,
        api.user_service,
        api.company_membership_service,
    )


def test_organisation_can_be_read_updated_and_lifecycle_managed(tmp_path):
    db, organisations, users, memberships = make_services(tmp_path)
    org = organisations.create_organisation(" acme ", "Acme")
    assert organisations.get_organisation(org.id).code == "ACME"
    updated = organisations.update_organisation(org.id, name="Acme Holdings")
    assert updated.name == "Acme Holdings"
    assert organisations.suspend_organisation(org.id).status == "SUSPENDED"
    assert organisations.activate_organisation(org.id).status == "ACTIVE"
    assert organisations.close_organisation(org.id).status == "CLOSED"
    with pytest.raises(ValidationError):
        organisations.activate_organisation(org.id)
    db.close()


def test_membership_is_created_listed_and_restored(tmp_path):
    db, organisations, users, memberships = make_services(tmp_path)
    org = organisations.create_organisation("ACME", "Acme")
    user = users.create_user(username="alice", display_name="Alice", password="StrongPass123!")
    membership = memberships.add_membership(user.identity_id, org.id)
    assert memberships.get_membership(membership.id).identity_id == user.identity_id
    assert len(memberships.list_memberships(org.id, status="ACTIVE")) == 1
    memberships.suspend_membership(membership.id)
    assert memberships.list_memberships(org.id, status="SUSPENDED")[0].id == membership.id
    memberships.restore_membership(membership.id)
    assert memberships.get_membership(membership.id).status == "ACTIVE"
    db.close()


def test_duplicate_membership_is_rejected(tmp_path):
    db, organisations, users, memberships = make_services(tmp_path)
    org = organisations.create_organisation("ACME", "Acme")
    user = users.create_user(username="alice", display_name="Alice", password="StrongPass123!")
    memberships.add_membership(user.identity_id, org.id)
    with pytest.raises(ConflictError):
        memberships.add_membership(user.identity_id, org.id)
    db.close()


def test_suspended_organisation_suspends_memberships_and_blocks_new_members(tmp_path):
    db, organisations, users, memberships = make_services(tmp_path)
    org = organisations.create_organisation("ACME", "Acme")
    user1 = users.create_user(username="alice", display_name="Alice", password="StrongPass123!")
    memberships.add_membership(user1.identity_id, org.id)
    organisations.suspend_organisation(org.id)
    assert memberships.get_membership(memberships.list_memberships(org.id)[0].id).status == "SUSPENDED"
    user2 = users.create_user(username="bob", display_name="Bob", password="StrongPass123!")
    with pytest.raises(AuthorizationError):
        memberships.add_membership(user2.identity_id, org.id)
    db.close()


def test_identity_can_belong_to_multiple_organisations_without_cross_tenant_membership(tmp_path):
    db, organisations, users, memberships = make_services(tmp_path)
    org1 = organisations.create_organisation("ONE", "Organisation One")
    org2 = organisations.create_organisation("TWO", "Organisation Two")
    user = users.create_user(username="alice", display_name="Alice", password="StrongPass123!")
    m1 = memberships.add_membership(user.identity_id, org1.id)
    m2 = memberships.add_membership(user.identity_id, org2.id)
    assert m1.organisation_id != m2.organisation_id
    assert {m.organisation_id for m in memberships.list_memberships(org1.id)} == {org1.id}
    assert {m.organisation_id for m in memberships.list_memberships(org2.id)} == {org2.id}
    db.close()


def test_removed_membership_is_terminal(tmp_path):
    db, organisations, users, memberships = make_services(tmp_path)
    org = organisations.create_organisation("ACME", "Acme")
    user = users.create_user(username="alice", display_name="Alice", password="StrongPass123!")
    membership = memberships.add_membership(user.identity_id, org.id)
    memberships.remove_membership(membership.id)
    with pytest.raises(ValidationError):
        memberships.restore_membership(membership.id)
    db.close()

