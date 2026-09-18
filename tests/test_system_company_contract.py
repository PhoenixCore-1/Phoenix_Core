from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from phoenix_system.contracts import CompanyAdministration, CompanyStatus


def test_company_administration_contains_core_organisation_identity():
    organisation_id = uuid4()

    company = CompanyAdministration(
        organisation_id=organisation_id,
        name="Example Company",
        status=CompanyStatus.ACTIVE,
    )

    assert company.organisation_id == organisation_id
    assert company.name == "Example Company"
    assert company.status == CompanyStatus.ACTIVE
    assert company.active


def test_company_administration_supports_administrative_capabilities():
    company = CompanyAdministration(
        organisation_id=uuid4(),
        name="Example Company",
        status=CompanyStatus.ACTIVE,
        can_manage_users=True,
        can_manage_modules=True,
        can_manage_configuration=True,
    )

    assert company.can_manage_users
    assert company.can_manage_modules
    assert company.can_manage_configuration
    assert company.administration_enabled


def test_inactive_company_is_not_administration_enabled():
    company = CompanyAdministration(
        organisation_id=uuid4(),
        name="Suspended Company",
        status=CompanyStatus.SUSPENDED,
        can_manage_users=True,
    )

    assert not company.active
    assert not company.administration_enabled


def test_closed_company_is_not_active():
    company = CompanyAdministration(
        organisation_id=uuid4(),
        name="Closed Company",
        status=CompanyStatus.CLOSED,
    )

    assert not company.active
    assert not company.administration_enabled


def test_company_administration_is_immutable():
    company = CompanyAdministration(
        organisation_id=uuid4(),
        name="Example Company",
        status=CompanyStatus.ACTIVE,
    )

    with pytest.raises(FrozenInstanceError):
        company.name = "Changed"


def test_company_administration_supports_metadata():
    company = CompanyAdministration(
        organisation_id=uuid4(),
        name="Example Company",
        status=CompanyStatus.ACTIVE,
        metadata={"region": "ZA", "type": "customer"},
    )

    assert company.metadata["region"] == "ZA"
    assert company.metadata["type"] == "customer"
