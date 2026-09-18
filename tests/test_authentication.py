from phoenix_system.services.authentication import AuthenticationService


def test_valid_credentials_create_session() -> None:
    service = AuthenticationService(username="admin", password="correct")
    user = service.authenticate("admin", "correct")

    assert user is not None
    assert user.username == "admin"
    assert user.role == "Administrator"

    token = service.create_session(user)
    assert service.get_user(token) == user


def test_invalid_credentials_are_rejected() -> None:
    service = AuthenticationService(username="admin", password="correct")

    assert service.authenticate("admin", "wrong") is None
    assert service.authenticate("other", "correct") is None


def test_logout_revokes_session() -> None:
    service = AuthenticationService(username="admin", password="correct")
    user = service.authenticate("admin", "correct")
    assert user is not None

    token = service.create_session(user)
    service.revoke_session(token)

    assert service.get_user(token) is None
