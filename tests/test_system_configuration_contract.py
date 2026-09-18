from uuid import uuid4

from phoenix_system.contracts.configuration import ConfigurationAdministration


def test_configuration_defaults():
    configuration = ConfigurationAdministration(
        configuration_id=uuid4(),
        organisation_id=uuid4(),
        key="timezone",
        value="Africa/Johannesburg",
    )

    assert configuration.active is True
    assert configuration.administrable is False
    assert configuration.can_administer_configuration() is False


def test_configuration_disabled():
    configuration = ConfigurationAdministration(
        configuration_id=uuid4(),
        organisation_id=uuid4(),
        key="timezone",
        value="Africa/Johannesburg",
        enabled=False,
    )

    assert configuration.active is False


def test_configuration_administration():
    configuration = ConfigurationAdministration(
        configuration_id=uuid4(),
        organisation_id=uuid4(),
        key="timezone",
        value="Africa/Johannesburg",
        can_manage_configuration=True,
    )

    assert configuration.administrable is True
    assert configuration.can_administer_configuration() is True


def test_configuration_requires_administration_permission():
    configuration = ConfigurationAdministration(
        configuration_id=uuid4(),
        organisation_id=uuid4(),
        key="timezone",
        value="Africa/Johannesburg",
        enabled=True,
        can_manage_configuration=False,
    )

    assert configuration.active is True
    assert configuration.administrable is False
    assert configuration.can_administer_configuration() is False


def test_configuration_supports_structured_values():
    value = {"currency": "ZAR", "locale": "en-ZA"}

    configuration = ConfigurationAdministration(
        configuration_id=uuid4(),
        organisation_id=uuid4(),
        key="regional_settings",
        value=value,
    )

    assert configuration.value == value


def test_configuration_is_tenant_bound():
    organisation_id = uuid4()

    configuration = ConfigurationAdministration(
        configuration_id=uuid4(),
        organisation_id=organisation_id,
        key="timezone",
        value="Africa/Johannesburg",
    )

    assert configuration.organisation_id == organisation_id
