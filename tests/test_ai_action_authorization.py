from uuid import uuid4

import pytest

from phoenix_core.ai.action_authorization import AIActionAuthorizationService
from phoenix_core.ai.contracts import AIActionRequest
from phoenix_core.security.context import RequestContext


def authorized_context():
    return RequestContext(
        request_id="action-test",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        permissions=frozenset({"ai.action"}),
        entitlements=frozenset({"ai"}),
    )


def test_authorized_ai_action_is_accepted():
    service = AIActionAuthorizationService()

    action = AIActionRequest(
        action_type="create_production_order",
        parameters={"quantity": 10},
        target_type="production_order",
    )

    service.authorize(
        authorized_context(),
        action,
        required_permission="ai.action",
        required_entitlement="ai",
    )


def test_action_requires_permission():
    service = AIActionAuthorizationService()

    context = RequestContext(
        request_id="action-test",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        permissions=frozenset(),
        entitlements=frozenset({"ai"}),
    )

    action = AIActionRequest(
        action_type="create_production_order",
    )

    with pytest.raises(PermissionError, match="AI action permission"):
        service.authorize(
            context,
            action,
            required_permission="ai.action",
            required_entitlement="ai",
        )


def test_action_requires_entitlement():
    service = AIActionAuthorizationService()

    context = RequestContext(
        request_id="action-test",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        permissions=frozenset({"ai.action"}),
        entitlements=frozenset(),
    )

    action = AIActionRequest(
        action_type="create_production_order",
    )

    with pytest.raises(PermissionError, match="AI action entitlement"):
        service.authorize(
            context,
            action,
            required_permission="ai.action",
            required_entitlement="ai",
        )


def test_action_requires_tenant_context():
    service = AIActionAuthorizationService()

    context = RequestContext(
        request_id="action-test",
        identity_id=uuid4(),
        organisation_id=None,
        permissions=frozenset({"ai.action"}),
        entitlements=frozenset({"ai"}),
    )

    action = AIActionRequest(
        action_type="create_production_order",
    )

    with pytest.raises(PermissionError, match="Organisation context"):
        service.authorize(
            context,
            action,
            required_permission="ai.action",
            required_entitlement="ai",
        )


def test_empty_action_type_is_rejected():
    service = AIActionAuthorizationService()

    action = AIActionRequest(action_type="")

    with pytest.raises(ValueError, match="AI action type"):
        service.authorize(
            authorized_context(),
            action,
            required_permission="ai.action",
            required_entitlement="ai",
        )
