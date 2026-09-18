from uuid import uuid4

from phoenix_system.contracts.module import ModuleAdministration


def test_module_defaults():
    module = ModuleAdministration(
        module_code="crm",
        name="CRM",
        version="1.0.0",
        organisation_id=uuid4(),
    )

    assert module.active is False
    assert module.administrable is False
    assert module.configurable is False
    assert module.can_administer_module() is False


def test_module_active_when_enabled_and_entitled():
    module = ModuleAdministration(
        module_code="crm",
        name="CRM",
        version="1.0.0",
        organisation_id=uuid4(),
        enabled=True,
        entitled=True,
    )

    assert module.active is True


def test_module_not_active_without_entitlement():
    module = ModuleAdministration(
        module_code="crm",
        name="CRM",
        version="1.0.0",
        organisation_id=uuid4(),
        enabled=True,
        entitled=False,
    )

    assert module.active is False


def test_module_administration():
    module = ModuleAdministration(
        module_code="crm",
        name="CRM",
        version="1.0.0",
        organisation_id=uuid4(),
        can_manage_module=True,
    )

    assert module.administrable is True
    assert module.configurable is False
    assert module.can_administer_module() is True


def test_module_configuration():
    module = ModuleAdministration(
        module_code="crm",
        name="CRM",
        version="1.0.0",
        organisation_id=uuid4(),
        can_manage_configuration=True,
    )

    assert module.administrable is False
    assert module.configurable is True
    assert module.can_administer_module() is True


def test_module_is_tenant_bound():
    organisation_id = uuid4()

    module = ModuleAdministration(
        module_code="crm",
        name="CRM",
        version="1.0.0",
        organisation_id=organisation_id,
    )

    assert module.organisation_id == organisation_id
