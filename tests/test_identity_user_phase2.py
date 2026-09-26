from uuid import UUID

import pytest

from phoenix_core.errors import ConflictError, NotFoundError, ValidationError


def make_services(tmp_path):
    from phoenix_core.api.application import CoreApi
    from phoenix_core.infrastructure import SQLiteDatabase

    db = SQLiteDatabase(tmp_path / "test.db")
    db.initialise_schema()
    api = CoreApi(db)

    return (
        db,
        api.user_service,
        api.identity_service,
        api.authentication_service,
        api.organisation_service,
        api.company_membership_service,
    )


def create_test_user(users, username="alice", display_name="Alice"):
    return users.create_user(
        username=username,
        display_name=display_name,
        password="StrongPass123!",
    )


def create_authenticated_user(users, organisations, memberships, username="alice"):
    user = create_test_user(users, username)
    organisation = organisations.create_organisation(
        f"{username.upper()}ORG",
        f"{username.title()} Organisation",
    )
    memberships.add_membership(user.identity_id, organisation.id)
    return user, organisation


def test_user_can_be_read_and_updated(tmp_path):
    db, users, identities, authentication, organisations, memberships = make_services(tmp_path)
    user = create_test_user(users, "alice", "Alice Smith")
    loaded = users.get_user(user.id)

    assert loaded.identity_id == user.identity_id
    assert loaded.display_name == "Alice Smith"

    updated = users.update_user(user.id, display_name="Alice Jones")

    assert updated.display_name == "Alice Jones"
    assert updated.username == "alice"
    db.close()


def test_user_username_change_respects_uniqueness(tmp_path):
    db, users, identities, authentication, organisations, memberships = make_services(tmp_path)
    first = create_test_user(users, "alice", "Alice")
    create_test_user(users, "bob", "Bob")

    with pytest.raises(ConflictError):
        users.update_user(first.id, username="bob")

    db.close()


def test_user_lifecycle_syncs_identity_and_revokes_sessions(tmp_path):
    db, users, identities, authentication, organisations, memberships = make_services(tmp_path)
    user, organisation = create_authenticated_user(
        users,
        organisations,
        memberships,
        "alice",
    )

    session, token, _ = authentication.authenticate(
        user.username,
        "StrongPass123!",
        organisation.id,
    )

    users.suspend_user(user.id)

    assert users.get_user(user.id).status == "SUSPENDED"
    assert identities.get_identity(user.identity_id).status == "SUSPENDED"

    row = db.execute(
        "SELECT status FROM sessions WHERE id=?",
        (str(session.id),),
    ).fetchone()

    assert row["status"] == "REVOKED"

    with pytest.raises(Exception):
        authentication.authenticate(
            user.username,
            "StrongPass123!",
            organisation.id,
        )

    users.reactivate_user(user.id)

    assert users.get_user(user.id).status == "ACTIVE"
    assert identities.get_identity(user.identity_id).status == "ACTIVE"
    db.close()


def test_missing_user_is_rejected(tmp_path):
    db, users, identities, authentication, organisations, memberships = make_services(tmp_path)

    with pytest.raises(NotFoundError):
        users.get_user(UUID("00000000-0000-0000-0000-000000000000"))

    db.close()


def test_blank_user_update_is_rejected(tmp_path):
    db, users, identities, authentication, organisations, memberships = make_services(tmp_path)
    user = create_test_user(users)

    with pytest.raises(ValidationError):
        users.update_user(user.id, display_name="   ")

    db.close()
