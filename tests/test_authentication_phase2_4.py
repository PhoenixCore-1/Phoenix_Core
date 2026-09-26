import pytest
from phoenix_core.auth.service import AuthenticationService
from phoenix_core.errors import AuthenticationError, ValidationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.security.passwords import verify_password
from phoenix_core.sessions.service import SessionService

def make_services(tmp_path):
    from phoenix_core.api.application import CoreApi
    db = SQLiteDatabase(tmp_path / "test.db")
    db.initialise_schema()
    api = CoreApi(db)
    return (
        db,
        api.organisation_service,
        api.user_service,
        api.company_membership_service,
    )

def setup_user(organisations, users, memberships, username="authuser"):
    org = organisations.create_organisation("AUTH", "Auth Org")
    user = users.create_user(
        username=username,
        display_name="Auth User",
        password="CorrectPassword123!",
    )
    membership = memberships.add_membership(user.identity_id, org.id)
    return user, org, membership

def test_authentication_creates_active_session(tmp_path):
    db, organisations, users, memberships = make_services(tmp_path)
    user, org, _ = setup_user(organisations, users, memberships)
    session, token, _ = AuthenticationService(db).authenticate(
        user.username, "CorrectPassword123!", org.id
    )
    assert session.identity_id == user.identity_id
    assert session.status == "ACTIVE"
    assert token
    assert SessionService(db).get_active(session.id)["status"] == "ACTIVE"
    db.close()

def test_bad_credentials_are_rejected(tmp_path):
    db, organisations, users, memberships = make_services(tmp_path)
    user, org, _ = setup_user(organisations, users, memberships, "badcred")
    with pytest.raises(AuthenticationError):
        AuthenticationService(db).authenticate(user.username, "wrong", org.id)
    db.close()

def test_inactive_membership_cannot_authenticate_to_org(tmp_path):
    db, organisations, users, memberships = make_services(tmp_path)
    user, org, membership = setup_user(organisations, users, memberships, "inactive")
    memberships.suspend_membership(membership.id)
    with pytest.raises(AuthenticationError):
        AuthenticationService(db).authenticate(user.username, "CorrectPassword123!", org.id)
    db.close()

def test_session_revoke_and_revoke_all_work(tmp_path):
    db, organisations, users, memberships = make_services(tmp_path)
    user, org, _ = setup_user(organisations, users, memberships, "revoke")
    auth = AuthenticationService(db)
    first, _, _ = auth.authenticate(user.username, "CorrectPassword123!", org.id)
    second, _, _ = auth.authenticate(user.username, "CorrectPassword123!", org.id)
    assert SessionService(db).revoke(first.id)
    assert not SessionService(db).revoke(first.id)
    assert SessionService(db).revoke_all_for_identity(user.identity_id) == 1
    with pytest.raises(AuthenticationError):
        SessionService(db).get_active(second.id)
    db.close()

def test_password_change_requires_current_password_and_updates_hash(tmp_path):
    db, organisations, users, memberships = make_services(tmp_path)
    user, _, _ = setup_user(organisations, users, memberships, "pwchange")
    auth = AuthenticationService(db)
    with pytest.raises(AuthenticationError):
        auth.change_password(user.id, "wrong", "NewPassword12345!")
    auth.change_password(user.id, "CorrectPassword123!", "NewPassword12345!")
    row = db.execute("SELECT password_hash FROM users WHERE id=?", (str(user.id),)).fetchone()
    assert verify_password("NewPassword12345!", row["password_hash"])
    db.close()

def test_password_change_enforces_minimum(tmp_path):
    db, organisations, users, memberships = make_services(tmp_path)
    user, _, _ = setup_user(organisations, users, memberships, "pwmin")
    with pytest.raises(ValidationError):
        AuthenticationService(db).change_password(
            user.id, "CorrectPassword123!", "short"
        )
    db.close()


def test_organisation_scoped_authentication_returns_identity_session(tmp_path):
    db, organisations, users, memberships = make_services(tmp_path)
    user, org, _ = setup_user(organisations, users, memberships, "orgscope")

    session, token, _ = AuthenticationService(db).authenticate(
        user.username,
        "CorrectPassword123!",
        org.id,
    )

    assert session.identity_id == user.identity_id
    assert session.status == "ACTIVE"
    assert token

    db.close()
