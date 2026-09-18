from uuid import uuid4

import pytest

from phoenix_core.errors import ValidationError
from phoenix_core.organization import (
    AccessScope,
    Assignment,
    AssignmentType,
    OrganizationUnit,
    OrganizationUnitType,
)


def test_create_region():
    org_id = uuid4()
    region = OrganizationUnit.create(org_id, "Gauteng", OrganizationUnitType.REGION)
    assert region.organization_id == org_id
    assert region.unit_type is OrganizationUnitType.REGION
    assert region.active is True


def test_organization_cannot_have_parent():
    with pytest.raises(ValidationError):
        OrganizationUnit.create(
            uuid4(), "Acme", OrganizationUnitType.ORGANIZATION, parent_id=uuid4()
        )


def test_assignment_defaults_to_primary():
    assignment = Assignment.create(uuid4(), uuid4(), uuid4(), uuid4())
    assert assignment.assignment_type is AssignmentType.PRIMARY
    assert assignment.active is True


def test_access_scope_checks_explicit_resource():
    resource_id = uuid4()
    scope = AccessScope(uuid4(), frozenset(), frozenset(), frozenset({resource_id}))
    assert scope.can_access_resource(resource_id)
    assert not scope.can_access_resource(uuid4())
