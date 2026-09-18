"""Organization structure, assignment and access-scope domain models.

This layer is platform-level infrastructure. Business modules consume the
resulting access scope; they do not implement their own organizational
visibility model.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import FrozenSet, Optional
from uuid import UUID, uuid4

from phoenix_core.errors import ValidationError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OrganizationUnitType(str, Enum):
    ORGANIZATION = "ORGANIZATION"
    REGION = "REGION"
    TERRITORY = "TERRITORY"
    TEAM = "TEAM"


class AssignmentType(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"


@dataclass(frozen=True)
class OrganizationUnit:
    id: UUID
    organization_id: UUID
    name: str
    unit_type: OrganizationUnitType
    parent_id: Optional[UUID]
    active: bool
    created_at: datetime

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        name: str,
        unit_type: OrganizationUnitType,
        parent_id: Optional[UUID] = None,
    ) -> "OrganizationUnit":
        if not name.strip():
            raise ValidationError("Organization unit name is required.")
        if unit_type == OrganizationUnitType.ORGANIZATION and parent_id is not None:
            raise ValidationError("An organization cannot have a parent unit.")
        return cls(uuid4(), organization_id, name.strip(), unit_type, parent_id, True, utcnow())


@dataclass(frozen=True)
class Assignment:
    id: UUID
    organization_id: UUID
    subject_id: UUID
    resource_id: UUID
    assignment_type: AssignmentType
    assigned_by: UUID
    active: bool
    created_at: datetime

    @classmethod
    def create(
        cls,
        organization_id: UUID,
        subject_id: UUID,
        resource_id: UUID,
        assigned_by: UUID,
        assignment_type: AssignmentType = AssignmentType.PRIMARY,
    ) -> "Assignment":
        return cls(
            uuid4(), organization_id, subject_id, resource_id,
            assignment_type, assigned_by, True, utcnow()
        )


@dataclass(frozen=True)
class AccessScope:
    """Resolved authorization scope for a user.

    ``organization_ids`` and ``unit_ids`` identify the organizational scope
    available to the caller. ``resource_ids`` may contain explicitly assigned
    resources such as customer/account identifiers. A separate authorization
    layer must still evaluate the requested action/permission.
    """

    subject_id: UUID
    organization_ids: FrozenSet[UUID]
    unit_ids: FrozenSet[UUID]
    resource_ids: FrozenSet[UUID]
    include_children: bool = True

    def can_access_resource(self, resource_id: UUID) -> bool:
        return resource_id in self.resource_ids
