from uuid import uuid4

import pytest

from phoenix_core.ai.action_service import AIActionService
from phoenix_core.ai.contracts import AIActionRequest
from phoenix_core.security.context import RequestContext


def authorized_context():
    return RequestContext(
        request_id="proposal-test",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        permissions=frozenset({"ai.action"}),
        entitlements=frozenset({"ai"}),
    )


def test_authorized_proposal_is_returned_without_execution():
    service = AIActionService()

    action = AIActionRequest(
        action_type="create_production_order",
        parameters={"quantity": 25},
        target_type="production_order",
        target_id="PO-001",
    )

    result = service.authorize_proposal(
        authorized_context(),
        action,
        required_permission="ai.action",
        required_entitlement="ai",
    )

    assert result is action
    assert result.action_type == "create_production_order"
    assert result.parameters["quantity"] == 25


def test_unauthorized_proposal_is_rejected():
    service = AIActionService()

    context = RequestContext(
        request_id="proposal-test",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        permissions=frozenset(),
        entitlements=frozenset({"ai"}),
    )

    action = AIActionRequest(
        action_type="create_production_order",
    )

    with pytest.raises(PermissionError):
        service.authorize_proposal(
            context,
            action,
            required_permission="ai.action",
            required_entitlement="ai",
        )


def test_action_service_has_no_business_execution_authority():
    service = AIActionService()

    assert not hasattr(service, "execute")
    assert not hasattr(service, "execute_action")
    assert not hasattr(service, "execute_business_action")
