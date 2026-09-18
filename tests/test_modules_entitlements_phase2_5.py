import pytest
from uuid import UUID

from phoenix_core.errors import AuthorizationError, ConflictError, NotFoundError, ValidationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.services import CoreFoundationService


def make_service(tmp_path):
    db = SQLiteDatabase(tmp_path / "test.db")
    service = CoreFoundationService(db)
    service.initialise()
    return db, service


def setup_org(service):
    return service.create_organisation("ACME", "Acme")


def test_module_registration_lookup_and_lifecycle(tmp_path):
    db, service = make_service(tmp_path)
    module = service.register_module("CRM", "CRM", "1.0.0")
    assert module.code == "crm"
    assert service.get_module(module.id).id == module.id
    assert service.get_module_by_code("CRM").id == module.id
    assert service.enable_module(module.id).status == "ENABLED"
    assert service.disable_module(module.id).status == "DISABLED"
    assert service.enable_module(module.id).status == "ENABLED"
    assert service.retire_module(module.id).status == "RETIRED"
    with pytest.raises(ValidationError):
        service.enable_module(module.id)
    db.close()


def test_duplicate_module_code_rejected(tmp_path):
    db, service = make_service(tmp_path)
    service.register_module("CRM", "CRM", "1.0.0")
    with pytest.raises(ConflictError):
        service.register_module("crm", "Another CRM", "2.0.0")
    db.close()


def test_retired_module_cannot_be_entitled(tmp_path):
    db, service = make_service(tmp_path)
    org = setup_org(service)
    module = service.register_module("CRM", "CRM", "1.0.0")
    service.retire_module(module.id)
    with pytest.raises(ValidationError):
        service.grant_module_entitlement(org.id, module.id)
    db.close()


def test_entitlement_grant_requires_active_org_and_module(tmp_path):
    db, service = make_service(tmp_path)
    org = setup_org(service)
    module = service.register_module("CRM", "CRM", "1.0.0")
    entitlement = service.grant_module_entitlement(org.id, module.id)
    assert entitlement.status == "ACTIVE"
    with pytest.raises(ConflictError):
        service.grant_module_entitlement(org.id, module.id)
    service.suspend_organisation(org.id)
    module2 = service.register_module("ERP", "ERP", "1.0.0")
    with pytest.raises(AuthorizationError):
        service.grant_module_entitlement(org.id, module2.id)
    db.close()


def test_entitlement_lifecycle_and_module_availability(tmp_path):
    db, service = make_service(tmp_path)
    org = setup_org(service)
    module = service.register_module("CRM", "CRM", "1.0.0")
    assert not service.module_available(org.id, module.id)
    entitlement = service.grant_module_entitlement(org.id, module.id)
    assert not service.module_available(org.id, module.id)
    service.enable_module(module.id)
    assert service.module_available(org.id, module.id)
    service.suspend_module_entitlement(entitlement.id)
    assert not service.module_available(org.id, module.id)
    service.activate_module_entitlement(entitlement.id)
    assert service.module_available(org.id, module.id)
    service.revoke_module_entitlement(entitlement.id)
    assert not service.module_available(org.id, module.id)
    with pytest.raises(ValidationError):
        service.activate_module_entitlement(entitlement.id)
    db.close()


def test_entitlement_cannot_cross_tenant(tmp_path):
    db, service = make_service(tmp_path)
    org1 = service.create_organisation("ONE", "One")
    org2 = service.create_organisation("TWO", "Two")
    module = service.register_module("CRM", "CRM", "1.0.0")
    entitlement = service.grant_module_entitlement(org1.id, module.id)
    assert service.get_module_entitlement(entitlement.id).organisation_id == org1.id
    assert service.module_available(org2.id, module.id) is False
    db.close()


def test_effective_capability_requires_permission_and_entitlement(tmp_path):
    db, service = make_service(tmp_path)
    org = setup_org(service)
    user = service.create_user("alice", "Alice", "StrongPass123!")
    membership = service.add_membership(user.identity_id, org.id)
    role = service.create_role(org.id, "sales", "Sales")
    permission = service.create_permission("crm.customer.read", "Read CRM customers")
    service.assign_role(membership.id, role.id)
    service.grant_permission(role.id, permission.id)
    module = service.register_module("CRM", "CRM", "1.0.0")
    assert not service.has_capability(user.identity_id, org.id, "crm.customer.read", module.id)
    service.grant_module_entitlement(org.id, module.id)
    assert not service.has_capability(user.identity_id, org.id, "crm.customer.read", module.id)
    service.enable_module(module.id)
    assert service.has_capability(user.identity_id, org.id, "crm.customer.read", module.id)
    db.close()


def test_effective_capability_denied_for_other_tenant(tmp_path):
    db, service = make_service(tmp_path)
    org1 = service.create_organisation("ONE", "One")
    org2 = service.create_organisation("TWO", "Two")
    user = service.create_user("alice", "Alice", "StrongPass123!")
    membership = service.add_membership(user.identity_id, org1.id)
    role = service.create_role(org1.id, "sales", "Sales")
    permission = service.create_permission("crm.customer.read", "Read CRM customers")
    service.assign_role(membership.id, role.id)
    service.grant_permission(role.id, permission.id)
    module = service.register_module("CRM", "CRM", "1.0.0")
    service.grant_module_entitlement(org2.id, module.id)
    service.enable_module(module.id)
    assert not service.has_capability(user.identity_id, org2.id, "crm.customer.read", module.id)
    db.close()
