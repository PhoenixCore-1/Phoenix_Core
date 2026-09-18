from uuid import uuid4

from phoenix_system.contracts.platform import PlatformAdministration


def test_platform_defaults():
    platform = PlatformAdministration(
        administration_id=uuid4(),
        organisation_id=uuid4(),
        capability="global_search",
    )

    assert platform.active is False
    assert platform.administrable is False
    assert platform.can_administer_platform() is False


def test_platform_active_when_enabled_and_available():
    platform = PlatformAdministration(
        administration_id=uuid4(),
        organisation_id=uuid4(),
        capability="global_search",
        enabled=True,
        available=True,
    )

    assert platform.active is True


def test_platform_not_active_when_unavailable():
    platform = PlatformAdministration(
        administration_id=uuid4(),
        organisation_id=uuid4(),
        capability="global_search",
        enabled=True,
        available=False,
    )

    assert platform.active is False


def test_platform_administration():
    platform = PlatformAdministration(
        administration_id=uuid4(),
        organisation_id=uuid4(),
        capability="global_search",
        can_manage_platform=True,
    )

    assert platform.administrable is True
    assert platform.can_administer_platform() is True


def test_platform_requires_administration_permission():
    platform = PlatformAdministration(
        administration_id=uuid4(),
        organisation_id=uuid4(),
        capability="global_search",
        enabled=True,
        available=True,
        can_manage_platform=False,
    )

    assert platform.active is True
    assert platform.administrable is False
    assert platform.can_administer_platform() is False


def test_platform_is_tenant_bound():
    organisation_id = uuid4()

    platform = PlatformAdministration(
        administration_id=uuid4(),
        organisation_id=organisation_id,
        capability="global_search",
    )

    assert platform.organisation_id == organisation_id
