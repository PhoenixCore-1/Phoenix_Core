"""Phoenix System contracts."""

from phoenix_system.contracts.company import (
    CompanyAdministration,
    CompanyStatus,
)
from phoenix_system.contracts.configuration import ConfigurationAdministration
from phoenix_system.contracts.entitlement import EntitlementAdministration
from phoenix_system.contracts.membership import (
    MembershipAdministration,
    MembershipStatus,
)
from phoenix_system.contracts.module import ModuleAdministration
from phoenix_system.contracts.platform import PlatformAdministration
from phoenix_system.contracts.role import RoleAdministration
from phoenix_system.contracts.user import (
    UserAdministration,
    UserStatus,
)

__all__ = [
    "CompanyAdministration",
    "CompanyStatus",
    "ConfigurationAdministration",
    "EntitlementAdministration",
    "MembershipAdministration",
    "MembershipStatus",
    "ModuleAdministration",
    "PlatformAdministration",
    "RoleAdministration",
    "UserAdministration",
    "UserStatus",
]
