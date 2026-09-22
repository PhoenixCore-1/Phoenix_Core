import pytest
from phoenix_core.api.application import CoreApi
from phoenix_core.errors import AuthorizationError, ConflictError, ValidationError
from phoenix_core.infrastructure import SQLiteDatabase


def make_services(tmp_path):
    db = SQLiteDatabase(tmp_path / "test.db")
    db.initialise_schema()
    api = CoreApi(db)
    return (
        db,
        api.organisation_service,
        api.user_service,
        api.company_membership_service,
        api.role_service,
        api.authorization_service,
    )


def setup_org_user(organisations, users, memberships):
    org = organisations.create_organisation("ACME", "Acme")
    user = users.create_user(
        username="alice",
        display_name="Alice",
        password="StrongPass123!",
    )
    membership = memberships.add_membership(user.identity_id, org.id)
    return org, user, membership


def test_role_can_be_read_updated_listed_and_disabled(tmp_path):
    db, organisations, users, memberships, roles, authorization = make_services(tmp_path)
    org, _, _ = setup_org_user(organisations, users, memberships)

    role = roles.create_role(org.id, "sales", "Sales")

    assert roles.get_role(role.id).code == "SALES"
    assert roles.list_roles(org.id)[0].id == role.id

    updated = roles.update_role(role.id, name="Sales Manager")
    assert updated.name == "Sales Manager"

    assert roles.disable_role(role.id).status == "DISABLED"
    assert roles.enable_role(role.id).status == "ACTIVE"

    db.close()


def test_duplicate_role_code_is_rejected_per_organisation(tmp_path):
    db, organisations, users, memberships, roles, authorization = make_services(tmp_path)
    org, _, _ = setup_org_user(organisations, users, memberships)

    roles.create_role(org.id, "admin", "Admin")

    with pytest.raises(ConflictError):
        roles.create_role(org.id, "ADMIN", "Another Admin")

    db.close()


def test_same_role_code_is_allowed_in_different_organisations(tmp_path):
    db, organisations, _, _, roles, _ = make_services(tmp_path)

    org1 = organisations.create_organisation("ONE", "One")
    org2 = organisations.create_organisation("TWO", "Two")

    r1 = roles.create_role(org1.id, "admin", "Admin")
    r2 = roles.create_role(org2.id, "admin", "Admin")

    assert r1.id != r2.id

    db.close()


def test_permission_lifecycle_and_global_uniqueness(tmp_path):
    db, _, _, _, roles, _ = make_services(tmp_path)

    permission = roles.create_permission(
        "sales.quote.create",
        "Create quotes",
    )

    assert (
        roles.get_permission_by_code("SALES.QUOTE.CREATE").id
        == permission.id
    )

    permissions = roles.list_permissions()
    assert any(item.id == permission.id for item in permissions)

    with pytest.raises(ConflictError):
        roles.create_permission(
            "sales.quote.create",
            "Duplicate",
        )

    updated = roles.update_permission(
        permission.id,
        name="Create sales quotes",
    )
    assert updated.name == "Create sales quotes"

    db.close()


def test_role_permission_grant_revoke_and_effective_authorization(tmp_path):
    db, organisations, users, memberships, roles, authorization = make_services(tmp_path)
    org, user, membership = setup_org_user(
        organisations,
        users,
        memberships,
    )

    role = roles.create_role(org.id, "sales", "Sales")
    permission = roles.create_permission(
        "sales.quote.create",
        "Create quotes",
    )

    roles.assign_role(membership.id, role.id)
    roles.grant_permission(role.id, permission.id)

    assert [
        p.code for p in roles.list_role_permissions(role.id)
    ] == ["sales.quote.create"]

    assert authorization.authorize(
        user.identity_id,
        org.id,
        "sales.quote.create",
    )

    assert not authorization.authorize(
        user.identity_id,
        org.id,
        "sales.quote.delete",
    )

    assert roles.revoke_permission(role.id, permission.id)

    assert not authorization.authorize(
        user.identity_id,
        org.id,
        "sales.quote.create",
    )

    db.close()


def test_duplicate_permission_grant_is_rejected(tmp_path):
    db, organisations, users, memberships, roles, authorization = make_services(tmp_path)
    org, _, membership = setup_org_user(
        organisations,
        users,
        memberships,
    )

    role = roles.create_role(org.id, "sales", "Sales")
    permission = roles.create_permission(
        "sales.quote.create",
        "Create quotes",
    )

    roles.assign_role(membership.id, role.id)
    roles.grant_permission(role.id, permission.id)

    with pytest.raises(ConflictError):
        roles.grant_permission(role.id, permission.id)

    db.close()


def test_cross_tenant_role_assignment_is_rejected(tmp_path):
    db, organisations, users, memberships, roles, authorization = make_services(tmp_path)
    org1, _, membership = setup_org_user(
        organisations,
        users,
        memberships,
    )

    org2 = organisations.create_organisation("TWO", "Two")
    role = roles.create_role(org2.id, "sales", "Sales")

    with pytest.raises(AuthorizationError):
        roles.assign_role(membership.id, role.id)

    db.close()


def test_disabled_role_cannot_provide_permissions(tmp_path):
    db, organisations, users, memberships, roles, authorization = make_services(tmp_path)
    org, user, membership = setup_org_user(
        organisations,
        users,
        memberships,
    )

    role = roles.create_role(org.id, "sales", "Sales")
    permission = roles.create_permission(
        "sales.quote.create",
        "Create quotes",
    )

    roles.assign_role(membership.id, role.id)
    roles.grant_permission(role.id, permission.id)

    assert authorization.authorize(
        user.identity_id,
        org.id,
        "sales.quote.create",
    )

    roles.disable_role(role.id)

    assert not authorization.authorize(
        user.identity_id,
        org.id,
        "sales.quote.create",
    )

    db.close()


def test_role_assignment_can_be_removed(tmp_path):
    db, organisations, users, memberships, roles, authorization = make_services(tmp_path)
    org, user, membership = setup_org_user(
        organisations,
        users,
        memberships,
    )

    role = roles.create_role(org.id, "sales", "Sales")
    permission = roles.create_permission(
        "sales.quote.create",
        "Create quotes",
    )

    roles.assign_role(membership.id, role.id)
    roles.grant_permission(role.id, permission.id)

    assert authorization.authorize(
        user.identity_id,
        org.id,
        "sales.quote.create",
    )

    assert roles.remove_role(membership.id, role.id)

    assert not authorization.authorize(
        user.identity_id,
        org.id,
        "sales.quote.create",
    )

    db.close()


def test_system_roles_are_not_created_through_tenant_role_service(tmp_path):
    db, organisations, users, memberships, roles, authorization = make_services(tmp_path)
    org, _, _ = setup_org_user(
        organisations,
        users,
        memberships,
    )

    with pytest.raises(ValidationError):
        roles.create_role(
            org.id,
            "system-admin",
            "System Admin",
            scope="SYSTEM",
        )

    db.close()
