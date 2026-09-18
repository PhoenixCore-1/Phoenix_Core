from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from phoenix_core.security.context import RequestContext
from phoenix_framework.context import FrameworkContext
from phoenix_system.context import SystemContext


def make_framework_context(
    permissions=(),
    entitlements=(),
):
    core_context = RequestContext(
        request_id="req-system-001",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        session_id=uuid4(),
        permissions=frozenset(permissions),
        entitlements=frozenset(entitlements),
    )

    return FrameworkContext.from_core(core_context)


def test_system_context_derives_from_framework_context():
    framework_context = make_framework_context(
        permissions=("system.company.view",),
        entitlements=("system",),
    )

    context = SystemContext.from_framework(framework_context)

    assert context.request_id == framework_context.request_id
    assert context.identity_id == framework_context.identity_id
    assert context.organisation_id == framework_context.organisation_id
    assert context.permissions == framework_context.permissions
    assert context.entitlements == framework_context.entitlements


def test_system_context_is_immutable():
    context = SystemContext(
        request_id="req-system-002",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        session_id=None,
        permissions=frozenset(),
        entitlements=frozenset(),
    )

    with pytest.raises(FrozenInstanceError):
        context.request_id = "changed"


def test_system_context_permission_checks():
    context = SystemContext(
        request_id="req-system-003",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        session_id=None,
        permissions=frozenset({"system.users.view"}),
        entitlements=frozenset(),
    )

    assert context.has_permission("system.users.view")
    assert not context.has_permission("system.users.edit")

    context.require_permission("system.users.view")

    with pytest.raises(PermissionError):
        context.require_permission("system.users.edit")


def test_system_context_entitlement_checks():
    context = SystemContext(
        request_id="req-system-004",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        session_id=None,
        permissions=frozenset(),
        entitlements=frozenset({"system"}),
    )

    assert context.has_entitlement("system")
    assert not context.has_entitlement("other")

    context.require_entitlement("system")

    with pytest.raises(PermissionError):
        context.require_entitlement("other")


def test_system_context_rejects_unauthenticated_framework_context():
    framework_context = FrameworkContext(
        request_id="req-system-005",
        identity_id=None,
        organisation_id=None,
        session_id=None,
        permissions=frozenset(),
        entitlements=frozenset(),
    )

    with pytest.raises(PermissionError):
        SystemContext.from_framework(framework_context)


def test_system_context_rejects_missing_tenant_context():
    framework_context = FrameworkContext(
        request_id="req-system-006",
        identity_id=uuid4(),
        organisation_id=None,
        session_id=None,
        permissions=frozenset(),
        entitlements=frozenset(),
    )

    with pytest.raises(PermissionError):
        SystemContext.from_framework(framework_context)
