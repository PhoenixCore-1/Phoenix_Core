from uuid import uuid4

import pytest

from phoenix_core.security.context import RequestContext


def test_request_context_supports_anonymous_context():
    context = RequestContext(request_id="req-001")

    assert context.request_id == "req-001"
    assert context.identity_id is None
    assert context.organisation_id is None
    assert context.session_id is None
    assert context.permissions == frozenset()
    assert context.entitlements == frozenset()


def test_request_context_supports_authenticated_context():
    identity_id = uuid4()
    organisation_id = uuid4()
    session_id = uuid4()

    context = RequestContext(
        request_id="req-002",
        identity_id=identity_id,
        organisation_id=organisation_id,
        session_id=session_id,
        permissions=frozenset({"documents.file.read"}),
        entitlements=frozenset({"documents"}),
    )

    assert context.identity_id == identity_id
    assert context.organisation_id == organisation_id
    assert context.session_id == session_id
    assert context.has_permission("documents.file.read")
    assert not context.has_permission("documents.file.delete")
    assert context.has_entitlement("documents")
    assert not context.has_entitlement("crm")


def test_request_context_is_immutable():
    context = RequestContext(request_id="req-003")

    with pytest.raises(AttributeError):
        context.request_id = "changed"
