from uuid import uuid4

from phoenix_core.security.context import RequestContext
from phoenix_framework.context.framework import FrameworkContext
from phoenix_system.context.system import SystemContext
from phoenix_system.services.administration import SystemAdministrationService


def make_context(permissions=frozenset()):
    core_context = RequestContext(
        request_id="test-request",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        session_id=uuid4(),
        permissions=permissions,
        entitlements=frozenset(),
    )

    framework_context = FrameworkContext.from_core(core_context)
    return SystemContext.from_framework(framework_context)


def test_administration_access_requires_authentication_and_tenant():
    context = make_context()
    service = SystemAdministrationService(context)

    service.require_administration_access()


def test_company_management_permission():
    context = make_context(frozenset({"system.company.manage"}))
    service = SystemAdministrationService(context)

    assert service.can_manage_company() is True
    assert service.can_manage_users() is False


def test_user_and_membership_management_permissions():
    context = make_context(
        frozenset({
            "system.users.manage",
            "system.memberships.manage",
        })
    )
    service = SystemAdministrationService(context)

    assert service.can_manage_users() is True
    assert service.can_manage_memberships() is True


def test_role_and_module_management_permissions():
    context = make_context(
        frozenset({
            "system.roles.manage",
            "system.modules.manage",
        })
    )
    service = SystemAdministrationService(context)

    assert service.can_manage_roles() is True
    assert service.can_manage_modules() is True


def test_entitlement_and_configuration_management_permissions():
    context = make_context(
        frozenset({
            "system.entitlements.manage",
            "system.configuration.manage",
        })
    )
    service = SystemAdministrationService(context)

    assert service.can_manage_entitlements() is True
    assert service.can_manage_configuration() is True


def test_platform_management_permission():
    context = make_context(frozenset({"system.platform.manage"}))
    service = SystemAdministrationService(context)

    assert service.can_manage_platform() is True
    assert service.can_manage_configuration() is False


def test_unrelated_permissions_do_not_grant_administration_access():
    context = make_context(
        frozenset({
            "crm.users.manage",
            "sales.manage",
        })
    )
    service = SystemAdministrationService(context)

    assert service.can_manage_company() is False
    assert service.can_manage_users() is False
    assert service.can_manage_modules() is False
    assert service.can_manage_platform() is False
