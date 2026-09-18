from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping
from uuid import UUID


class CompanyStatus(str, Enum):
    """Generic presentation status for a company."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


@dataclass(frozen=True)
class CompanyAdministration:
    """
    Administrative representation of a Core-owned organisation.

    This contract does not own or persist company authority.
    """

    organisation_id: UUID
    name: str
    status: CompanyStatus
    can_manage_users: bool = False
    can_manage_modules: bool = False
    can_manage_configuration: bool = False
    metadata: Mapping[str, str] = field(default_factory=dict)

    @property
    def active(self) -> bool:
        return self.status == CompanyStatus.ACTIVE

    @property
    def administration_enabled(self) -> bool:
        return self.active and (
            self.can_manage_users
            or self.can_manage_modules
            or self.can_manage_configuration
        )
