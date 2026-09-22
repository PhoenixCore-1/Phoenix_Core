import pytest
from phoenix_core.errors import AuthorizationError, ConflictError, ValidationError

from phoenix_core.api.application import CoreApi
from phoenix_core.infrastructure import SQLiteDatabase


def make_services(tmp_path):
    db = SQLiteDatabase(tmp_path / "test.db")
    api = CoreApi(db)
    db.initialise_schema()
    return db, api


def setup_org(api):
    return api.organisation_service.create_organisation("ACME", "Acme")


def test_module_registration_lookup_and_lifecycle(tmp_path):
    db, api = make_services(tmp_path)
    modules = api.module_service

    module = modules.register("CRM", "CRM", "1.0.0")
    assert module.code == "crm"
    assert modules.get(module.id).id == module.id
    assert modules.get_by_code("CRM").id == module.id
    assert modules.enable(module.id).status == "ENABLED"
    assert modules.disable(module.id).status == "DISABLED"
    assert modules.enable(module.id).status == "ENABLED"
    assert modules.retire(module.id).status == "RETIRED"

    with pytest.raises(ValidationError):
        modules.enable(module.id)

    db.close()


def test_duplicate_module_code_rejected(tmp_path):
    db, api = make_services(tmp_path)
    modules = api.module_service

    modules.register("CRM", "CRM", "1.0.0")

    with pytest.raises(ConflictError):
        modules.register("crm", "Another CRM", "2.0.0")

    db.close()


def test_retired_module_cannot_be_entitled(tmp_path):
    db, api = make_services(tmp_path)
    org = setup_org(api)
    modules = api.module_service
    entitlements = api.entitlement_service

    module = modules.register("CRM", "CRM", "1.0.0")
    modules.retire(module.id)

    with pytest.raises(ValidationError):
        entitlements.grant(org.id, module.id)

    db.close()


def test_entitlement_grant_requires_active_org_and_module(tmp_path):
    db, api = make_services(tmp_path)
    org = setup_org(api)
    modules = api.module_service
    entitlements = api.entitlement_service
    organisations = api.organisation_service

    module = modules.register("CRM", "CRM", "1.0.0")
    entitlement = entitlements.grant(org.id, module.id)

    assert entitlement.status == "ACTIVE"

    with pytest.raises(ConflictError):
        entitlements.grant(org.id, module.id)

    organisations.suspend_organisation(org.id)

    module2 = modules.register("ERP", "ERP", "1.0.0")

    with pytest.raises(AuthorizationError):
        entitlements.grant(org.id, module2.id)

    db.close()


def test_entitlement_lifecycle_and_module_availability(tmp_path):
    db, api = make_services(tmp_path)
    org = setup_org(api)
    modules = api.module_service
    entitlements = api.entitlement_service

    module = modules.register("CRM", "CRM", "1.0.0")

    assert not entitlements.is_module_available(org.id, module.id)

    entitlement = entitlements.grant(org.id, module.id)

    assert not entitlements.is_module_available(org.id, module.id)

    modules.enable(module.id)

    assert entitlements.is_module_available(org.id, module.id)

    entitlements.suspend(entitlement.id)

    assert not entitlements.is_module_available(org.id, module.id)

    entitlements.activate(entitlement.id)

    assert entitlements.is_module_available(org.id, module.id)

    entitlements.revoke(entitlement.id)

    assert not entitlements.is_module_available(org.id, module.id)

    with pytest.raises(ValidationError):
        entitlements.activate(entitlement.id)

    db.close()


def test_entitlement_cannot_cross_tenant(tmp_path):
    db, api = make_services(tmp_path)
    organisations = api.organisation_service
    modules = api.module_service
    entitlements = api.entitlement_service

    org1 = organisations.create_organisation("ONE", "One")
    org2 = organisations.create_organisation("TWO", "Two")
    module = modules.register("CRM", "CRM", "1.0.0")

    entitlement = entitlements.grant(org1.id, module.id)

    assert entitlements.get(entitlement.id).organisation_id == org1.id
    assert entitlements.is_module_available(org2.id, module.id) is False

    db.close()


def test_effective_capability_requires_permission_and_entitlement(tmp_path):
    db, api = make_services(tmp_path)
    org = setup_org(api)

    user = api.user_service.create_user(
        username="alice",
        display_name="Alice",
        password="StrongPass123!",
    )

    membership = api.company_membership_service.add_membership(
        user.identity_id,
        org.id,
    )

    role = api.role_service.create_role(org.id, "sales", "Sales")
    permission = api.role_service.create_permission(
        "crm.customer.read",
        "Read CRM customers",
    )

    api.role_service.assign_role(membership.id, role.id)
    api.role_service.grant_permission(role.id, permission.id)

    module = api.module_service.register("CRM", "CRM", "1.0.0")

    assert not api.authorization_service.has_capability(
        user.identity_id,
        org.id,
        "crm.customer.read",
        module.id,
    )

    api.entitlement_service.grant(org.id, module.id)

    assert not api.authorization_service.has_capability(
        user.identity_id,
        org.id,
        "crm.customer.read",
        module.id,
    )

    api.module_service.enable(module.id)

    assert api.authorization_service.has_capability(
        user.identity_id,
        org.id,
        "crm.customer.read",
        module.id,
    )

    db.close()


def test_effective_capability_denied_for_other_tenant(tmp_path):
    db, api = make_services(tmp_path)
    organisations = api.organisation_service

    org1 = organisations.create_organisation("ONE", "One")
    org2 = organisations.create_organisation("TWO", "Two")

    user = api.user_service.create_user(
        username="alice",
        display_name="Alice",
        password="StrongPass123!",
    )

    membership = api.company_membership_service.add_membership(
        user.identity_id,
        org1.id,
    )

    role = api.role_service.create_role(org1.id, "sales", "Sales")
    permission = api.role_service.create_permission(
        "crm.customer.read",
        "Read CRM customers",
    )

    api.role_service.assign_role(membership.id, role.id)
    api.role_service.grant_permission(role.id, permission.id)

    module = api.module_service.register("CRM", "CRM", "1.0.0")

    api.entitlement_service.grant(org2.id, module.id)
    api.module_service.enable(module.id)

    assert not api.authorization_service.has_capability(
        user.identity_id,
        org2.id,
        "crm.customer.read",
        module.id,
    )

    db.close()
