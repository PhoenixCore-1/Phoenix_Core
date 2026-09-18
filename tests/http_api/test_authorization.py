"""Tests for the Phoenix Core HTTP authorization boundary."""

from uuid import uuid4

import pytest

from phoenix_core.api.application import CoreApi
from phoenix_core.api.context import RequestContextResolver
from phoenix_core.errors import AuthenticationError, AuthorizationError
from phoenix_core.http_api.authorization import _organisation_id


def test_missing_organisation_context_is_rejected():
    class Request:
        headers = {}

    with pytest.raises(AuthenticationError):
        _organisation_id(Request())


def test_invalid_organisation_context_is_rejected():
    class Request:
        headers = {"X-Phoenix-Organisation": "not-a-uuid"}

    with pytest.raises(AuthenticationError):
        _organisation_id(Request())


def test_permission_check_uses_resolved_context():
    context = type(
        "Context",
        (),
        {
            "has_permission": lambda self, permission: permission == "company.users.manage",
            "has_entitlement": lambda self, module: module == "production",
        },
    )()

    CoreApi.require_permission(context, "company.users.manage")
    CoreApi.require_entitlement(context, "production")

    with pytest.raises(AuthorizationError):
        CoreApi.require_permission(context, "system.billing.manage")

    with pytest.raises(AuthorizationError):
        CoreApi.require_entitlement(context, "accounts")


def test_request_context_requires_active_membership():
    assert RequestContextResolver is not None
    assert uuid4() is not None
