from uuid import uuid4

from phoenix_system.contracts.membership import (
    MembershipAdministration,
    MembershipStatus,
)


def test_membership_defaults():
    membership = MembershipAdministration(
        membership_id=uuid4(),
        identity_id=uuid4(),
        organisation_id=uuid4(),
        status=MembershipStatus.ACTIVE,
    )

    assert membership.active is True
    assert membership.administrable is True
    assert membership.can_administer_membership() is False


def test_membership_active():
    membership = MembershipAdministration(
        membership_id=uuid4(),
        identity_id=uuid4(),
        organisation_id=uuid4(),
        status=MembershipStatus.ACTIVE,
        can_manage_membership=True,
    )

    assert membership.active is True
    assert membership.administrable is True
    assert membership.can_administer_membership() is True


def test_membership_suspended():
    membership = MembershipAdministration(
        membership_id=uuid4(),
        identity_id=uuid4(),
        organisation_id=uuid4(),
        status=MembershipStatus.SUSPENDED,
        can_manage_membership=True,
    )

    assert membership.active is False
    assert membership.administrable is False
    assert membership.can_administer_membership() is True


def test_membership_revoked():
    membership = MembershipAdministration(
        membership_id=uuid4(),
        identity_id=uuid4(),
        organisation_id=uuid4(),
        status=MembershipStatus.REVOKED,
        can_assign_roles=True,
    )

    assert membership.active is False
    assert membership.administrable is False
    assert membership.can_administer_membership() is True


def test_membership_role_administration():
    membership = MembershipAdministration(
        membership_id=uuid4(),
        identity_id=uuid4(),
        organisation_id=uuid4(),
        status=MembershipStatus.ACTIVE,
        can_assign_roles=True,
    )

    assert membership.can_assign_roles is True
    assert membership.can_administer_membership() is True


def test_membership_module_access_administration():
    membership = MembershipAdministration(
        membership_id=uuid4(),
        identity_id=uuid4(),
        organisation_id=uuid4(),
        status=MembershipStatus.ACTIVE,
        can_manage_module_access=True,
    )

    assert membership.can_manage_module_access is True
    assert membership.can_administer_membership() is True
