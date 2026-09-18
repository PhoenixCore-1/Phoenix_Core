import pytest
from phoenix_core.errors import AuthorizationError, ConflictError, NotFoundError, ValidationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.services import CoreFoundationService

def make_service(tmp_path):
    db = SQLiteDatabase(tmp_path / "test.db")
    service = CoreFoundationService(db)
    service.initialise()
    return db, service

def setup_org_user(service):
    org = service.create_organisation("ACME", "Acme")
    user = service.create_user("alice", "Alice", "StrongPass123!")
    membership = service.add_membership(user.identity_id, org.id)
    return org, user, membership

def test_role_can_be_read_updated_listed_and_disabled(tmp_path):
    db, service = make_service(tmp_path)
    org, _, _ = setup_org_user(service)
    role = service.create_role(org.id, "sales", "Sales")
    assert service.get_role(role.id).code == "SALES"
    assert service.list_roles(org.id)[0].id == role.id
    updated = service.update_role(role.id, name="Sales Manager")
    assert updated.name == "Sales Manager"
    assert service.disable_role(role.id).status == "DISABLED"
    assert service.enable_role(role.id).status == "ACTIVE"
    db.close()

def test_duplicate_role_code_is_rejected_per_organisation(tmp_path):
    db, service = make_service(tmp_path)
    org, _, _ = setup_org_user(service)
    service.create_role(org.id, "admin", "Admin")
    with pytest.raises(ConflictError):
        service.create_role(org.id, "ADMIN", "Another Admin")
    db.close()

def test_same_role_code_is_allowed_in_different_organisations(tmp_path):
    db, service = make_service(tmp_path)
    org1 = service.create_organisation("ONE", "One")
    org2 = service.create_organisation("TWO", "Two")
    r1 = service.create_role(org1.id, "admin", "Admin")
    r2 = service.create_role(org2.id, "admin", "Admin")
    assert r1.id != r2.id
    db.close()

def test_permission_lifecycle_and_global_uniqueness(tmp_path):
    db, service = make_service(tmp_path)
    p = service.create_permission("sales.quote.create", "Create quotes")
    assert service.get_permission_by_code("SALES.QUOTE.CREATE").id == p.id
    permissions = service.list_permissions()
    assert any(permission.id == p.id for permission in permissions)
    with pytest.raises(ConflictError):
        service.create_permission("sales.quote.create", "Duplicate")
    updated = service.update_permission(p.id, name="Create sales quotes")
    assert updated.name == "Create sales quotes"
    db.close()

def test_role_permission_grant_revoke_and_effective_authorization(tmp_path):
    db, service = make_service(tmp_path)
    org, user, membership = setup_org_user(service)
    role = service.create_role(org.id, "sales", "Sales")
    permission = service.create_permission("sales.quote.create", "Create quotes")
    service.assign_role(membership.id, role.id)
    service.grant_permission(role.id, permission.id)
    assert [p.code for p in service.list_role_permissions(role.id)] == ["sales.quote.create"]
    assert service.authorize(user.identity_id, org.id, "sales.quote.create")
    assert not service.authorize(user.identity_id, org.id, "sales.quote.delete")
    assert service.revoke_permission(role.id, permission.id)
    assert not service.authorize(user.identity_id, org.id, "sales.quote.create")
    db.close()

def test_duplicate_permission_grant_is_rejected(tmp_path):
    db, service = make_service(tmp_path)
    org, _, _ = setup_org_user(service)
    role = service.create_role(org.id, "sales", "Sales")
    permission = service.create_permission("sales.quote.create", "Create quotes")
    service.grant_permission(role.id, permission.id)
    with pytest.raises(ConflictError):
        service.grant_permission(role.id, permission.id)
    db.close()

def test_cross_tenant_role_assignment_is_rejected(tmp_path):
    db, service = make_service(tmp_path)
    org1, _, membership = setup_org_user(service)
    org2 = service.create_organisation("TWO", "Two")
    role = service.create_role(org2.id, "sales", "Sales")
    with pytest.raises(AuthorizationError):
        service.assign_role(membership.id, role.id)
    db.close()

def test_disabled_role_cannot_provide_permissions(tmp_path):
    db, service = make_service(tmp_path)
    org, user, membership = setup_org_user(service)
    role = service.create_role(org.id, "sales", "Sales")
    permission = service.create_permission("sales.quote.create", "Create quotes")
    service.assign_role(membership.id, role.id)
    service.grant_permission(role.id, permission.id)
    assert service.authorize(user.identity_id, org.id, "sales.quote.create")
    service.disable_role(role.id)
    assert not service.authorize(user.identity_id, org.id, "sales.quote.create")
    db.close()

def test_role_assignment_can_be_removed(tmp_path):
    db, service = make_service(tmp_path)
    org, user, membership = setup_org_user(service)
    role = service.create_role(org.id, "sales", "Sales")
    permission = service.create_permission("sales.quote.create", "Create quotes")
    service.assign_role(membership.id, role.id)
    service.grant_permission(role.id, permission.id)
    assert service.authorize(user.identity_id, org.id, "sales.quote.create")
    assert service.remove_role(membership.id, role.id)
    assert not service.authorize(user.identity_id, org.id, "sales.quote.create")
    db.close()

def test_system_roles_are_not_created_through_tenant_role_service(tmp_path):
    db, service = make_service(tmp_path)
    org, _, _ = setup_org_user(service)
    with pytest.raises(ValidationError):
        service.create_role(org.id, "system-admin", "System Admin", scope="SYSTEM")
    db.close()
