from uuid import uuid4

from phoenix_system.contracts.role import RoleAdministration


def test_role_defaults():
    role = RoleAdministration(
        role_id=uuid4(),
        organisation_id=uuid4(),
        name="Administrator",
    )

    assert role.administrable is False
    assert role.assignable is False
    assert role.can_administer_role() is False


def test_role_permission_check():
    role = RoleAdministration(
        role_id=uuid4(),
        organisation_id=uuid4(),
        name="Administrator",
        permissions=frozenset({"users.view", "users.manage"}),
    )

    assert role.has_permission("users.view") is True
    assert role.has_permission("users.manage") is True
    assert role.has_permission("billing.manage") is False


def test_role_management():
    role = RoleAdministration(
        role_id=uuid4(),
        organisation_id=uuid4(),
        name="Manager",
        can_manage_role=True,
    )

    assert role.administrable is True
    assert role.assignable is False
    assert role.can_administer_role() is True


def test_role_assignment():
    role = RoleAdministration(
        role_id=uuid4(),
        organisation_id=uuid4(),
        name="Manager",
        can_assign_role=True,
    )

    assert role.administrable is False
    assert role.assignable is True
    assert role.can_administer_role() is True


def test_role_management_and_assignment():
    role = RoleAdministration(
        role_id=uuid4(),
        organisation_id=uuid4(),
        name="Administrator",
        can_manage_role=True,
        can_assign_role=True,
    )

    assert role.administrable is True
    assert role.assignable is True
    assert role.can_administer_role() is True


def test_role_is_tenant_bound():
    organisation_id = uuid4()

    role = RoleAdministration(
        role_id=uuid4(),
        organisation_id=organisation_id,
        name="Administrator",
    )

    assert role.organisation_id == organisation_id
