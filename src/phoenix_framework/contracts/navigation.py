from dataclasses import dataclass, field
from typing import Mapping, Optional


@dataclass(frozen=True)
class NavigationContract:
    """
    Generic navigation contribution for the Phoenix Platform UI.

    Navigation metadata controls presentation and discovery only.
    Authorization remains authoritative in Phoenix Core.
    """

    key: str
    label: str
    route: str
    module_code: Optional[str] = None
    icon: Optional[str] = None
    permission: Optional[str] = None
    entitlement: Optional[str] = None
    order: int = 0
    enabled: bool = True
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("Navigation key cannot be empty")

        if not self.label.strip():
            raise ValueError("Navigation label cannot be empty")

        if not self.route.strip():
            raise ValueError("Navigation route cannot be empty")

    @property
    def requires_authorization(self) -> bool:
        return self.permission is not None or self.entitlement is not None

    def requires_permission(self, permission: str) -> bool:
        return self.permission == permission

    def requires_entitlement(self, entitlement: str) -> bool:
        return self.entitlement == entitlement
