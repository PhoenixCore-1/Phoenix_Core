from uuid import uuid4

from phoenix_system.contracts.entitlement import EntitlementAdministration


def test_entitlement_defaults():
    entitlement = EntitlementAdministration(
        entitlement_id=uuid4(),
        organisation_id=uuid4(),
        key="crm",
    )

    assert entitlement.active is False
    assert entitlement.administrable is False
    assert entitlement.can_administer_entitlement() is False


def test_entitlement_active():
    entitlement = EntitlementAdministration(
        entitlement_id=uuid4(),
        organisation_id=uuid4(),
        key="crm",
        enabled=True,
    )

    assert entitlement.active is True


def test_entitlement_disabled():
    entitlement = EntitlementAdministration(
        entitlement_id=uuid4(),
        organisation_id=uuid4(),
        key="crm",
        enabled=False,
    )

    assert entitlement.active is False


def test_entitlement_administration():
    entitlement = EntitlementAdministration(
        entitlement_id=uuid4(),
        organisation_id=uuid4(),
        key="crm",
        can_manage_entitlement=True,
    )

    assert entitlement.administrable is True
    assert entitlement.can_administer_entitlement() is True


def test_entitlement_requires_administration_permission():
    entitlement = EntitlementAdministration(
        entitlement_id=uuid4(),
        organisation_id=uuid4(),
        key="crm",
        enabled=True,
        can_manage_entitlement=False,
    )

    assert entitlement.active is True
    assert entitlement.administrable is False
    assert entitlement.can_administer_entitlement() is False


def test_entitlement_is_tenant_bound():
    organisation_id = uuid4()

    entitlement = EntitlementAdministration(
        entitlement_id=uuid4(),
        organisation_id=organisation_id,
        key="crm",
    )

    assert entitlement.organisation_id == organisation_id
