"""Stable contracts for the Phoenix Generic Framework."""

from phoenix_framework.contracts.capability import PlatformCapabilityContract
from phoenix_framework.contracts.command import ModuleCommand
from phoenix_framework.contracts.delivery import EventDelivery
from phoenix_framework.contracts.event import ModuleEvent
from phoenix_framework.contracts.integration import (
    ModuleDependency,
    ModuleIntegrationContract,
)
from phoenix_framework.contracts.invocation import (
    ModuleInvocationRequest,
    ModuleInvocationResponse,
)
from phoenix_framework.contracts.module import ModuleContract, ModuleLifecycle
from phoenix_framework.contracts.navigation import NavigationContract
from phoenix_framework.contracts.platform import (
    CompanyContext,
    ModuleDescriptor,
    NavigationItem,
    PlatformCapability,
    UserContext,
)
from phoenix_framework.contracts.query import ModuleQuery
from phoenix_framework.contracts.subscription import EventSubscription

__all__ = [
    "CompanyContext",
    "EventDelivery",
    "EventSubscription",
    "ModuleCommand",
    "ModuleContract",
    "ModuleDependency",
    "ModuleDescriptor",
    "ModuleEvent",
    "ModuleIntegrationContract",
    "ModuleInvocationRequest",
    "ModuleInvocationResponse",
    "ModuleLifecycle",
    "ModuleQuery",
    "NavigationContract",
    "NavigationItem",
    "PlatformCapability",
    "PlatformCapabilityContract",
    "UserContext",
]
