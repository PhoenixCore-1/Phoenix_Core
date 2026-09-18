from dataclasses import dataclass
from uuid import uuid4

from phoenix_framework.context import FrameworkContext
from phoenix_framework.contracts import (
    PlatformCapability,
    PlatformCapabilityContract,
)


@dataclass(frozen=True)
class SearchCapabilityStub(PlatformCapabilityContract):

    @property
    def capability(self) -> PlatformCapability:
        return PlatformCapability(
            code="global_search",
            name="Global Search",
            description="Search authorised Phoenix data.",
        )

    def is_available(self, context: FrameworkContext) -> bool:
        return (
            context.authenticated
            and context.tenant_bound
            and context.has_permission("search.use")
        )

    def required_permissions(self):
        return ("search.use",)

    def required_entitlements(self):
        return ("platform.search",)


def test_platform_capability_contract_exposes_metadata():
    capability = SearchCapabilityStub()

    assert capability.capability.code == "global_search"
    assert capability.capability.name == "Global Search"


def test_platform_capability_contract_declares_security_requirements():
    capability = SearchCapabilityStub()

    assert capability.required_permissions() == ("search.use",)
    assert capability.required_entitlements() == ("platform.search",)


def test_platform_capability_is_available_for_authorised_context():
    context = FrameworkContext(
        request_id="req-001",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        session_id=None,
        permissions=frozenset({"search.use"}),
        entitlements=frozenset({"platform.search"}),
    )

    capability = SearchCapabilityStub()

    assert capability.is_available(context)


def test_platform_capability_is_unavailable_without_permission():
    context = FrameworkContext(
        request_id="req-002",
        identity_id=uuid4(),
        organisation_id=uuid4(),
        session_id=None,
        permissions=frozenset(),
        entitlements=frozenset({"platform.search"}),
    )

    capability = SearchCapabilityStub()

    assert not capability.is_available(context)


def test_platform_capability_is_unavailable_without_authentication():
    context = FrameworkContext(
        request_id="req-003",
        identity_id=None,
        organisation_id=None,
        session_id=None,
        permissions=frozenset({"search.use"}),
        entitlements=frozenset({"platform.search"}),
    )

    capability = SearchCapabilityStub()

    assert not capability.is_available(context)
