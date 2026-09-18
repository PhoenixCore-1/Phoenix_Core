from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from phoenix_core.security.context import RequestContext
from phoenix_framework.context import FrameworkContext


def test_framework_context_maps_authoritative_core_context():
    identity_id = uuid4()
    organisation_id = uuid4()
    session_id = uuid4()

    core_context = RequestContext(
        request_id="req-001",
        identity_id=identity_id,
        organisation_id=organisation_id,
        session_id=session_id,
        permissions=frozenset({"users.view"}),
        entitlements=frozenset({"system"}),
    )

    context = FrameworkContext.from_core(core_context)

    assert context.request_id == "req-001"
    assert context.identity_id == identity_id
    assert context.organisation_id == organisation_id
    assert context.session_id == session_id
    assert context.has_permission("users.view")
    assert context.has_entitlement("system")


def test_framework_context_is_immutable():
    context = FrameworkContext(
        request_id="req-002",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        session_id=None,
        permissions=frozenset(),
        entitlements=frozenset(),
    )

    with pytest.raises(FrozenInstanceError):
        context.request_id = "changed"


def test_framework_context_authentication_and_tenant_state():
    unauthenticated = FrameworkContext(
        request_id="req-003",
        identity_id=None,
        organisation_id=None,
        session_id=None,
        permissions=frozenset(),
        entitlements=frozenset(),
    )

    assert not unauthenticated.authenticated
    assert not unauthenticated.tenant_bound

    authenticated = FrameworkContext(
        request_id="req-004",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        session_id=None,
        permissions=frozenset(),
        entitlements=frozenset(),
    )

    assert authenticated.authenticated
    assert authenticated.tenant_bound


def test_framework_context_requires_authentication():
    context = FrameworkContext(
        request_id="req-005",
        identity_id=None,
        organisation_id=None,
        session_id=None,
        permissions=frozenset(),
        entitlements=frozenset(),
    )

    with pytest.raises(PermissionError):
        context.require_authenticated()


def test_framework_context_requires_tenant():
    context = FrameworkContext(
        request_id="req-006",
        identity_id=uuid4(),
        organisation_id=None,
        session_id=None,
        permissions=frozenset(),
        entitlements=frozenset(),
    )

    with pytest.raises(PermissionError):
        context.require_tenant()


def test_framework_context_preserves_core_security_values():
    core_context = RequestContext(
        request_id="req-007",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        permissions=frozenset({"a", "b"}),
        entitlements=frozenset({"x", "y"}),
    )

    context = FrameworkContext.from_core(core_context)

    assert context.permissions == frozenset({"a", "b"})
    assert context.entitlements == frozenset({"x", "y"})
