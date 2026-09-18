from uuid import uuid4

from phoenix_system.contracts.user import UserAdministration, UserStatus


def test_user_administration_defaults():
    user = UserAdministration(
        identity_id=uuid4(),
        organisation_id=uuid4(),
        status=UserStatus.ACTIVE,
    )

    assert user.active is True
    assert user.administrable is True
    assert user.can_administer_users() is False


def test_user_administration_active():
    user = UserAdministration(
        identity_id=uuid4(),
        organisation_id=uuid4(),
        status=UserStatus.ACTIVE,
        can_manage_profile=True,
    )

    assert user.active is True
    assert user.administrable is True
    assert user.can_administer_users() is True


def test_user_administration_suspended():
    user = UserAdministration(
        identity_id=uuid4(),
        organisation_id=uuid4(),
        status=UserStatus.SUSPENDED,
        can_manage_profile=True,
    )

    assert user.active is False
    assert user.administrable is False
    assert user.can_administer_users() is True


def test_user_administration_disabled():
    user = UserAdministration(
        identity_id=uuid4(),
        organisation_id=uuid4(),
        status=UserStatus.DISABLED,
        can_manage_module_access=True,
    )

    assert user.active is False
    assert user.administrable is False
    assert user.can_administer_users() is True


def test_user_administration_membership_and_roles():
    user = UserAdministration(
        identity_id=uuid4(),
        organisation_id=uuid4(),
        status=UserStatus.ACTIVE,
        can_manage_memberships=True,
        can_manage_roles=True,
    )

    assert user.can_manage_memberships is True
    assert user.can_manage_roles is True
    assert user.can_administer_users() is True


def test_user_administration_module_access():
    user = UserAdministration(
        identity_id=uuid4(),
        organisation_id=uuid4(),
        status=UserStatus.ACTIVE,
        can_manage_module_access=True,
    )

    assert user.can_manage_module_access is True
    assert user.can_administer_users() is True
